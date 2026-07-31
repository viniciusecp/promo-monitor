"""Testes da autenticação do painel. Rodar a partir de server/:

    python -m pytest tests/test_auth.py           # se pytest instalado
    python tests/test_auth.py                     # fallback sem pytest

Usa um SQLite temporário próprio: `DATABASE_URL` é definido **antes** de
importar qualquer coisa de `app`, porque o engine nasce no import de
`app.database.session` a partir do singleton `settings`.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_TMP_DB = Path(tempfile.mkdtemp(prefix="promo-auth-test-")) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ["AUTH_SEED_EMAIL"] = "dono@exemplo.com"
os.environ["AUTH_SEED_PASSWORD"] = "senha-do-seed-123"

from datetime import timedelta  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.core.exceptions import AuthError  # noqa: E402
from app.core.security import (  # noqa: E402
    LoginThrottle,
    hash_password,
    hash_token,
    login_throttle,
    verify_password,
)
from app.core.timeutils import utcnow_naive  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import PAPEL_OWNER, PAPEL_VIEWER  # noqa: E402
from app.repositories.user_repo import SessionRepository, UserRepository  # noqa: E402
from app.schemas.user import UserCreate, UserUpdate  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402
from app.services.user_service import UserService  # noqa: E402

SEED_EMAIL = "dono@exemplo.com"
SEED_SENHA = "senha-do-seed-123"


def _reset_db():
    """Banco limpo e owner semeado. Cada teste começa do mesmo estado."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    login_throttle._attempts.clear()
    db = SessionLocal()
    try:
        AuthService(UserRepository(db), SessionRepository(db)).seed_owner()
    finally:
        db.close()


def _services():
    db = SessionLocal()
    return db, AuthService(UserRepository(db), SessionRepository(db)), UserService(
        UserRepository(db), SessionRepository(db)
    )


def _client() -> TestClient:
    """TestClient sem entrar no lifespan — ele subiria o worker do Telegram."""
    return TestClient(app)


# --- hash de senha ---

def test_hash_e_argon2id():
    h = hash_password("uma-senha-qualquer")
    assert h.startswith("$argon2id$"), h[:20]


def test_verify_password():
    h = hash_password("uma-senha-qualquer")
    assert verify_password("uma-senha-qualquer", h)
    assert not verify_password("outra-senha", h)


def test_verify_password_com_hash_ausente():
    # Não pode explodir: é o caminho do e-mail inexistente no login.
    assert not verify_password("qualquer", None)


def test_hash_de_token_e_deterministico_e_de_64_chars():
    assert hash_token("abc") == hash_token("abc")
    assert len(hash_token("abc")) == 64
    assert hash_token("abc") != hash_token("abd")


# --- seed ---

def test_seed_cria_owner_uma_vez_so():
    _reset_db()
    db, auth, _ = _services()
    try:
        users = UserRepository(db)
        assert users.count_all() == 1
        owner = users.get_by_email(SEED_EMAIL)
        assert owner.papel == PAPEL_OWNER
        # Senha vinda de arquivo em disco tem que ser trocada no primeiro uso.
        assert owner.trocar_senha is True

        auth.seed_owner()
        assert users.count_all() == 1, "seed rodou duas vezes"
    finally:
        db.close()


# --- ciclo de sessão ---

def test_login_abre_sessao_resolvivel():
    _reset_db()
    db, auth, _ = _services()
    try:
        user, token = auth.login(SEED_EMAIL, SEED_SENHA, ip="1.2.3.4")
        assert user.email == SEED_EMAIL
        resolvido, renovada = auth.resolve_session(token)
        assert resolvido.id == user.id
        # Sessão recém-criada não renova: `ultimo_uso_em` acabou de ser gravado.
        assert renovada is False
    finally:
        db.close()


def test_sessao_expirada_e_recusada_e_removida():
    _reset_db()
    db, auth, _ = _services()
    try:
        _, token = auth.login(SEED_EMAIL, SEED_SENHA, ip="1.2.3.4")
        sessions = SessionRepository(db)
        registro = sessions.get_by_token_hash(hash_token(token))
        registro.expira_em = utcnow_naive() - timedelta(seconds=1)
        db.commit()

        try:
            auth.resolve_session(token)
            raise AssertionError("sessão expirada deveria ter sido recusada")
        except AuthError as e:
            assert e.code == "session_expired", e.code

        assert sessions.get_by_token_hash(hash_token(token)) is None
    finally:
        db.close()


def test_renovacao_deslizante_estende_a_validade():
    """O ponto do login persistente: usar o painel empurra a expiração."""
    _reset_db()
    db, auth, _ = _services()
    try:
        _, token = auth.login(SEED_EMAIL, SEED_SENHA, ip="1.2.3.4")
        sessions = SessionRepository(db)
        registro = sessions.get_by_token_hash(hash_token(token))

        # Simula uma sessão usada pela última vez há duas horas.
        registro.ultimo_uso_em = utcnow_naive() - timedelta(hours=2)
        expira_antes = registro.expira_em = utcnow_naive() + timedelta(days=1)
        db.commit()

        _, renovada = auth.resolve_session(token)
        assert renovada is True, "deveria ter renovado após mais de 1h de uso"

        registro = sessions.get_by_token_hash(hash_token(token))
        assert registro.expira_em > expira_antes, "a validade não foi estendida"
    finally:
        db.close()


def test_usuario_desativado_perde_a_sessao_aberta():
    _reset_db()
    db, auth, users_svc = _services()
    try:
        owner = UserRepository(db).get_by_email(SEED_EMAIL)
        novo = users_svc.create(
            UserCreate(
                email="viewer@exemplo.com",
                nome="Viewer",
                papel=PAPEL_VIEWER,
                senha="senha-do-viewer-1",
            )
        )
        _, token = auth.login("viewer@exemplo.com", "senha-do-viewer-1", ip="1.2.3.4")
        assert auth.resolve_session(token)[0].id == novo.id

        users_svc.update(novo.id, UserUpdate(ativo=False), actor=owner)

        try:
            auth.resolve_session(token)
            raise AssertionError("desativar deveria derrubar a sessão na hora")
        except AuthError as e:
            assert e.code in ("user_disabled", "not_authenticated"), e.code
    finally:
        db.close()


def test_troca_de_senha_invalida_as_sessoes():
    _reset_db()
    db, auth, _ = _services()
    try:
        user, token = auth.login(SEED_EMAIL, SEED_SENHA, ip="1.2.3.4")
        auth.change_password(user, SEED_SENHA, "nova-senha-forte-9")

        try:
            auth.resolve_session(token)
            raise AssertionError("a sessão antiga deveria ter caído")
        except AuthError:
            pass

        _, novo_token = auth.login(SEED_EMAIL, "nova-senha-forte-9", ip="1.2.3.4")
        assert auth.resolve_session(novo_token)[0].trocar_senha is False
    finally:
        db.close()


# --- throttle ---

def test_throttle_bloqueia_apos_o_limite():
    t = LoginThrottle(max_attempts=3, lockout_seconds=60)
    assert t.retry_after("a@b.com", "1.1.1.1") == 0
    assert t.register_failure("a@b.com", "1.1.1.1") == 0
    assert t.register_failure("a@b.com", "1.1.1.1") == 0
    assert t.register_failure("a@b.com", "1.1.1.1") == 60
    assert t.retry_after("a@b.com", "1.1.1.1") > 0


def test_throttle_e_por_ip():
    """Errar a senha de outro IP não pode trancar o login do dono."""
    t = LoginThrottle(max_attempts=2, lockout_seconds=60)
    t.register_failure("a@b.com", "9.9.9.9")
    t.register_failure("a@b.com", "9.9.9.9")
    assert t.retry_after("a@b.com", "9.9.9.9") > 0
    assert t.retry_after("a@b.com", "1.1.1.1") == 0


def test_throttle_zera_no_sucesso():
    t = LoginThrottle(max_attempts=3, lockout_seconds=60)
    t.register_failure("a@b.com", "1.1.1.1")
    t.reset("a@b.com", "1.1.1.1")
    assert t.register_failure("a@b.com", "1.1.1.1") == 0


def test_login_bloqueia_apos_tentativas_erradas():
    _reset_db()
    db, auth, _ = _services()
    try:
        for _ in range(5):  # MAX_LOGIN_ATTEMPTS=5 hardcoded em security.py
            try:
                auth.login(SEED_EMAIL, "errada", ip="5.5.5.5")
            except AuthError:
                pass
        try:
            auth.login(SEED_EMAIL, SEED_SENHA, ip="5.5.5.5")
            raise AssertionError("deveria estar bloqueado mesmo com a senha certa")
        except AuthError as e:
            assert e.code == "too_many_attempts", e.code
            assert e.retry_after and e.retry_after > 0
    finally:
        db.close()


# --- trava do último owner ---

def test_nao_da_para_rebaixar_o_ultimo_owner():
    _reset_db()
    db, _, users_svc = _services()
    try:
        owner = UserRepository(db).get_by_email(SEED_EMAIL)
        try:
            users_svc.update(owner.id, UserUpdate(papel=PAPEL_VIEWER), actor=owner)
            raise AssertionError("rebaixar o único owner deveria falhar")
        except AuthError as e:
            assert e.code == "last_owner", e.code
    finally:
        db.close()


def test_nao_da_para_desativar_o_ultimo_owner():
    _reset_db()
    db, _, users_svc = _services()
    try:
        owner = UserRepository(db).get_by_email(SEED_EMAIL)
        try:
            users_svc.update(owner.id, UserUpdate(ativo=False), actor=owner)
            raise AssertionError("desativar o único owner deveria falhar")
        except AuthError as e:
            assert e.code == "last_owner", e.code
    finally:
        db.close()


def test_da_para_rebaixar_owner_quando_existe_outro():
    _reset_db()
    db, _, users_svc = _services()
    try:
        owner = UserRepository(db).get_by_email(SEED_EMAIL)
        segundo = users_svc.create(
            UserCreate(
                email="outro@exemplo.com",
                nome="Outro",
                papel=PAPEL_OWNER,
                senha="senha-do-outro-1",
            )
        )
        atualizado = users_svc.update(
            segundo.id, UserUpdate(papel=PAPEL_VIEWER), actor=owner
        )
        assert atualizado.papel == PAPEL_VIEWER
    finally:
        db.close()


def test_email_duplicado_e_recusado():
    _reset_db()
    db, _, users_svc = _services()
    try:
        try:
            users_svc.create(
                UserCreate(
                    # Maiúsculas de propósito: a normalização tem que pegar.
                    email="DONO@Exemplo.com",
                    nome="Clone",
                    papel=PAPEL_VIEWER,
                    senha="senha-do-clone-1",
                )
            )
            raise AssertionError("e-mail duplicado deveria falhar")
        except AuthError as e:
            assert e.code == "email_taken", e.code
    finally:
        db.close()


def test_senha_curta_e_recusada():
    _reset_db()
    db, _, users_svc = _services()
    try:
        try:
            users_svc.create(
                UserCreate(
                    email="curto@exemplo.com",
                    nome="Curto",
                    papel=PAPEL_VIEWER,
                    senha="abc",
                )
            )
            raise AssertionError("senha curta deveria falhar")
        except AuthError as e:
            assert e.code == "password_weak", e.code
    finally:
        db.close()


# --- gate HTTP ---

def test_rotas_protegidas_respondem_401_sem_cookie():
    _reset_db()
    client = _client()
    for rota in ("/matches", "/interests", "/settings", "/users", "/health"):
        r = client.get(rota)
        assert r.status_code == 401, f"{rota} devolveu {r.status_code}"
        assert r.json()["detail"]["code"] == "not_authenticated", rota


def test_telegram_auth_fechado_sem_cookie():
    """A rota mais sensível: sem gate, um estranho pede código de login."""
    _reset_db()
    client = _client()
    assert client.get("/telegram/auth/status").status_code == 401
    assert client.post("/telegram/auth/request-code").status_code == 401


def test_healthz_continua_publico():
    # O HEALTHCHECK do container bate aqui sem cookie.
    _reset_db()
    assert _client().get("/healthz").json() == {"status": "ok"}


def test_login_seta_cookie_persistente_e_me_devolve_o_usuario():
    _reset_db()
    client = _client()
    r = client.post("/auth/login", json={"email": SEED_EMAIL, "senha": SEED_SENHA})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["papel"] == PAPEL_OWNER
    assert r.json()["user"]["trocar_senha"] is True

    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie, cookie
    assert "samesite=lax" in cookie, cookie
    # Max-Age é o que faz o login sobreviver a fechar o navegador: sem ele o
    # cookie seria de sessão e o navegador o descartaria ao fechar a janela.
    assert "max-age=" in cookie, cookie

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["email"] == SEED_EMAIL


def test_login_errado_nao_seta_cookie():
    _reset_db()
    client = _client()
    r = client.post("/auth/login", json={"email": SEED_EMAIL, "senha": "errada"})
    assert r.status_code == 401, r.text
    assert r.json()["detail"]["code"] == "credentials_invalid"
    assert "set-cookie" not in r.headers


def test_viewer_nao_acessa_rotas_de_owner():
    _reset_db()
    db, _, users_svc = _services()
    try:
        users_svc.create(
            UserCreate(
                email="viewer@exemplo.com",
                nome="Viewer",
                papel=PAPEL_VIEWER,
                senha="senha-do-viewer-1",
            )
        )
    finally:
        db.close()

    client = _client()
    client.post(
        "/auth/login", json={"email": "viewer@exemplo.com", "senha": "senha-do-viewer-1"}
    )
    # Vê o feed…
    assert client.get("/matches").status_code == 200
    # …mas não as rotas do dono.
    assert client.get("/settings").status_code == 403
    assert client.get("/users").status_code == 403
    assert client.get("/telegram/auth/status").status_code == 403


def test_logout_derruba_o_acesso():
    _reset_db()
    client = _client()
    client.post("/auth/login", json={"email": SEED_EMAIL, "senha": SEED_SENHA})
    assert client.get("/auth/me").status_code == 200
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").status_code == 401


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                failures += 1
                print(f"FAIL {name}: {e}")
            except Exception as e:  # noqa: BLE001
                failures += 1
                print(f"ERROR {name}: {type(e).__name__}: {e}")
    sys.exit(1 if failures else 0)
