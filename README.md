# Promo Monitor

Monitor de promoções no Telegram. O backend entra nos seus grupos/canais via uma sessão de usuário do Telegram (Telethon), pontua cada mensagem recebida contra "interesses" de produto que você define, registra os matches e te notifica na DM através de um **bot do Telegram**. O frontend é um painel para gerenciar interesses e navegar pelas mensagens/matches.

```
┌──────────────┐    mensagens     ┌─────────────────────────────────────┐
│   Telegram   │ ───────────────▶ │  server/ (FastAPI + Telethon)       │
│ grupos/canais│                  │  listener → matcher → LLM → alerta  │
└──────────────┘                  │  SQLite + REST API (porta 3333)     │
       ▲                          └─────────────────────────────────────┘
       │ alerta via bot                         ▲
       │ (DM)                                   │ REST
       │                          ┌─────────────────────────────────────┐
       └───────────────────────  │  web/ (React + Vite, porta 3000)    │
                                  │  painel: interesses, matches, etc.  │
                                  └─────────────────────────────────────┘
```

## Como funciona

1. Uma sessão de **usuário** do Telegram (Telethon) escuta, em tempo real, as mensagens dos grupos/canais que você já participa.
2. Cada mensagem é persistida e pontuada pelo **matcher** contra seus interesses: palavras-chave (keyword) + similaridade textual (fuzzy via rapidfuzz), com veto por palavras excluídas e extração de preço por regex. Score ≥ `0.6` é candidato a match.
3. Opcionalmente, cada candidato passa por uma **validação via LLM** (LangChain + OpenRouter) que confirma se a mensagem é mesmo a promoção buscada. É *fail-open*: sem chave/erro/timeout, o candidato é aprovado.
4. Match aprovado é gravado e dispara um **alerta na sua DM** via um segundo client Telethon logado como bot (`@BotFather`) — com produto, preço, trecho do texto e link para a mensagem original.

## Componentes

| Pasta | O que é | Stack | Porta |
|-------|---------|-------|-------|
| [`server/`](server/README.md) | API + worker do Telegram | Python 3.12, FastAPI, Telethon, SQLAlchemy/SQLite, rapidfuzz | 3333 |
| [`web/`](web/README.md) | Painel de gerenciamento | React 19, Vite, TanStack Router/Query, Tailwind v4, shadcn/ui | 3000 |

## Quickstart

Você precisa das credenciais da API do Telegram (`my.telegram.org/apps`) e, para receber os alertas, de um bot criado no `@BotFather`.

**Backend** (porta 3333):
```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
cp .env.example .env      # preencha TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, TELEGRAM_BOT_TOKEN
pip install -r requirements.txt
python3 run.py            # lê API_HOST/API_PORT do .env
```
Na **primeira execução** o processo bloqueia em `input()` pedindo o código de verificação enviado ao Telegram. Depois a sessão é salva e reutilizada. Mande `/start` no seu bot para registrar o chat de destino dos alertas.

**Frontend** (porta 3000):
```bash
cd web
pnpm install
pnpm dev
```
O painel consome a API em `http://localhost:3333` (o backend libera CORS apenas para `http://localhost:3000`).

**Docker** (backend):
```bash
cd server && docker compose up --build
```
Para o login na primeira execução: `docker attach telegram-promobot` e digite o código.

## Documentação

- [`server/README.md`](server/README.md) — setup detalhado, variáveis de ambiente, endpoints da API, fluxo de dados e estrutura do banco.
- [`web/README.md`](web/README.md) — estrutura do frontend, rotas e scripts.
- [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) — notas de arquitetura para agentes/contribuidores.

## Licença

MIT
