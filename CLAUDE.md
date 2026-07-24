# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A more detailed companion document lives in `AGENTS.md` (API table, Docker notes, directory tree) — keep both in sync when architecture changes.

## What this is

A Telegram promotion monitor. The backend joins Telegram groups via a Telethon user-session, scores every incoming message against user-defined product "interests", and records matches. The frontend is a dashboard to manage interests and browse messages/matches.

## Commands

### Backend (`server/`, runs on port 3333)
```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
cp .env.example .env      # set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
pip install -r requirements.txt
python3 run.py            # uvicorn with reload, reads API_HOST/API_PORT from .env
```
- **First run blocks on `input()`** for a Telegram verification code (interactive login in `app/telegram/auth.py`). Under Docker: `docker attach promo-monitor-backend`.
- **Matcher tests** live in `server/tests/test_matcher.py`. Run `python -m pytest tests/test_matcher.py` (if pytest is installed) or standalone with no deps: `python tests/test_matcher.py`. There is no linter, typechecker, or CI. `requirements.txt` has version ranges, no lockfile.

### Frontend (`web/`, runs on port 3000)
```bash
cd web
pnpm install
pnpm dev          # vite dev server
pnpm build        # tsc -b && vite build
pnpm lint         # eslint
```
`pnpm` is the package manager (`pnpm-lock.yaml` is committed).

### Docker (both services)
The root `docker-compose.yml` builds and runs both services: `promo-monitor-backend`
(uvicorn on `API_PORT`) and `promo-monitor-web` (nginx serving the built SPA on `WEB_PORT`).
```bash
cp .env.example .env                 # VITE_API_URL (build-time), API_PORT, WEB_PORT
cp server/.env.example server/.env   # TELEGRAM_API_ID/HASH/PHONE etc.
docker compose up --build -d
docker attach promo-monitor-backend  # first run only: type the Telegram code, then Ctrl-P Ctrl-Q
```
- `VITE_API_URL` is baked into the frontend **at build time** — rebuild the `web` image to change it.
- Telegram session and the SQLite db persist via bind mounts (`server/session/`, `server/data/`).
- The backend Dockerfile reads the listen port from `API_PORT`; keep it a single uvicorn process (the Telegram worker shares the event loop — multiple workers would duplicate the listener).

## Architecture

### Backend pipeline (the core flow)
1. `app/main.py` lifespan creates tables, runs `ensure_columns()` (a lightweight additive migration — new columns are ALTERed in, there is no Alembic), then spawns `run_telegram_worker()` as an asyncio task **inside the FastAPI process** — the listener and the HTTP API share one event loop.
2. `app/workers/telegram_worker.py` starts the user-session client, starts the bot (see below), builds a `MessageService`, and attaches `app/telegram/listener.py`. It reloads active interests **every 60s** so interest edits take effect without a restart.
3. `app/telegram/listener.py` handles incoming **group/channel** messages only (DMs and self-sent messages are ignored to avoid an alert→match feedback loop) → hands each to `message_service.process_message`.
4. `app/services/message_service.py` evaluates interests **before persisting**: only messages that produce a match are written to the DB — non-matching messages are discarded. So the `messages` table is *matched* messages, not a raw firehose.
5. `app/services/matcher_service.py` `composite_matcher.match(text, interest)` scores text against a `ProductInterest`. All text is run through `normalize_text` (lowercase, strip accents, alnum-only):
   - `palavras_excluidas` hit ⇒ immediate score `0.0` (hard veto; substring match, not word-boundary).
   - **Keyword is authoritative.** `KeywordMatchStrategy` is OR-semantics with word boundaries: score `1.0` if *any* `palavras_chave` entry is present, else `0.0`. `FuzzyMatchStrategy` is rapidfuzz `token_set_ratio` of `nome_produto`. **If the interest defines any keyword, fuzzy is forced to `0.0`** — fuzzy only acts as a fallback when there are no keywords. Final score = `max(keyword, fuzzy)`.
   - Prices are regex-extracted (`extract_prices`, handles `R$ 1.234,56`, `X reais`, BR vs US decimals via `_parse_price`); the **lowest** extracted price is used, and a match is dropped if it exceeds `preco_maximo`.
   - Threshold is per-interest `limiar_match`, falling back to `settings.match_score_threshold` (default **0.6**).
6. Candidates that clear the threshold and price gate are re-checked by `app/services/llm_validator_service.py` (`LLMValidator`, LangChain + OpenRouter, model `LLM_MODEL`). It is **fail-open**: with no `OPENROUTER_API_KEY`, `llm_validation_enabled=False`, or on error it approves. Rejected candidates are **still stored** as a `PromotionMatch` (`llm_aprovado=False`, for audit) but do **not** trigger an alert.
7. Approved matches call `alert_service.send_alert`, which pushes a Telegram message via the **bot client** to the configured `alert_target` chat.

### Telegram: two clients
- **User session** (`get_client`, `TELEGRAM_PHONE`): the listener that reads groups/channels. First run blocks on `input()` for the login code.
- **Bot** (`get_bot_client`, `TELEGRAM_BOT_TOKEN`, optional): sends the alerts. Its `/start` handler saves the sender's chat as `app_config.alert_target` (one-click alert setup — see the frontend `BotSetupGuide`); `/id` echoes the chat id. Without `TELEGRAM_BOT_TOKEN` the bot is skipped and no alerts are sent.

### Backend layering
Strict layered architecture — respect these boundaries when adding features:
`api/routes` → `services` (business logic) → `repositories` (data access, `BaseRepository[T]` generic) → `models` (SQLAlchemy ORM). `schemas` are Pydantic request/response DTOs; `core` holds `Settings` (pydantic-settings), structlog setup, and exceptions.

- **SQLite** via SQLAlchemy. `app/database/session.py` enables WAL mode + foreign keys through a `@event.listens_for` connect hook.
- **Portuguese domain names** throughout models/schemas/routes: `nome_produto`, `preco_maximo`, `palavras_chave`, `palavras_excluidas`, `ativo`. Keep new domain fields in Portuguese to match.
- `data/` and `session/` dirs are created at runtime by `Settings.model_post_init` and are gitignored.

### Frontend
- **React 19 + Vite + TypeScript**, **TanStack Router** (file-based routing — `routeTree.gen.ts` is auto-generated, do not edit by hand), **TanStack Query** for server state (hooks in `src/hooks/`).
- **Tailwind CSS v4** via `@tailwindcss/vite`, **shadcn/ui** components in `src/components/ui/`. Path alias `@/` → `src/`.
- API client in `src/lib/api.ts` (base URL from `VITE_API_URL`, falls back to `http://localhost:3333`); types in `src/types/`. CORS on the backend is open to all origins (`allow_origins=["*"]`).
