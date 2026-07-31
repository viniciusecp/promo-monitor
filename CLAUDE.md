# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A more detailed companion document lives in `AGENTS.md` (API table, Docker notes, directory tree) — keep both in sync when architecture changes.

## What this is

A Telegram promotion monitor. The backend joins Telegram groups via a Telethon user-session, scores every incoming message against user-defined product "interests", and records matches. The frontend is a dashboard to manage interests and browse the matched promotions — `/` is the matches feed, with per-match read/unread state. The panel is **behind a login** (e-mail + password, invite-only, roles `owner`/`viewer`) because it is meant to be reachable from a public network.

## Commands

### Backend (`server/`, runs on port 3333)
```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
cp .env.example .env      # set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
pip install -r requirements.txt
python3 run.py            # uvicorn with reload, reads API_PORT from .env
```
- **First run does not block.** With no valid session the backend logs `telegram_login_required` and serves HTTP idle; the verification code is typed in the web panel (`/telegram`, owner-only). There is no `input()` anywhere in `server/app` — keep it that way, it would freeze the shared event loop.
- **Tests** live in `server/tests/`: `test_matcher.py` and `test_auth.py`. Run `python -m pytest tests/` or standalone (`python tests/test_auth.py`). `test_auth.py` sets `DATABASE_URL` to a temp SQLite **before importing `app`** — the engine is built at import of `app.database.session`, so a later assignment has no effect. There is no linter, typechecker, or CI. `requirements.txt` has version ranges, no lockfile.

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
The root `docker-compose.yml` builds and runs both services: `promo-monitor-server`
(uvicorn on `API_PORT`) and `promo-monitor-web` (nginx serving the built SPA on `WEB_PORT`).
```bash
cp .env.example .env                 # WEB_PORT (the only published port, default 5000)
cp server/.env.example server/.env   # TELEGRAM_API_ID/HASH/PHONE + AUTH_SEED_EMAIL/PASSWORD
docker compose up --build -d
# First run: open the panel → log in with AUTH_SEED_* → forced password change →
# Telegram connect screen → "Enviar código".
```
- **Single origin.** The `web` container's nginx serves the SPA *and* proxies `/api/*` to `backend:3333`; the backend publishes **no host port**. So: `VITE_API_URL` is gone (the client calls the relative `/api`, so changing IP/domain needs no image rebuild), the session cookie needs no CORS, and `pnpm dev` mirrors this with `server.proxy` in `vite.config.ts` — where `changeOrigin` is deliberately **false**, since a rewritten Host breaks the backend's Origin check.
- nginx must send `proxy_set_header Host $http_host`, **not** `$host`: `$host` drops the port, and the backend would then compare Origin `http://ip:5000` against `http://ip` and reject every write, login included.
- **Without `AUTH_SEED_EMAIL`/`AUTH_SEED_PASSWORD` on a fresh DB nobody can get in** — there is no open signup and no bootstrap route. The backend logs `auth_no_users`.
- **The stack still serves plain HTTP by operator decision.** The login password, the Telegram 2FA password and the session cookie all travel in the clear; the gate stops whoever merely knows the URL, not whoever watches the network. With a TLS proxy in front, `AUTH_COOKIE_SECURE=true` is the only app-side change — do not set it before HTTPS exists, or the cookie is never sent and nobody can log in.
- Telegram session and the SQLite db persist via bind mounts (`server/session/`, `server/data/`).
- The backend Dockerfile runs uvicorn with `--proxy-headers` (the login rate limiter needs the real client IP, not nginx's) and keeps a single uvicorn process (the Telegram worker shares the event loop — multiple workers would duplicate the listener).

## Architecture

### Backend pipeline (the core flow)
1. `app/main.py` lifespan creates tables, runs `ensure_columns()` (a lightweight additive migration — new columns are ALTERed in, there is no Alembic), seeds the first owner + purges expired sessions (`_bootstrap_auth`), then spawns `run_telegram_worker()` as an asyncio task **inside the FastAPI process** — the listener and the HTTP API share one event loop.
2. `app/workers/telegram_worker.py` only connects and checks the saved session. If it is valid it calls `supervisor.ensure_started()`; if not it logs `telegram_login_required` and returns, leaving the API up to serve the login screen. `app/workers/supervisor.py` is what builds the bot, the `MessageService` and `app/telegram/listener.py`, and it reloads active interests **every 60s** so interest edits take effect without a restart.
3. `app/telegram/listener.py` handles incoming **group/channel** messages only (DMs and self-sent messages are ignored to avoid an alert→match feedback loop) → hands each to `message_service.process_message`.
4. `app/services/message_service.py` evaluates interests **before persisting**: only messages that produce a match are written to the DB — non-matching messages are discarded. So the `messages` table is *matched* messages, not a raw firehose.
5. `app/services/matcher_service.py` `composite_matcher.match(text, interest)` scores text against a `ProductInterest`. All text is run through `normalize_text` (lowercase, strip accents, alnum-only):
   - `palavras_excluidas` hit ⇒ immediate score `0.0` (hard veto; substring match, not word-boundary).
   - **Keyword is authoritative.** `KeywordMatchStrategy` is OR-semantics with word boundaries: score `1.0` if *any* `palavras_chave` entry is present, else `0.0`. `FuzzyMatchStrategy` is rapidfuzz `token_set_ratio` of `nome_produto`. **If the interest defines any keyword, fuzzy is forced to `0.0`** — fuzzy only acts as a fallback when there are no keywords. Final score = `max(keyword, fuzzy)`.
   - Prices are regex-extracted (`extract_prices`, handles `R$ 1.234,56`, `X reais`, BR vs US decimals via `_parse_price`); the **lowest** extracted price is used, and a match is dropped if it exceeds `preco_maximo`.
   - Threshold is hardcoded at 0.6.
6. Candidates that clear the threshold and price gate are re-checked by `app/services/llm_validator_service.py` (`LLMValidator`, LangChain + OpenRouter, model `LLM_MODEL`). It is **fail-open**: with no `OPENROUTER_API_KEY`, `llm_validation_enabled=False`, or on error it approves. Rejected candidates are **still stored** as a `PromotionMatch` (`llm_aprovado=False`, for audit) but do **not** trigger an alert.
7. Approved matches call `alert_service.send_alert`, which pushes a Telegram message via the **bot client** to the configured `alert_target` chat.

### Panel auth (login, roles, persistent session)
- **Opaque cookie session, not JWT** — chosen for *revocation*: disabling or deleting a user must kill access immediately, and a JWT only expires. `app/services/auth_service.py` hashes with Argon2id (`pwdlib`, `PasswordHash.recommended()`), stores only the **SHA-256** of the token, and `verify_password` burns the same time on a missing user (throwaway hash) so response timing can't enumerate accounts.
- **Persistent login is three pieces, and missing any one produces "I have to log in constantly"**: (1) the cookie carries `max_age` — without it the browser makes a *session cookie* and drops it on close; (2) `resolve_session` slides the expiry (at most 1×/hour) and returns `(user, renovada)`, and the `renew_session_cookie` middleware in `main.py` re-issues the `Set-Cookie` — extending only the DB row would let the cookie die first; (3) `GET /auth/me` restores it on boot, and `__root.tsx`'s `isLoading` branch must not render `/login` while that call is in flight.
- `set_session_cookie` in `app/api/deps.py` is the **only** place cookie attributes are set. Two emitters with different attributes is a "logs itself out" bug that is very hard to find.
- **The gate is `require_user` on the protected subrouter in `app/api/router.py`**, so a newly added router is closed by default. `require_owner` guards `users`, `settings` and `telegram_auth` — the last one is load-bearing: those routes request a login code and take the 2FA password of the owner's *personal* Telegram account, and `server/session/` is equivalent to that account.
- **No open signup anywhere.** The first owner comes from `AuthService.seed_owner()` in the lifespan, only when `users` is empty, from `AUTH_SEED_EMAIL/PASSWORD` — the same "env seeds once, DB owns it after" contract as the bot token. It is created with `trocar_senha=True` because that password lives in a file on disk.
- `UserService._assert_nao_e_ultimo_owner` blocks demoting/disabling/deleting the last active owner. Without it the panel ends up with nobody able to administer it, and the only recovery is editing the SQLite by hand.
- **CSRF** is `SameSite=Lax` plus the `block_cross_origin_writes` middleware comparing `Origin` to the Host on unsafe methods. `LoginThrottle` (in `app/core/security.py`) rate-limits per (e-mail, IP) in process — safe because there is exactly one uvicorn worker, and keyed on IP so a stranger failing logins can't lock the owner out.
- Frontend: `useSession` maps **401 → `null`**, so "logged out" does not land on `__root`'s "Backend indisponível" screen — that screen must keep meaning *network failure*. The `__root.tsx` gate runs two stages (panel session → Telegram connection) and `useAuthStatus(enabled)` only fires with a session, otherwise the login screen would poll `/telegram/auth/status` into 401s every 3s. A disconnected Telegram redirects the **owner** to `/telegram` but never a viewer (they cannot complete a login that isn't theirs) — `SEM_TELEGRAM_OK` also exempts `/settings`, so the owner can still manage users and the bot token while Telegram is down. `useLogout` (panel) and `useTelegramLogout` are deliberately distinct names.

### Reading the feed (`app/services/match_service.py`)
- `promotion_matches.lido` / `lido_em` hold per-match read state. `GET /matches` returns an envelope `{items, total, has_more}` and takes filters for period, status, chat, price range and ordering; `POST /matches/read-all` takes **the same filter model as its body**, so bulk-read provably covers exactly what the list shows. `MatchRepository._where_clauses` is the single source of the WHERE for list, count and bulk-update.
- Ordering always appends `desc(PromotionMatch.id)` as a tiebreaker. `preco_encontrado` is nullable and `score` clusters at 1.0 — without it, offset pagination repeats and skips rows across pages.
- **Timezones are load-bearing here.** `DateTime(timezone=True)` columns store *naive UTC*: SQLite's bind processor serializes the wall-clock fields and drops tzinfo without converting first. Every boundary is normalized through `app/core/timeutils.py` (`utcnow_naive`, `resolve_timezone`). `hoje` is a calendar boundary in the user's tz (`?tz=`, falling back to `APP_TIMEZONE`, default `America/Sao_Paulo`); `7d`/`30d` are rolling windows. A bare `datetime.now()` in this code is a 3-hour bug in Brazil.
- `alertState` ('sent'/'failed'/'skipped') is derived **client-side** in `web/src/lib/match.ts` from `alerted`/`preco_ok`/`llm_aprovado`. `failed` is an inference ("approved but not alerted"), not a recorded fact — it can't distinguish "no target configured" from "bot offline" from "send raised". Making it truthful would mean new columns on `promotion_matches`.

### Telegram: two clients
- **User session** (`get_client`, `TELEGRAM_PHONE`): the listener that reads groups/channels. Logged in from the web (see below).
- **Bot** (`bot_manager`, optional): sends the alerts. Its `/start` handler saves the sender's chat as `app_config.alert_target` — **the only writer of that field**, and it only accepts `event.sender_id == authenticator.user_id`. That check is load-bearing, not defensive politeness: bot usernames are publicly searchable and `alert_target` is a single column, so an unguarded `/start` from a stranger *hijacks* the destination — they start receiving the promos and the owner silently stops. It fails closed when `user_id` is `None` (the bot can be up before the user session is logged in, since the token is saved from the panel, which has its own login independent of Telegram). Authorization is on the *sender*, so `/start` from inside a group still targets the group. The panel is read-only here (`AlertStatus` shows "waiting for /start" or "active", plus the test button) and `SettingsUpdate` deliberately does not accept `alert_target`: a chat picked from a list is one the *user session* can see, not necessarily one the bot can post to, which produced silent send failures. `/id` echoes the chat id. Without a token the bot is skipped and no alerts are sent. **The token lives in `app_config.telegram_bot_token`** — configured exclusively via the panel (`PUT /settings`), and the panel owns it.

### Auth + worker supervisor
- `app/telegram/auth.py` is a state machine (`unauthenticated → awaiting_code → awaiting_password → authenticated`) driven by `POST /telegram/auth/*`. Its `asyncio.Lock` **fast-fails** with 409 instead of queueing: two concurrent code submissions would fight over the single `phone_code_hash`. The hash itself is deliberately not stored here — Telethon caches it in `client._phone_code_hash[phone]` and `sign_in` resolves it.
- Three things that must not regress: **never `client.start()`** (it prompts on stdin, unlike `connect()`); **never send a code at boot** (with `restart: on-failure:5`, one burned code per restart lands you in a multi-hour `FloodWaitError`); and `PhoneCodeExpiredError` must reset the state to `unauthenticated`, because Telethon pops the hash and any retry then raises an opaque `ValueError`.
- `app/workers/supervisor.py` owns the pipeline. `ensure_started()` is idempotent (guarded by a lock *and* by `MessageListener._handler_registered`) — a double registration means every message is processed twice, i.e. duplicated matches and alerts. `refresh_interests` and the watchdog are **stored** tasks, cancelled in `stop()`.
- `run_until_disconnected()` is gone on purpose: it only kept the coroutine alive, while Telethon's own tasks (spawned in `connect()`) dispatch events. Removing it is what lets an HTTP handler start the pipeline. Its real job — noticing a dropped connection — moved to `_watchdog_loop` (30s), which also detects a session revoked from another device and sends the UI back to `/telegram`.
- The long-lived DB session belongs to the supervisor (`self._db`) and closes only in `stop()`. Closing it in a `finally`, as the old worker did, would leave every repository holding a dead session the moment setup returned.
- Changing the bot token calls `bot_manager.apply_token`, which **deletes `bot.session`**. `client.start(bot_token=...)` skips sign-in when the session is already authorized, so without the delete a token swap silently keeps alerting through the old bot. For the same reason `AlertService` takes a `bot_provider` callable, never a client instance.

### Backend layering
Strict layered architecture — respect these boundaries when adding features:
`api/routes` → `services` (business logic) → `repositories` (data access, `BaseRepository[T]` generic) → `models` (SQLAlchemy ORM). `schemas` are Pydantic request/response DTOs; `core` holds `Settings` (pydantic-settings), structlog setup, exceptions, and `security` (Argon2id, session tokens, `LoginThrottle`). `api/deps.py` holds the auth dependencies (`require_user`, `require_owner`) and the session-cookie helpers.

- **SQLite** via SQLAlchemy. `app/database/session.py` enables WAL mode + foreign keys through a `@event.listens_for` connect hook.
- **Adding a column**: add the `mapped_column` to the model *and* an entry to `_COLUMN_MIGRATIONS` with SQLite DDL (a `NOT NULL` column needs a literal `DEFAULT`). `ensure_columns()` tracks which columns it just created and can run a guarded one-shot backfill off that — that's how pre-existing matches were marked `lido=1` so the unread counter didn't start with the whole table in it. Keep its return type `None`; `app/main.py` calls it for effect. `app_config` also has an entry (`telegram_bot_token`), but that column is configured exclusively via the panel, not seeded from env vars.
- **Portuguese domain names** throughout models/schemas/routes: `nome_produto`, `preco_maximo`, `palavras_chave`, `palavras_excluidas`, `ativo`. Keep new domain fields in Portuguese to match.
- `data/` and `session/` dirs are created at runtime by `Settings.model_post_init` and are gitignored.

### Frontend
- **React 19 + Vite + TypeScript**, **TanStack Router** (file-based routing — `routeTree.gen.ts` is auto-generated, do not edit by hand), **TanStack Query** for server state (hooks in `src/hooks/`).
- **Tailwind CSS v4** via `@tailwindcss/vite`, **shadcn/ui** in `src/components/ui/` (`base-nova` style, **base-ui** primitives under the hood — not Radix). Path alias `@/` → `src/`.
- API client in `src/lib/api.ts`: base URL is `/api` (same origin — nginx in prod, `server.proxy` in dev), and every request sends `credentials: 'include'` because the session cookie is `HttpOnly` and there is no token in JS to put in a header. Types in `src/types/`. CORS is **off** by default (`settings.cors_origins` empty); it only turns on, with explicit origins and `allow_credentials=True`, if someone points the dev panel straight at port 3333 — the old `allow_origins=["*"]` is incompatible with credentialed requests.
- Routes: `/login` is the **panel** login (e-mail + password); `/telegram` is the Telegram account connection (owner-only) that used to live at `/login`; `/trocar-senha` is the forced password change. `/` is the matches feed; `/matches` only redirects to it. `MatchTable` (desktop) and `MatchCard` (mobile) are separate components on purpose — shared logic lives in `src/lib/match.ts`, the duplication is layout-only.
- **No SSE/websockets, and no interval polling on the feed.** Freshness comes from the window-focus refetch: `useMatchesInfinite` sets `refetchOnWindowFocus` *only while page 1 is the only loaded page* (a refetch with N pages loaded re-fetches all of them against a shifted offset window, duplicating/dropping rows), and `/matches/stats` refetches on focus unconditionally. The global `staleTime: 15_000` in `main.tsx` is what keeps a quick alt-tab from firing requests. Past page 1 the only refresh is `LastUpdated`'s manual button — that's why the "atualizado há X" indicator exists. `useMarkRead` patches optimistically and invalidates **only** `['matches','stats']` — invalidating the list would refetch every loaded page and throw away the scroll position.
- Responsive gotchas worth not re-breaking: the flex container in `__root.tsx` needs `min-w-0` (otherwise `flex-1`'s `min-width:auto` stops the tables' `overflow-x-auto` from ever engaging, and the page scrolls horizontally); a `max-w-*` at a `DialogContent` call-site overrides its mobile clamp via `tailwind-merge`, so pair it (`max-w-[calc(100%-2rem)] sm:max-w-lg`).
- base-ui `Select` differs from Radix: pass `items` to `Select.Root` or `SelectValue` renders the raw value instead of the label, and `<SelectItem value="">` silently shadows the placeholder instead of throwing — use a sentinel (`'todos'`) mapped to `undefined`.
- The `.dark` class is applied on `<html>` in `index.html`; shadcn tokens resolve to the dark palette. Existing components still hardcode `zinc-*`, which is fine — just don't assume the token palette is light.
