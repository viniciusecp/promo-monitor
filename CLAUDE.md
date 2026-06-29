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
- **First run blocks on `input()`** for a Telegram verification code (interactive login in `app/telegram/auth.py`). Under Docker: `docker attach telegram-promobot`.
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

### Docker
```bash
cd server && docker compose up --build
```

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
- API client in `src/lib/api.ts`; types in `src/types/`. CORS on the backend only allows `http://localhost:3000`.
