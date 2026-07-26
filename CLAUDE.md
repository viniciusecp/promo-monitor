# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A more detailed companion document lives in `AGENTS.md` (API table, Docker notes, directory tree) — keep both in sync when architecture changes.

## What this is

A Telegram promotion monitor. The backend joins Telegram groups via a Telethon user-session, scores every incoming message against user-defined product "interests", and records matches. The frontend is a dashboard to manage interests and browse the matched promotions — `/` is the matches feed, with per-match read/unread state.

## Commands

### Backend (`server/`, runs on port 3333)
```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
cp .env.example .env      # set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
pip install -r requirements.txt
python3 run.py            # uvicorn with reload, reads API_HOST/API_PORT from .env
```
- **First run does not block.** With no valid session the backend logs `telegram_login_required` and serves HTTP idle; the verification code is typed in the web panel (`/login`). There is no `input()` anywhere in `server/app` — keep it that way, it would freeze the shared event loop.
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
# First run: open the panel, you land on /login → "Enviar código" → type it there.
```
- `VITE_API_URL` is baked into the frontend **at build time** — rebuild the `web` image to change it.
- **The login and settings endpoints are unauthenticated by design** (the operator runs this on a trusted local server). The 2FA password crosses plain HTTP on a CORS-`*` API — never port-forward this stack to the internet.
- Telegram session and the SQLite db persist via bind mounts (`server/session/`, `server/data/`).
- The backend Dockerfile reads the listen port from `API_PORT`; keep it a single uvicorn process (the Telegram worker shares the event loop — multiple workers would duplicate the listener).

## Architecture

### Backend pipeline (the core flow)
1. `app/main.py` lifespan creates tables, runs `ensure_columns()` (a lightweight additive migration — new columns are ALTERed in, there is no Alembic), then spawns `run_telegram_worker()` as an asyncio task **inside the FastAPI process** — the listener and the HTTP API share one event loop.
2. `app/workers/telegram_worker.py` only connects and checks the saved session. If it is valid it calls `supervisor.ensure_started()`; if not it logs `telegram_login_required` and returns, leaving the API up to serve the login screen. `app/workers/supervisor.py` is what builds the bot, the `MessageService` and `app/telegram/listener.py`, and it reloads active interests **every 60s** so interest edits take effect without a restart.
3. `app/telegram/listener.py` handles incoming **group/channel** messages only (DMs and self-sent messages are ignored to avoid an alert→match feedback loop) → hands each to `message_service.process_message`.
4. `app/services/message_service.py` evaluates interests **before persisting**: only messages that produce a match are written to the DB — non-matching messages are discarded. So the `messages` table is *matched* messages, not a raw firehose.
5. `app/services/matcher_service.py` `composite_matcher.match(text, interest)` scores text against a `ProductInterest`. All text is run through `normalize_text` (lowercase, strip accents, alnum-only):
   - `palavras_excluidas` hit ⇒ immediate score `0.0` (hard veto; substring match, not word-boundary).
   - **Keyword is authoritative.** `KeywordMatchStrategy` is OR-semantics with word boundaries: score `1.0` if *any* `palavras_chave` entry is present, else `0.0`. `FuzzyMatchStrategy` is rapidfuzz `token_set_ratio` of `nome_produto`. **If the interest defines any keyword, fuzzy is forced to `0.0`** — fuzzy only acts as a fallback when there are no keywords. Final score = `max(keyword, fuzzy)`.
   - Prices are regex-extracted (`extract_prices`, handles `R$ 1.234,56`, `X reais`, BR vs US decimals via `_parse_price`); the **lowest** extracted price is used, and a match is dropped if it exceeds `preco_maximo`.
   - Threshold is per-interest `limiar_match`, falling back to `settings.match_score_threshold` (default **0.6**).
6. Candidates that clear the threshold and price gate are re-checked by `app/services/llm_validator_service.py` (`LLMValidator`, LangChain + OpenRouter, model `LLM_MODEL`). It is **fail-open**: with no `OPENROUTER_API_KEY`, `llm_validation_enabled=False`, or on error it approves. Rejected candidates are **still stored** as a `PromotionMatch` (`llm_aprovado=False`, for audit) but do **not** trigger an alert.
7. Approved matches call `alert_service.send_alert`, which pushes a Telegram message via the **bot client** to the configured `alert_target` chat.

### Reading the feed (`app/services/match_service.py`)
- `promotion_matches.lido` / `lido_em` hold per-match read state. `GET /matches` returns an envelope `{items, total, has_more}` and takes filters for period, status, chat, price range and ordering; `POST /matches/read-all` takes **the same filter model as its body**, so bulk-read provably covers exactly what the list shows. `MatchRepository._where_clauses` is the single source of the WHERE for list, count and bulk-update.
- Ordering always appends `desc(PromotionMatch.id)` as a tiebreaker. `preco_encontrado` is nullable and `score` clusters at 1.0 — without it, offset pagination repeats and skips rows across pages.
- **Timezones are load-bearing here.** `DateTime(timezone=True)` columns store *naive UTC*: SQLite's bind processor serializes the wall-clock fields and drops tzinfo without converting first. Every boundary is normalized through `app/core/timeutils.py` (`utcnow_naive`, `resolve_timezone`). `hoje` is a calendar boundary in the user's tz (`?tz=`, falling back to `APP_TIMEZONE`, default `America/Sao_Paulo`); `7d`/`30d` are rolling windows. A bare `datetime.now()` in this code is a 3-hour bug in Brazil.
- `alertState` ('sent'/'failed'/'skipped') is derived **client-side** in `web/src/lib/match.ts` from `alerted`/`preco_ok`/`llm_aprovado`. `failed` is an inference ("approved but not alerted"), not a recorded fact — it can't distinguish "no target configured" from "bot offline" from "send raised". Making it truthful would mean new columns on `promotion_matches`.

### Telegram: two clients
- **User session** (`get_client`, `TELEGRAM_PHONE`): the listener that reads groups/channels. Logged in from the web (see below).
- **Bot** (`bot_manager`, optional): sends the alerts. Its `/start` handler saves the sender's chat as `app_config.alert_target` — **the only writer of that field**. The panel is read-only here (`AlertStatus` shows "waiting for /start" or "active", plus the test button) and `SettingsUpdate` deliberately does not accept `alert_target`: a chat picked from a list is one the *user session* can see, not necessarily one the bot can post to, which produced silent send failures. `/id` echoes the chat id. Without a token the bot is skipped and no alerts are sent. **The token lives in `app_config.telegram_bot_token`, not in `settings`** — `TELEGRAM_BOT_TOKEN` only seeds it once (via the `ensure_columns` backfill for existing DBs, via `AppConfigRepository.get_or_create` for new ones), and afterwards the panel owns it.

### Auth + worker supervisor
- `app/telegram/auth.py` is a state machine (`unauthenticated → awaiting_code → awaiting_password → authenticated`) driven by `POST /telegram/auth/*`. Its `asyncio.Lock` **fast-fails** with 409 instead of queueing: two concurrent code submissions would fight over the single `phone_code_hash`. The hash itself is deliberately not stored here — Telethon caches it in `client._phone_code_hash[phone]` and `sign_in` resolves it.
- Three things that must not regress: **never `client.start()`** (it prompts on stdin, unlike `connect()`); **never send a code at boot** (with `restart: on-failure:5`, one burned code per restart lands you in a multi-hour `FloodWaitError`); and `PhoneCodeExpiredError` must reset the state to `unauthenticated`, because Telethon pops the hash and any retry then raises an opaque `ValueError`.
- `app/workers/supervisor.py` owns the pipeline. `ensure_started()` is idempotent (guarded by a lock *and* by `MessageListener._handler_registered`) — a double registration means every message is processed twice, i.e. duplicated matches and alerts. `refresh_interests` and the watchdog are **stored** tasks, cancelled in `stop()`.
- `run_until_disconnected()` is gone on purpose: it only kept the coroutine alive, while Telethon's own tasks (spawned in `connect()`) dispatch events. Removing it is what lets an HTTP handler start the pipeline. Its real job — noticing a dropped connection — moved to `_watchdog_loop` (30s), which also detects a session revoked from another device and sends the UI back to `/login`.
- The long-lived DB session belongs to the supervisor (`self._db`) and closes only in `stop()`. Closing it in a `finally`, as the old worker did, would leave every repository holding a dead session the moment setup returned.
- Changing the bot token calls `bot_manager.apply_token`, which **deletes `bot.session`**. `client.start(bot_token=...)` skips sign-in when the session is already authorized, so without the delete a token swap silently keeps alerting through the old bot. For the same reason `AlertService` takes a `bot_provider` callable, never a client instance.

### Backend layering
Strict layered architecture — respect these boundaries when adding features:
`api/routes` → `services` (business logic) → `repositories` (data access, `BaseRepository[T]` generic) → `models` (SQLAlchemy ORM). `schemas` are Pydantic request/response DTOs; `core` holds `Settings` (pydantic-settings), structlog setup, and exceptions.

- **SQLite** via SQLAlchemy. `app/database/session.py` enables WAL mode + foreign keys through a `@event.listens_for` connect hook.
- **Adding a column**: add the `mapped_column` to the model *and* an entry to `_COLUMN_MIGRATIONS` with SQLite DDL (a `NOT NULL` column needs a literal `DEFAULT`). `ensure_columns()` tracks which columns it just created and can run a guarded one-shot backfill off that — that's how pre-existing matches were marked `lido=1` so the unread counter didn't start with the whole table in it. Keep its return type `None`; `app/main.py` calls it for effect. `app_config` now has an entry too (`telegram_bot_token`), with a backfill that seeds it from `TELEGRAM_BOT_TOKEN` — note that a *fresh* install needs the seed in `AppConfigRepository.get_or_create` instead, since the row is created after the migration runs.
- **Portuguese domain names** throughout models/schemas/routes: `nome_produto`, `preco_maximo`, `palavras_chave`, `palavras_excluidas`, `ativo`. Keep new domain fields in Portuguese to match.
- `data/` and `session/` dirs are created at runtime by `Settings.model_post_init` and are gitignored.

### Frontend
- **React 19 + Vite + TypeScript**, **TanStack Router** (file-based routing — `routeTree.gen.ts` is auto-generated, do not edit by hand), **TanStack Query** for server state (hooks in `src/hooks/`).
- **Tailwind CSS v4** via `@tailwindcss/vite`, **shadcn/ui** in `src/components/ui/` (`base-nova` style, **base-ui** primitives under the hood — not Radix). Path alias `@/` → `src/`.
- API client in `src/lib/api.ts` (base URL from `VITE_API_URL`, falls back to `http://localhost:3333`); types in `src/types/`. CORS on the backend is open to all origins (`allow_origins=["*"]`).
- `/` is the matches feed; `/matches` only redirects to it. `MatchTable` (desktop) and `MatchCard` (mobile) are separate components on purpose — shared logic lives in `src/lib/match.ts`, the duplication is layout-only.
- **No SSE/websockets, and no interval polling on the feed.** Freshness comes from the window-focus refetch: `useMatchesInfinite` sets `refetchOnWindowFocus` *only while page 1 is the only loaded page* (a refetch with N pages loaded re-fetches all of them against a shifted offset window, duplicating/dropping rows), and `/matches/stats` refetches on focus unconditionally. The global `staleTime: 15_000` in `main.tsx` is what keeps a quick alt-tab from firing requests. Past page 1 the only refresh is `LastUpdated`'s manual button — that's why the "atualizado há X" indicator exists. `useMarkRead` patches optimistically and invalidates **only** `['matches','stats']` — invalidating the list would refetch every loaded page and throw away the scroll position.
- Responsive gotchas worth not re-breaking: the flex container in `__root.tsx` needs `min-w-0` (otherwise `flex-1`'s `min-width:auto` stops the tables' `overflow-x-auto` from ever engaging, and the page scrolls horizontally); a `max-w-*` at a `DialogContent` call-site overrides its mobile clamp via `tailwind-merge`, so pair it (`max-w-[calc(100%-2rem)] sm:max-w-lg`).
- base-ui `Select` differs from Radix: pass `items` to `Select.Root` or `SelectValue` renders the raw value instead of the label, and `<SelectItem value="">` silently shadows the placeholder instead of throwing — use a sentinel (`'todos'`) mapped to `undefined`.
- The `.dark` class is applied on `<html>` in `index.html`; shadcn tokens resolve to the dark palette. Existing components still hardcode `zinc-*`, which is fine — just don't assume the token palette is light.
