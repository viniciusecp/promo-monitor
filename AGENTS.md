# promo-monitor

**Backend:** Python 3.12 + FastAPI. **Frontend:** React + Vite + TanStack Router.

## Architecture

### Backend
- **FastAPI** app with lifespan that spawns a **Telethon** background worker (`app/workers/telegram_worker.py`) to listen to Telegram groups in real time
- **SQLite** via SQLAlchemy (WAL mode + foreign keys enabled via `@event.listens_for` in `app/database/session.py`)
- **Repository pattern** (`BaseRepository[T]` in `app/repositories/base.py`)
- **Portuguese naming** in models/schemas/routes (`nome_produto`, `preco_maximo`, `palavras_chave`, `palavras_excluidas`, `ativo`)
- **Composite matching**: keyword (OR-semantics, word boundary) is authoritative — when an interest has any `palavras_chave`, fuzzy (rapidfuzz `token_set_ratio` of `nome_produto`) is forced to 0 and only serves as fallback when there are no keywords. Score = max of both; per-interest `limiar_match` overrides the default threshold 0.6. `palavras_excluidas` is a hard veto. Price extraction via regex (`R$ 1.234,56` etc.), lowest price used, dropped if above `preco_maximo`.
- **LLM validation** (optional, `app/services/llm_validator_service.py`): matcher candidates are re-checked by an LLM (LangChain + OpenRouter, `LLM_MODEL`) before a match/alert is created. Gated by `OPENROUTER_API_KEY`; fail-open (approves on no-key/disabled/error). Rejections **are** stored as a `PromotionMatch` with `llm_aprovado=false` (for audit) — they just don't trigger an alert.
- **Read state**: `promotion_matches.lido` / `lido_em` back the "unread" feed. There is no Alembic — new columns go in `_COLUMN_MIGRATIONS` in `app/database/session.py` and are `ALTER TABLE ADD COLUMN`'d at startup. `ensure_columns()` also runs a one-shot backfill (guarded by "did I just create this column?") marking pre-existing rows as read, so the unread counter doesn't start with the whole table in it.
- **Timezone**: `DateTime(timezone=True)` columns store **naive UTC** — SQLite's bind processor serializes the wall-clock fields and drops tzinfo without converting. Any datetime used in a comparison must go through `app/core/timeutils.py`. The `hoje` period is a calendar boundary in the *user's* timezone (`?tz=`, falling back to `APP_TIMEZONE`); `7d`/`30d` are rolling windows.
- **structlog** for structured logging, **pydantic-settings** for config

### Frontend
- **Vite** + **React 19** + **TypeScript 6**
- **TanStack Router** (file-based, auto code-splitting via `@tanstack/router-plugin`)
- **TanStack Query** (server state management)
- **Tailwind CSS v4** via `@tailwindcss/vite` plugin
- **shadcn/ui** components, `base-nova` style over **base-ui** (`button`, `card`, `input`, `label`, `table`, `badge`, `select`, `switch`, `dialog`, `sheet`, `skeleton`, `textarea`, `sonner`)
- Path alias `@/` → `src/`
- `/` **is** the matches feed (`/matches` only redirects to it). Unread matches are visually highlighted inside a date-sorted list — `lido` is not a sort key, because re-sorting on read would make rows jump between offset-paginated pages.
- Polling, not SSE. `useMatchesInfinite` stops polling past page 1 (a background refetch of N pages against a shifted offset window duplicates/drops rows); `/matches/stats` polls unconditionally so the unread badge stays live regardless.
- `Select.Root` needs the `items` prop for `SelectValue` to render a label instead of the raw value. Never use `<SelectItem value="">` — use a sentinel like `'todos'`.

## Directory structure

```
server/
  app/
    api/routes/     # FastAPI routers (health, interests, matcher, matches, messages, settings, telegram)
    core/           # config, logging, exceptions, links (build_message_link), timeutils (naive-UTC + tz)
    database/       # engine, session (+ ensure_columns), declarative Base
    models/         # SQLAlchemy ORM (TelegramMessage, ProductInterest, PromotionMatch, AppConfig)
    repositories/   # data access layer
    schemas/        # Pydantic request/response
    services/       # business logic (interest, matcher, llm_validator, alert, message, match)
    telegram/       # Telethon client, auth (interactive code prompt), listener
    workers/        # background worker entrypoint
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
| GET | `/matches` | envelope `{items,total,has_more}`. Filters: `periodo` (`hoje\|7d\|30d\|tudo`) + `tz`, `nao_lidos`, `status` (repeatable: `alertado`, `reprovado`), `chat_id`, `preco_min`, `preco_max`, `order_by` (`data\|preco\|score`), `order_dir`, `skip`, `limit`. Includes LLM-rejected (`llm_aprovado=false`) |
| GET | `/matches/stats` | `?tz=` → `nao_lidos`, `novos_hoje`, `ultimas_24h`, `ultimos_7d`, `interesses_ativos` (global, filter-independent — backs the nav badge) |
| GET | `/matches/chats` | distinct chats **that have matches**, with counts (for the group filter). Not `/telegram/chats`, which round-trips Telethon |
| POST | `/matches/{id}/read` | mark read |
| POST | `/matches/{id}/unread` | mark unread |
| POST | `/matches/read-all` | body = the same filter model as `GET /matches`, so bulk-read hits exactly what's on screen. Returns `{updated}` |
| GET | `/messages` | list stored (matched) messages |
| POST | `/matcher/preview` | dry-run scoring of a candidate interest against recent stored messages |
| GET / PUT | `/settings` | read/update `app_config` (e.g. `alert_target`) |
| GET | `/telegram/chats` | list the user session's dialogs |
