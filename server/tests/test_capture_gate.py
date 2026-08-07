"""Testes do portão da captura. Rodar a partir de server/:

    python -m pytest tests/test_capture_gate.py   # se pytest instalado
    python tests/test_capture_gate.py             # fallback sem pytest

Sem rede e sem banco: os repositórios são dublês que falham se tocados, que é
justamente o que se quer provar do caminho quente.
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.product_interest import ProductInterest
from app.services.message_service import MessageService
from app.telegram.listener import MessageListener


class _RepoProibido:
    """Qualquer acesso ao banco no caminho quente é falha de teste."""

    def exists_by_telegram_id(self, message_id, chat_id):
        raise AssertionError("consultou o banco sem interesse ativo")

    def create(self, **kwargs):
        raise AssertionError("gravou mensagem sem interesse ativo")


def _interest(nome: str = "monitor", ativo: bool = True) -> ProductInterest:
    return ProductInterest(
        nome_produto=nome,
        palavras_chave=[nome],
        palavras_excluidas=[],
        preco_maximo=None,
        ativo=ativo,
    )


def _service(interests: list[ProductInterest]) -> MessageService:
    return MessageService(
        message_repo=_RepoProibido(),
        match_repo=_RepoProibido(),
        alert_service=None,
        llm_validator=None,
        interests=interests,
    )


def _process(service: MessageService, texto: str = "monitor em promocao") -> None:
    asyncio.run(
        service.process_message(
            message_id=1,
            chat_id=-100123,
            chat_name="grupo",
            sender_id=7,
            sender_name="alguem",
            text=texto,
            raw_date=None,
        )
    )


# --------------------------------------------------------------- MessageService


def test_sem_interesse_nao_consulta_o_banco():
    _process(_service([]))  # _RepoProibido levantaria


def test_interesse_inativo_conta_como_ausente():
    _process(_service([_interest(ativo=False)]))


def test_refresh_descarta_inativos():
    service = _service([])
    service.refresh_interests([_interest("a"), _interest("b", ativo=False)])
    assert len(service.interests) == 1, service.interests
    assert service.has_active_interests


def test_com_interesse_ativo_chega_ao_banco():
    service = _service([_interest()])
    try:
        _process(service)
    except AssertionError as e:
        assert "consultou o banco" in str(e), e
    else:
        raise AssertionError("deveria ter consultado o banco")


# -------------------------------------------------------------------- Listener


class _ServicoEspiao:
    def __init__(self, ativo: bool = True) -> None:
        self.has_active_interests = ativo
        self.chamadas = 0

    async def process_message(self, **kwargs):
        self.chamadas += 1


class _MsgFalsa:
    def __init__(self, date: datetime) -> None:
        self.id = 1
        self.chat_id = -100123
        self.date = date
        self.text = "monitor em promocao"
        self.message = self.text


class _EventoFalso:
    def __init__(self, date: datetime) -> None:
        self.is_private = False
        self.message = _MsgFalsa(date)
        self.resolveu = 0

    async def get_chat(self):
        self.resolveu += 1
        return type("C", (), {"title": "grupo"})()

    async def get_sender(self):
        self.resolveu += 1
        return type("S", (), {"first_name": "alguem", "id": 7})()


def _entregar(listener: MessageListener, event: _EventoFalso) -> None:
    asyncio.run(listener._on_new_message(event))


def test_listener_sai_antes_de_resolver_entidade():
    servico = _ServicoEspiao(ativo=False)
    listener = MessageListener(client=None, message_service=servico)
    evento = _EventoFalso(datetime.now(timezone.utc))
    _entregar(listener, evento)
    assert servico.chamadas == 0, "processou mensagem sem interesse ativo"
    assert evento.resolveu == 0, "resolveu entidade antes do portão"


def test_listener_descarta_mensagem_anterior_a_capture_since():
    servico = _ServicoEspiao()
    agora = datetime.now(timezone.utc)
    listener = MessageListener(
        client=None,
        message_service=servico,
        capture_since=agora.replace(tzinfo=None),
    )
    evento = _EventoFalso(agora - timedelta(hours=3))
    _entregar(listener, evento)
    assert servico.chamadas == 0, "deixou passar mensagem do catch-up"
    assert evento.resolveu == 0, "resolveu entidade antes do portão"


def test_listener_aceita_mensagem_dentro_da_janela():
    servico = _ServicoEspiao()
    agora = datetime.now(timezone.utc)
    listener = MessageListener(
        client=None,
        message_service=servico,
        capture_since=(agora - timedelta(hours=1)).replace(tzinfo=None),
    )
    _entregar(listener, _EventoFalso(agora))
    assert servico.chamadas == 1, "descartou mensagem que estava na janela"


def test_listener_sem_capture_since_aceita_catch_up():
    servico = _ServicoEspiao()
    listener = MessageListener(
        client=None, message_service=servico, capture_since=None
    )
    _entregar(listener, _EventoFalso(datetime.now(timezone.utc) - timedelta(hours=3)))
    assert servico.chamadas == 1, "descartou backlog do restart"


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
    sys.exit(1 if failures else 0)
