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
- No test runner, linter, or typechecker is configured for the backend. `requirements.txt` has version ranges, no lockfile.

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
1. `app/main.py` lifespan creates tables and spawns `run_telegram_worker()` as an asyncio task **inside the FastAPI process** — the listener and the HTTP API share one event loop.
2. `app/telegram/listener.py` receives messages → persists them via `message_service` → runs the matcher.
3. `app/services/matcher_service.py` `CompositeMatcher` scores text against each `ProductInterest`:
   - `palavras_excluidas` hit ⇒ immediate score `0.0` (hard veto).
   - Score = `max(KeywordMatchStrategy, FuzzyMatchStrategy)`. Keyword = fraction of `palavras_chave` present; Fuzzy = rapidfuzz `partial_ratio` of `nome_produto`. All text passes through `normalize_text` (lowercase, strip accents, alnum-only).
   - Prices are regex-extracted (`extract_prices`, handles `R$ 1.234,56`, `X reais`, etc.).
   - Threshold for a match is **0.6**; matches above it create a `PromotionMatch` and trigger `alert_service`.

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
