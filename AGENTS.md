# promo-monitor

**Backend:** Python 3.12 + FastAPI. **Frontend:** React + Vite + TanStack Router.

## Architecture

### Backend
- **FastAPI** app with lifespan that spawns a **Telethon** boot routine (`app/workers/telegram_worker.py`) to listen to Telegram groups in real time. If the saved session is still valid it starts the pipeline; otherwise it logs `telegram_login_required` and stays idle serving HTTP so the user can log in from `/login`. **No `input()` anywhere** — the verification code is submitted over HTTP
- **Auth state machine** (`app/telegram/auth.py`): `unauthenticated → awaiting_code → awaiting_password → authenticated`, driven by `POST /telegram/auth/*`, fast-failing (409) on concurrent submissions. **Never `client.start()`** (it prompts on stdin) and never auto-sends a code at boot (`restart: on-failure:5` would burn one per restart into a FloodWait)
- **Worker supervisor** (`app/workers/supervisor.py`): idempotent `ensure_started()`/`stop()` so the pipeline can start *after* a web login. `run_until_disconnected()` is gone — Telethon's own tasks dispatch events, and a 30s watchdog reconnects and detects a session revoked from another device. The long-lived DB session belongs to the supervisor and closes only in `stop()`
- **Capture pauses with zero active interests.** `sync_interests()` (called by the `/interests` write routes, and every 60s as a safety net) drives `_set_capture()`: no active interest ⇒ listener deregistered and the client reconnected with `receive_updates=False`, so Telegram stops pushing entirely. Pausing waits 30s (editing a list passes through zero-active states, and each transition is a reconnect); resuming is immediate but does **not backfill** — `MessageListener.capture_since` drops the reconnect's `GetDifference` replay so re-enabling an interest can't fire alerts for stale promos. The cutoff applies to resume only: `_build()` passes `capture_since=None` so a restart still processes the backlog Telegram redelivers. The `/interests` write routes stay sync `def` and hand `sync_interests` to `BackgroundTasks` — the SQLite commit belongs in the threadpool, not on the loop that dispatches Telegram updates. `/health` reports `capture_active` + `interests_count` because `worker_running` stays true while paused. Telethon's own `set_receive_updates()` is not enough: the flag only takes effect at `connect()`, so a reconnect is mandatory
- **SQLite** via SQLAlchemy (WAL mode + foreign keys enabled via `@event.listens_for` in `app/database/session.py`)
- **Repository pattern** (`BaseRepository[T]` in `app/repositories/base.py`)
- **Portuguese naming** in models/schemas/routes (`nome_produto`, `preco_maximo`, `palavras_chave`, `palavras_excluidas`, `ativo`)
- **Composite matching**: keyword (OR-semantics, word boundary) is authoritative — when an interest has any `palavras_chave`, fuzzy (rapidfuzz `token_set_ratio` of `nome_produto`) is forced to 0 and only serves as fallback when there are no keywords. Score = max of both; threshold is hardcoded at 0.6. `palavras_excluidas` is a hard veto. Price extraction via regex (`R$ 1.234,56` etc.), lowest price used, dropped if above `preco_maximo`.
- **LLM validation** (optional, `app/services/llm_validator_service.py`): matcher candidates are re-checked by an LLM (LangChain + OpenRouter, `LLM_MODEL`) before a match/alert is created. Gated by `OPENROUTER_API_KEY`; fail-open (approves on no-key/disabled/error). Rejections **are** stored as a `PromotionMatch` with `llm_aprovado=false` (for audit) — they just don't trigger an alert.
- **Bot token is DB-backed** (`app_config.telegram_bot_token`): the token is configured exclusively via the panel (`PUT /settings`) and changes apply without a restart. `BotManager` (`app/telegram/bot.py`) deletes `bot.session` on every restart — `start(bot_token=...)` skips sign-in when the session is already authorized, so a token change would otherwise be silently ignored and alerts would keep going through the old bot. `AlertService` takes a `bot_provider` callable, never a client instance
- **`/start` is owner-only.** It is the sole writer of `alert_target`, and it only accepts `event.sender_id == authenticator.user_id` — bot usernames are publicly searchable and the target is a single column, so an unguarded `/start` from a stranger hijacks the alerts (they receive, the owner silently stops). Fails closed when no account is connected. The check is on the *sender*, so `/start` inside a group still targets the group
- **Read state**: `promotion_matches.lido` / `lido_em` back the "unread" feed. There is no Alembic — new columns go in `_COLUMN_MIGRATIONS` in `app/database/session.py` and are `ALTER TABLE ADD COLUMN`'d at startup. `ensure_columns()` also runs a one-shot backfill (guarded by "did I just create this column?") marking pre-existing rows as read, so the unread counter doesn't start with the whole table in it.
- **Timezone**: `DateTime(timezone=True)` columns store **naive UTC** — SQLite's bind processor serializes the wall-clock fields and drops tzinfo without converting. Any datetime used in a comparison must go through `app/core/timeutils.py`. The `hoje` period is a calendar boundary in the *user's* timezone (`?tz=`, falling back to `APP_TIMEZONE`); `7d`/`30d` are rolling windows.
- **structlog** for structured logging, **pydantic-settings** for config

### Frontend
- **Vite** + **React 19** + **TypeScript 6**
- **TanStack Router** (file-based, auto code-splitting via `@tanstack/router-plugin`)
- **TanStack Query** (server state management)
- **Tailwind CSS v4** via `@tailwindcss/vite` plugin
- **shadcn/ui** components, `base-nova` style over **base-ui** (`alert`, `button`, `card`, `input`, `label`, `table`, `badge`, `select`, `switch`, `dialog`, `sheet`, `skeleton`, `textarea`, `sonner`)
- Path alias `@/` → `src/`
- `/login` is the Telegram login screen. The auth gate lives **in the `__root.tsx` component**, not in `beforeLoad` — a router-level async guard would block every navigation on a network call and can't be invalidated from a mutation. Backend-down renders its own screen instead of redirecting (redirecting would loop, since `/login` also needs the backend)
- `/` **is** the matches feed (`/matches` only redirects to it). Unread matches are visually highlighted inside a date-sorted list — `lido` is not a sort key, because re-sorting on read would make rows jump between offset-paginated pages.
- Window-focus refetch, not SSE and not interval polling. `useMatchesInfinite` only refetches on focus while page 1 is the only page loaded (a refetch of N pages against a shifted offset window duplicates/drops rows); `/matches/stats` refetches on focus unconditionally so the unread badge stays live. The global `staleTime: 15_000` debounces quick tab switches; past page 1 the manual button in `LastUpdated` is the only refresh.
- `Select.Root` needs the `items` prop for `SelectValue` to render a label instead of the raw value. Never use `<SelectItem value="">` — use a sentinel like `'todos'`.

## Directory structure

```
server/
  app/
    api/routes/     # FastAPI routers (auth, health, interests, matcher, matches,
                    #   messages, settings, telegram_auth, users)
    api/deps.py     # require_user / require_owner + helper do cookie de sessão
    core/           # config, logging, exceptions, links (build_message_link),
                    #   timeutils (naive-UTC + tz), masking (phone/token),
                    #   security (Argon2id, tokens de sessão, LoginThrottle)
    database/       # engine, session (+ ensure_columns), declarative Base
    models/         # SQLAlchemy ORM (TelegramMessage, ProductInterest, PromotionMatch,
                    #   AppConfig, User, UserSession)
    repositories/   # data access layer
    schemas/        # Pydantic request/response
    services/       # business logic (interest, matcher, llm_validator, alert, message,
                    #   match, auth, user)
    telegram/       # Telethon client (+ lifecycle helpers), auth (HTTP-driven state
                    #   machine), bot (BotManager, hot-swappable token), listener
    workers/        # boot routine + WorkerSupervisor (idempotent start/stop)
web/
  src/
    routes/               # File-based routes (TanStack Router auto-generates routeTree.gen.ts)
    components/ui/        # shadcn components
    components/features/  # domain components; matches/ holds the feed
      matches/            # MatchFeed, MatchTable (desktop), MatchCard (mobile),
                          # MatchDetailModal, MatchFilterBar, MatchStats, ReadToggle
    components/layout/    # Sidebar (+ MobileNav drawer), Header
    lib/                  # api client, cn/date helpers, match helpers (score, alertState)
    hooks/                # TanStack Query hooks
```

`MatchTable` (desktop) and `MatchCard` (mobile) are deliberately two components: a
`<table>` can't restructure into stacked cards without `display:block` overrides that
break both the semantics and the `overflow-x-auto` wrapper. Shared logic lives in
`lib/match.ts`, so the duplication is layout-only.

## Setup and run

### Backend (porta 4999)
```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
cp .env.example .env      # fill in TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
pip install -r requirements.txt
python3 run.py            # lê API_PORT do .env
```

First run: the backend sobe sem sessão e fica ocioso. Abra o painel, caia em
`/login` e clique em **Enviar código** — o código chega no app do Telegram e é
digitado na própria tela. Nenhum `input()` no console.

### Frontend (porta 3000)
```bash
cd web
pnpm install
pnpm dev
```

## Docker

O `docker-compose.yml` fica na **raiz** do repositório (não em `server/`) e sobe
os dois serviços (`promo-monitor-server`, `promo-monitor-web`):

```bash
cp .env.example .env                 # WEB_PORT (única porta publicada)
cp server/.env.example server/.env   # TELEGRAM_API_ID/HASH/PHONE + AUTH_SEED_EMAIL/PASSWORD
docker compose up --build -d
```

**Origem única.** O nginx do container `web` serve a SPA e proxia `/api/*` para
`backend:4999`; o backend **não publica porta** no host. Consequências: não existe
mais `VITE_API_URL` (o front chama `/api` relativo, então trocar de IP/domínio não
exige rebuild), o cookie de sessão dispensa CORS, e o `pnpm dev` replica isso com
`server.proxy` no `vite.config.ts` — `changeOrigin` fica **false** ali de propósito,
senão o Host reescrito quebra a checagem de Origin do backend.

First-run: abra `http://SEU_SERVIDOR:${WEB_PORT}` → login com `AUTH_SEED_*` → troca
de senha obrigatória → tela de conexão do Telegram → **Enviar código**. Não é preciso
`docker attach`.

**Segurança:** o painel agora exige login (ver *Autenticação* abaixo). O que continua
valendo é a ressalva de transporte: a stack serve **HTTP puro** por decisão de
operação, então a senha do login, a senha de duas etapas do Telegram e o cookie de
sessão trafegam em texto claro. O gate protege contra quem só conhece a URL, não
contra quem observa a rede. Com um proxy TLS na frente, basta `AUTH_COOKIE_SECURE=true`.

## Autenticação do painel

Sessão **opaca em cookie**, não JWT — a escolha é pela revogação: desativar ou
excluir um usuário precisa derrubar o acesso na hora, e um JWT só expira.

- `POST /auth/login` valida com Argon2id (`pwdlib`, `PasswordHash.recommended()`),
  gera `secrets.token_urlsafe(32)` e grava o **SHA-256** dele em `user_sessions`.
  Vazamento do banco não vira sessão válida. `verify_password` gasta o mesmo tempo
  com usuário inexistente (hash descartável) para não permitir enumerar contas.
- **Login persistente** — são três peças, e faltar qualquer uma produz o sintoma
  "tenho que logar toda hora":
  1. o cookie sai com `max_age` (sem ele o navegador cria um *session cookie* e
     descarta ao fechar);
  2. `resolve_session` faz renovação deslizante (no máximo 1x/hora) e devolve
     `(user, renovada)`; o middleware `renew_session_cookie` em `main.py` lê a marca
     em `request.state` e **reemite o Set-Cookie** — estender só a linha do banco
     deixaria o cookie morrer antes;
  3. `GET /auth/me` no boot do frontend restaura a sessão, e o ramo `isLoading` do
     `__root.tsx` evita piscar `/login` enquanto a chamada está em voo.
- `set_session_cookie` (em `api/deps.py`) é o **único** lugar que define os atributos
  do cookie. Emitir em dois lugares com atributos diferentes vira um "desloga
  sozinho" difícil de achar.
- **Sem cadastro aberto.** O primeiro owner vem de `AuthService.seed_owner()` no
  lifespan, só com a tabela `users` vazia, a partir de `AUTH_SEED_EMAIL/PASSWORD` —
  mesmo contrato do token do bot em `AppConfigRepository.get_or_create`. Ele nasce
  com `trocar_senha=True`: a senha veio de um arquivo em disco.
- `UserService._assert_nao_e_ultimo_owner` impede rebaixar/desativar/excluir o
  último owner ativo. Sem isso o painel ficaria sem quem o administre e a única
  saída seria editar o SQLite na mão.
- **CSRF:** `SameSite=Lax` no cookie + o middleware `block_cross_origin_writes`, que
  compara o `Origin` com o Host em métodos não-seguros. Por isso o nginx manda
  `proxy_set_header Host $http_host` e **não** `$host` — `$host` descarta a porta, e
  a comparação `http://ip:5000` vs `http://ip` barraria até o login.
- **Rate limit** em memória (`LoginThrottle`), chaveado por (e-mail, IP). Em processo
  é seguro porque o backend roda com um único worker uvicorn; a chave inclui o IP para
  que errar a senha de fora não tranque o login do dono. Depende de
  `--proxy-headers` no uvicorn, senão todo mundo compartilha o IP do nginx.
- `/health` entrou no bloco protegido (contava estado do Telegram/bot para quem só
  varreu a porta) e o HEALTHCHECK passou a usar o `/healthz` público.

No frontend: `useSession` (`hooks/useSession.ts`) traduz **401 → `null`**, para
"deslogado" não cair na tela "Backend indisponível" do `__root` — que precisa
continuar significando falha de rede. O gate do `__root.tsx` tem dois estágios
encadeados (sessão do painel → conexão do Telegram) e `useAuthStatus(enabled)` só
dispara com sessão, senão a tela de login pediria `/telegram/auth/status` a cada 3s.
O `useLogout` do painel e o `useTelegramLogout` são coisas diferentes de propósito.

## Dev tooling

**Backend:** No linter, typechecker ou CI. Testes: `tests/test_matcher.py` e
`tests/test_auth.py`, ambos rodáveis com `python -m pytest tests/` ou standalone
(`python tests/test_auth.py`). O de auth usa um SQLite temporário e define
`DATABASE_URL` **antes** de importar `app` — o engine nasce no import.
**Frontend:** ESLint (React hooks + refresh plugins). Build: `pnpm build` (tsc + vite).

- `requirements.txt` (server) has version ranges only (no lockfile)
- `pnpm-lock.yaml` (web) is committed
- `.env` (server) is gitignored; `data/` and `session/` directories are gitignored (created at runtime by `Settings.model_post_init`)
- Server `.gitignore` lives in `server/`; web `.gitignore` lives in `web/`

## API endpoints

Acesso: **público** = sem sessão · **user** = qualquer logado · **owner** = só admin.
O gate vive em `app/api/router.py` (`require_user` no subrouter protegido), então
**rota nova nasce fechada** — é o padrão certo numa API exposta.

| Method | Path | Acesso | Notes |
|--------|------|--------|-------|
| GET | `/healthz` | público | `{"status":"ok"}`. Alvo do HEALTHCHECK do Docker, que roda sem cookie |
| POST | `/auth/login` | público | `{email, senha}` → cookie `pm_session`. 401 `credentials_invalid`, 403 `user_disabled`, 429 `too_many_attempts` + `Retry-After` |
| POST | `/auth/logout` | público | apaga a sessão e o cookie (funciona mesmo com cookie já inválido) |
| GET | `/auth/me` | user | fonte da verdade da sessão no frontend; **401 quando deslogado** — o `useSession` traduz isso para `null`, não para erro |
| POST | `/auth/password` | user | `{senha_atual, senha_nova}`. Invalida as outras sessões e reabre a atual |
| GET | `/users` | owner | lista de acessos |
| POST | `/users` | owner | `{email, nome, papel, senha}` → 201. 409 `email_taken` |
| PATCH | `/users/{id}` | owner | parcial: `nome`, `papel`, `ativo`. 409 `last_owner`. Trocar papel ou desativar **revoga as sessões** do alvo |
| POST | `/users/{id}/password` | owner | reset; marca `trocar_senha` e derruba as sessões da pessoa |
| DELETE | `/users/{id}` | owner | 204. 409 `self_delete` / `last_owner` |
| GET | `/health` | user | `status`, `telegram_connected`, `telegram_authenticated`, `worker_running`, `bot_connected`, `uptime_seconds` — tudo de snapshot em memória (polado a cada 30s) |
| GET | `/telegram/auth/status` | owner | estado do login: `status`, `phone_masked`, `connected`, `worker_running`, `user`, `error_code`, `retry_after_seconds`, `can_request_code` |
| POST | `/telegram/auth/request-code` | owner | envia o código para `TELEGRAM_PHONE`. 429 + `Retry-After` no FloodWait |
| POST | `/telegram/auth/code` | owner | `{code}` → 400 `code_invalid` / `code_expired`, 409 `wrong_state`/`auth_busy` |
| POST | `/telegram/auth/password` | owner | `{password}` (2FA) → 400 `password_invalid` |
| POST | `/telegram/auth/logout` | owner | encerra a sessão, para o worker e o bot |
| POST | `/interests` | user | create with `nome_produto`, `preco_maximo`, `palavras_chave`, `palavras_excluidas` |
| GET | `/interests` | user | filter with `?ativo=true` |
| PUT | `/interests/{id}` | user | partial update |
| DELETE | `/interests/{id}` | user | — |
| GET | `/matches` | user | envelope `{items,total,has_more}`. Filters: `periodo` (`hoje\|7d\|30d\|tudo`) + `tz`, `nao_lidos`, `status` (repeatable: `alertado`, `reprovado`), `chat_id`, `preco_min`, `preco_max`, `order_by` (`data\|preco\|score`), `order_dir`, `skip`, `limit`. Includes LLM-rejected (`llm_aprovado=false`) |
| GET | `/matches/stats` | user | `?tz=` → `nao_lidos`, `novos_hoje`, `ultimas_24h`, `ultimos_7d`, `interesses_ativos` (global, filter-independent — backs the nav badge) |
| GET | `/matches/chats` | user | distinct chats **that have matches**, with counts (for the group filter) |
| POST | `/matches/{id}/read` | user | mark read |
| POST | `/matches/{id}/unread` | user | mark unread |
| POST | `/matches/read-all` | user | body = the same filter model as `GET /matches`, so bulk-read hits exactly what's on screen. Returns `{updated}` |
| GET | `/messages` | user | list stored (matched) messages |
| POST | `/matcher/preview` | user | dry-run scoring of a candidate interest against recent stored messages |
| GET / PUT | `/settings` | owner | PUT aceita **só** `telegram_bot_token` (parcial, `exclude_unset`: campo ausente = não mexe, `null` = limpa). `alert_target` é **read-only** na resposta — quem grava é o handler `/start` do bot. A resposta nunca traz o token cru — só `telegram_bot_token_set`/`_masked`, `bot_connected`, `bot_username`, `bot_last_error` |
| POST | `/settings/alert/test` | owner | manda uma mensagem de teste para o `alert_target` → `{ok, error}` |
