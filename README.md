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
O painel consome a API em `http://localhost:3333` (o backend libera CORS para qualquer origem).

**Docker** (backend + frontend, em uma única stack): suba tudo com `docker compose up --build` na raiz — veja o passo a passo em [Deploy em produção (Docker)](#deploy-em-produção-docker).

## Deploy em produção (Docker)

A raiz do projeto tem um `docker-compose.yml` que sobe a aplicação inteira em dois serviços:

| Serviço | Container | Imagem | Porta no host |
|---------|-----------|--------|---------------|
| `backend` | `promo-monitor-backend` | FastAPI/Telethon (uvicorn) | `API_PORT` (3333) |
| `web` | `promo-monitor-web` | SPA buildada servida por nginx | `WEB_PORT` (8080) |

O navegador acessa o painel em `web` e chama a API do `backend` diretamente — por isso a URL
pública do backend é embutida no build do frontend (`VITE_API_URL`).

### 1. Pré-requisitos no servidor
- **Docker** e **Docker Compose** instalados.
- Credenciais da API do Telegram (`my.telegram.org/apps`) e um bot do `@BotFather`.
- As portas `API_PORT` e `WEB_PORT` liberadas no firewall (ou atrás do seu proxy — veja TLS).

### 2. Clonar e configurar variáveis
```bash
git clone <repo> promo-monitor && cd promo-monitor

# Variáveis de orquestração (portas + URL pública do backend embutida no build)
cp .env.example .env

# Segredos do backend (Telegram, bot, OpenRouter)
cp server/.env.example server/.env
```
Edite o **`.env` da raiz**:
```ini
# URL pública pela qual o NAVEGADOR alcança o backend (vai embutida no build do frontend!)
VITE_API_URL=https://api.seudominio.com      # ou http://SEU_IP_PUBLICO:3333
API_PORT=3333
WEB_PORT=8080                                 # use 80 para servir o painel direto na porta web padrão
```
Edite o **`server/.env`** com `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`,
`TELEGRAM_BOT_TOKEN` e (opcional) `OPENROUTER_API_KEY`.

> ⚠️ **`VITE_API_URL` é resolvido em tempo de build**, não em runtime. Se você mudar o
> domínio/IP público do backend depois, é preciso **rebuildar a imagem `web`**
> (`docker compose build web` ou `docker compose up --build -d`).

### 3. Subir a stack
```bash
docker compose up --build -d
```

### 4. Login do Telegram (apenas na 1ª vez)
O backend bloqueia pedindo o código de verificação. Anexe ao container, digite o código e
**solte o terminal sem matar o container** com `Ctrl-P` `Ctrl-Q`:
```bash
docker attach promo-monitor-backend
```
A sessão fica salva no volume (`server/session/`); as próximas subidas não pedem código.
Depois, mande **`/start`** para o seu bot no Telegram para registrar o chat dos alertas.

### 5. Acessar e operar
- Painel: `http://SEU_SERVIDOR:${WEB_PORT}` · API: `http://SEU_SERVIDOR:${API_PORT}`
```bash
docker compose ps                 # status (o backend deve ficar "healthy")
docker compose logs -f backend    # acompanhar logs
docker compose down               # parar a stack (mantém os volumes)
docker compose up --build -d      # aplicar atualizações de código
```

### Persistência
Os dados ficam em **bind mounts** no host e sobrevivem a `down`/rebuild:
- `server/data/` — banco SQLite (`promobot.db`).
- `server/session/` — sessões do Telethon (usuário + bot).

### TLS / HTTPS
Os containers servem **HTTP puro**. Em produção, coloque-os atrás de um proxy com TLS
(Cloudflare, ou um nginx/Traefik/Caddy no host) terminando HTTPS e encaminhando para
`WEB_PORT` (painel) e `API_PORT` (API). Lembre que `VITE_API_URL` deve apontar para a URL
**pública final** do backend (ex.: `https://api.seudominio.com`).

> ℹ️ O backend roda como **um único processo uvicorn** de propósito: o worker do Telegram
> compartilha o event loop do FastAPI, então rodar múltiplos workers duplicaria o listener.

## Documentação

- [`server/README.md`](server/README.md) — setup detalhado, variáveis de ambiente, endpoints da API, fluxo de dados e estrutura do banco.
- [`web/README.md`](web/README.md) — estrutura do frontend, rotas e scripts.
- [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) — notas de arquitetura para agentes/contribuidores.

## Licença

MIT
