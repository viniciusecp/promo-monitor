# promo-monitor

**Backend:** Python 3.12 + FastAPI. **Frontend:** React + Vite + TanStack Router.

## Architecture

### Backend
- **FastAPI** app with lifespan that spawns a **Telethon** background worker (`app/workers/telegram_worker.py`) to listen to Telegram groups in real time
- **SQLite** via SQLAlchemy (WAL mode + foreign keys enabled via `@event.listens_for` in `app/database/session.py`)
- **Repository pattern** (`BaseRepository[T]` in `app/repositories/base.py`)
- **Portuguese naming** in models/schemas/routes (`nome_produto`, `preco_maximo`, `palavras_chave`, `palavras_excluidas`, `ativo`)
- **Composite matching**: keyword (OR-semantics, word boundary) is authoritative — when an interest has any `palavras_chave`, fuzzy (rapidfuzz `token_set_ratio` of `nome_produto`) is forced to 0 and only serves as fallback when there are no keywords. Score = max of both; per-interest `limiar_match` overrides the default threshold 0.6. `palavras_excluidas` is a hard veto. Price extraction via regex (`R$ 1.234,56` etc.), lowest price used, dropped if above `preco_maximo`.
- **LLM validation** (optional, `app/services/llm_validator_service.py`): matcher candidates are re-checked by an LLM (LangChain + OpenRouter, `LLM_MODEL`) before a match/alert is created. Gated by `OPENROUTER_API_KEY`; fail-open (approves on no-key/disabled/error). Rejections are logged as `llm_rejected`, not stored.
- **structlog** for structured logging, **pydantic-settings** for config

### Frontend
- **Vite** + **React 19** + **TypeScript 6**
- **TanStack Router** (file-based, auto code-splitting via `@tanstack/router-plugin`)
- **TanStack Query** (server state management)
- **Tailwind CSS v4** via `@tailwindcss/vite` plugin
- **shadcn/ui** components (`button`, `card`, `input`, `label`, `table`, `badge`, `select`, `switch`)
- Path alias `@/` → `src/`

## Directory structure

```
server/
  app/
    api/routes/     # FastAPI routers (health, interests, matches, messages)
    core/           # config (Settings via pydantic-settings), logging, exceptions
    database/       # engine, session, declarative Base
    models/         # SQLAlchemy ORM (TelegramMessage, ProductInterest, PromotionMatch)
    repositories/   # data access layer
    schemas/        # Pydantic request/response
    services/       # business logic (interest, matcher, llm_validator, alert, message)
    telegram/       # Telethon client, auth (interactive code prompt), listener
    workers/        # background worker entrypoint
web/
  src/
    routes/         # File-based routes (TanStack Router auto-generates routeTree.gen.ts)
    components/ui/  # shadcn components
    lib/            # Utilities (api client, cn helper)
    hooks/          # TanStack Query hooks
```

## Setup and run

### Backend (porta 3333)
```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
cp .env.example .env      # fill in TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
pip install -r requirements.txt
python3 run.py            # lê API_HOST e API_PORT do .env
```

First run **requires** a Telegram verification code via console `input()`.

### Frontend (porta 3000)
```bash
cd web
pnpm install
pnpm dev
```

## Docker

```bash
cd server
docker compose up --build
```

First-run login: `docker attach telegram-promobot` to type the verification code.

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
| GET | `/health` | app status |
| POST | `/interests` | create with `nome_produto`, `preco_maximo`, `limiar_match`, `palavras_chave`, `palavras_excluidas` |
| GET | `/interests` | filter with `?ativo=true` |
| PUT | `/interests/{id}` | partial update |
| DELETE | `/interests/{id}` | — |
| GET | `/matches` | list matches (includes LLM-rejected, `llm_aprovado=false`) |
| GET | `/messages` | list stored (matched) messages |
| POST | `/matcher/preview` | dry-run scoring of a candidate interest against recent stored messages |
| GET / PUT | `/settings` | read/update `app_config` (e.g. `alert_target`) |
| GET | `/telegram/chats` | list the user session's dialogs |
