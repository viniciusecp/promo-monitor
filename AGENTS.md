# promo-monitor

**Backend:** Python 3.12 + FastAPI. **Frontend:** React + Vite + TanStack Router.

## Architecture

### Backend
- **FastAPI** app with lifespan that spawns a **Telethon** boot routine (`app/workers/telegram_worker.py`) to listen to Telegram groups in real time. If the saved session is still valid it starts the pipeline; otherwise it logs `telegram_login_required` and stays idle serving HTTP so the user can log in from `/login`. **No `input()` anywhere** — the verification code is submitted over HTTP
- **Auth state machine** (`app/telegram/auth.py`): `unauthenticated → awaiting_code → awaiting_password → authenticated`, driven by `POST /telegram/auth/*`, fast-failing (409) on concurrent submissions. **Never `client.start()`** (it prompts on stdin) and never auto-sends a code at boot (`restart: on-failure:5` would burn one per restart into a FloodWait)
- **Worker supervisor** (`app/workers/supervisor.py`): idempotent `ensure_started()`/`stop()` so the pipeline can start *after* a web login. `run_until_disconnected()` is gone — Telethon's own tasks dispatch events, and a 30s watchdog reconnects and detects a session revoked from another device. The long-lived DB session belongs to the supervisor and closes only in `stop()`
- **SQLite** via SQLAlchemy (WAL mode + foreign keys enabled via `@event.listens_for` in `app/database/session.py`)
- **Repository pattern** (`BaseRepository[T]` in `app/repositories/base.py`)
- **Portuguese naming** in models/schemas/routes (`nome_produto`, `preco_maximo`, `palavras_chave`, `palavras_excluidas`, `ativo`)
- **Composite matching**: keyword (OR-semantics, word boundary) is authoritative — when an interest has any `palavras_chave`, fuzzy (rapidfuzz `token_set_ratio` of `nome_produto`) is forced to 0 and only serves as fallback when there are no keywords. Score = max of both; per-interest `limiar_match` overrides the default threshold 0.6. `palavras_excluidas` is a hard veto. Price extraction via regex (`R$ 1.234,56` etc.), lowest price used, dropped if above `preco_maximo`.
- **LLM validation** (optional, `app/services/llm_validator_service.py`): matcher candidates are re-checked by an LLM (LangChain + OpenRouter, `LLM_MODEL`) before a match/alert is created. Gated by `OPENROUTER_API_KEY`; fail-open (approves on no-key/disabled/error). Rejections **are** stored as a `PromotionMatch` with `llm_aprovado=false` (for audit) — they just don't trigger an alert.
- **Bot token is DB-backed** (`app_config.telegram_bot_token`): `TELEGRAM_BOT_TOKEN` only seeds it once, then the panel owns it and changes apply without a restart. `BotManager` (`app/telegram/bot.py`) deletes `bot.session` on every restart — `start(bot_token=...)` skips sign-in when the session is already authorized, so a token change would otherwise be silently ignored and alerts would keep going through the old bot. `AlertService` takes a `bot_provider` callable, never a client instance
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
    api/routes/     # FastAPI routers (health, interests, matcher, matches, messages,
                    #   settings, telegram_auth)
    core/           # config, logging, exceptions, links (build_message_link),
                    #   timeutils (naive-UTC + tz), masking (phone/token)
    database/       # engine, session (+ ensure_columns), declarative Base
    models/         # SQLAlchemy ORM (TelegramMessage, ProductInterest, PromotionMatch, AppConfig)
    repositories/   # data access layer
    schemas/        # Pydantic request/response
    services/       # business logic (interest, matcher, llm_validator, alert, message, match)
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

### Backend (porta 3333)
```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
cp .env.example .env      # fill in TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
pip install -r requirements.txt
python3 run.py            # lê API_HOST e API_PORT do .env
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
os dois serviços (`promo-monitor-backend`, `promo-monitor-web`):

```bash
cp .env.example .env                 # VITE_API_URL (build-time), API_PORT, WEB_PORT
cp server/.env.example server/.env   # TELEGRAM_API_ID/HASH/PHONE
docker compose up --build -d
```

First-run login: abra `http://SEU_SERVIDOR:${WEB_PORT}` → a tela de login →
**Enviar código**. Não é preciso `docker attach` (o `stdin_open`/`tty` foi
removido do compose).

**Segurança:** as rotas de login e de configuração são **sem autenticação**, por
decisão de projeto — a senha de duas etapas trafega em HTTP puro numa API com
CORS `*`. Mantenha a stack em localhost/LAN confiável e nunca faça port-forward
dela para a internet.

## Dev tooling

**Backend:** None configured (no test runner, no linter, no typechecker, no CI/CD).
**Frontend:** ESLint (React hooks + refresh plugins). Build: `pnpm build` (tsc + vite).

- `requirements.txt` (server) has version ranges only (no lockfile)
- `pnpm-lock.yaml` (web) is committed
- `.env` (server) is gitignored; `data/` and `session/` directories are gitignored (created at runtime by `Settings.model_post_init`)
- Server `.gitignore` lives in `server/`; web `.gitignore` lives in `web/`

## API endpoints

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | `status`, `telegram_connected`, `telegram_authenticated`, `worker_running`, `bot_connected`, `uptime_seconds` — tudo de snapshot em memória (polado a cada 30s) |
| GET | `/telegram/auth/status` | estado do login: `status`, `phone_masked`, `connected`, `worker_running`, `user`, `error_code`, `retry_after_seconds`, `can_request_code` |
| POST | `/telegram/auth/request-code` | envia o código para `TELEGRAM_PHONE`. 429 + `Retry-After` no FloodWait |
| POST | `/telegram/auth/code` | `{code}` → 400 `code_invalid` / `code_expired`, 409 `wrong_state`/`auth_busy` |
| POST | `/telegram/auth/password` | `{password}` (2FA) → 400 `password_invalid` |
| POST | `/telegram/auth/logout` | encerra a sessão, para o worker e o bot |
| POST | `/interests` | create with `nome_produto`, `preco_maximo`, `limiar_match`, `palavras_chave`, `palavras_excluidas` |
| GET | `/interests` | filter with `?ativo=true` |
| PUT | `/interests/{id}` | partial update |
| DELETE | `/interests/{id}` | — |
| GET | `/matches` | envelope `{items,total,has_more}`. Filters: `periodo` (`hoje\|7d\|30d\|tudo`) + `tz`, `nao_lidos`, `status` (repeatable: `alertado`, `reprovado`), `chat_id`, `preco_min`, `preco_max`, `order_by` (`data\|preco\|score`), `order_dir`, `skip`, `limit`. Includes LLM-rejected (`llm_aprovado=false`) |
| GET | `/matches/stats` | `?tz=` → `nao_lidos`, `novos_hoje`, `ultimas_24h`, `ultimos_7d`, `interesses_ativos` (global, filter-independent — backs the nav badge) |
| GET | `/matches/chats` | distinct chats **that have matches**, with counts (for the group filter) |
| POST | `/matches/{id}/read` | mark read |
| POST | `/matches/{id}/unread` | mark unread |
| POST | `/matches/read-all` | body = the same filter model as `GET /matches`, so bulk-read hits exactly what's on screen. Returns `{updated}` |
| GET | `/messages` | list stored (matched) messages |
| POST | `/matcher/preview` | dry-run scoring of a candidate interest against recent stored messages |
| GET / PUT | `/settings` | PUT aceita **só** `telegram_bot_token` (parcial, `exclude_unset`: campo ausente = não mexe, `null` = limpa). `alert_target` é **read-only** na resposta — quem grava é o handler `/start` do bot. A resposta nunca traz o token cru — só `telegram_bot_token_set`/`_masked`, `bot_connected`, `bot_username`, `bot_last_error` |
| POST | `/settings/alert/test` | manda uma mensagem de teste para o `alert_target` → `{ok, error}` |
