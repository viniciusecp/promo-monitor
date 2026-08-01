# Promo Monitor

Monitor de promoções no Telegram. O backend entra nos seus grupos/canais via uma sessão de usuário do Telegram (Telethon), pontua cada mensagem recebida contra "interesses" de produto que você define, registra os matches e te notifica na DM através de um **bot do Telegram**. O frontend é um painel para gerenciar interesses e navegar pelas mensagens/matches.

```
┌──────────────┐    mensagens     ┌─────────────────────────────────────┐
│   Telegram   │ ───────────────▶ │  server/ (FastAPI + Telethon)       │
│ grupos/canais│                  │  listener → matcher → LLM → alerta  │
└──────────────┘                  │  SQLite + REST API (porta 4999)     │
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
| [`server/`](server/README.md) | API + worker do Telegram | Python 3.12, FastAPI, Telethon, SQLAlchemy/SQLite, rapidfuzz | 4999 |
| [`web/`](web/README.md) | Painel de gerenciamento | React 19, Vite, TanStack Router/Query, Tailwind v4, shadcn/ui | 3000 |

## Quickstart

Você precisa das credenciais da API do Telegram (`my.telegram.org/apps`) e, para receber os alertas, de um bot criado no `@BotFather`.

**Backend** (porta 4999):
```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
cp .env.example .env      # preencha TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
pip install -r requirements.txt
python3 run.py            # lê API_PORT do .env
```
Na **primeira execução** o backend sobe sem sessão e fica aguardando: abra o painel,
você cai na tela de login, clique em **Enviar código** e digite ali mesmo o código que
o Telegram mandou (mais a senha de duas etapas, se você usar). Depois a sessão é salva
e reutilizada. O token do bot é colado em **Configurações** no painel, e mandar `/start`
para ele registra o chat de destino dos alertas sem recarregar a página.

**Frontend** (porta 3000):
```bash
cd web
pnpm install
pnpm dev
```
O painel chama a API em `/api`, que o proxy de dev do Vite encaminha para
`http://localhost:4999`. Mesma origem em dev e em produção — é o que faz o cookie de
sessão funcionar nos dois modos sem CORS.

Antes do primeiro acesso, defina `AUTH_SEED_EMAIL` e `AUTH_SEED_PASSWORD` no
`server/.env`: é assim que o primeiro administrador entra no banco (ver
[Autenticação](#autenticação)).

**Docker** (backend + frontend, em uma única stack): suba tudo com `docker compose up --build` na raiz — veja o passo a passo em [Deploy em produção (Docker)](#deploy-em-produção-docker).

## Deploy em produção (Docker)

A raiz do projeto tem um `docker-compose.yml` que sobe a aplicação inteira em dois serviços:

| Serviço | Container | Imagem | Porta no host |
|---------|-----------|--------|---------------|
| `web` | `promo-monitor-web` | SPA buildada + proxy da API (nginx) | `WEB_PORT` (5000) |
| `backend` | `promo-monitor-server` | FastAPI/Telethon (uvicorn) | *nenhuma* (rede interna) |

**Uma origem só.** O nginx do `web` serve o painel e encaminha `/api/*` para o backend, que
não publica porta nenhuma no host. Isso mantém o login do Telegram e as configurações fora do
alcance direto da internet, e faz o cookie de sessão dispensar CORS. Como consequência, não
existe mais `VITE_API_URL`: trocar o IP ou o domínio de acesso **não** exige rebuildar imagem.

### 1. Pré-requisitos no servidor
- **Docker** e **Docker Compose** instalados.
- Credenciais da API do Telegram (`my.telegram.org/apps`) e um bot do `@BotFather`.
- A porta `WEB_PORT` liberada no firewall. O backend não precisa de porta aberta.

### 2. Clonar e configurar variáveis
```bash
git clone <repo> promo-monitor && cd promo-monitor

# Variáveis de orquestração (só a porta publicada)
cp .env.example .env

# Segredos do backend (Telegram, bot, OpenRouter, primeiro administrador)
cp server/.env.example server/.env
```
Edite o **`.env` da raiz**:
```ini
WEB_PORT=5000     # única porta publicada; use 80 para servir na porta web padrão
```
Edite o **`server/.env`** com `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`,
(opcional) `OPENROUTER_API_KEY` e o **primeiro administrador**:
```ini
AUTH_SEED_EMAIL=voce@exemplo.com
AUTH_SEED_PASSWORD=uma-senha-longa-e-provisoria
```
> ⚠️ Sem esse par, a primeira subida cria o banco **sem nenhum usuário** e ninguém consegue
> entrar (não existe cadastro aberto). O backend avisa com `auth_no_users` no log. O seed só
> roda quando a tabela de usuários está vazia; depois disso, quem manda é o banco.

### 3. Subir a stack
```bash
docker compose up --build -d
```

### 4. Primeiro acesso
Abra o painel em `http://SEU_SERVIDOR:${WEB_PORT}` e entre com o e-mail e a senha do
`AUTH_SEED_*`. O painel **obriga a trocar a senha** na primeira entrada — ela veio de um
arquivo em disco e não deve virar credencial permanente.

Em seguida você cai na tela **Conectar o Telegram**: clique em **Enviar código**, digite o
código que chegou no app do Telegram (e a senha de duas etapas, se você usar) e a captura
começa sozinha. Nada de `docker attach`. A sessão fica salva no volume (`server/session/`);
as próximas subidas não pedem código.

Por fim, cole o token do bot em **Configurações** e mande **`/start`** para ele no Telegram
para registrar o chat dos alertas.

### 5. Acessar e operar
- Painel: `http://SEU_SERVIDOR:${WEB_PORT}` (a API fica sob `/api` na mesma origem)
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

## Autenticação

O painel exige login. **Não existe cadastro aberto**: só entra quem já está na lista de
usuários, e essa lista só é editada por um administrador.

### Papéis
| Papel | Pode |
|-------|------|
| `owner` (admin) | Tudo: feed, interesses, **usuários**, configurações e conexão do Telegram |
| `viewer` (leitura) | Feed de promoções e interesses |

A separação é o que protege o ativo mais sensível do projeto: as rotas `/telegram/auth/*`
pedem código de login e recebem a senha de duas etapas da **conta pessoal** do dono, e a
sessão Telethon em `server/session/` equivale a essa conta.

### Como a sessão funciona
- **Sessão opaca em cookie**, não JWT. O cookie (`pm_session`) é `HttpOnly` — JavaScript não
  alcança o token — e o banco guarda só o SHA-256 dele.
- **Login persistente.** O cookie tem `Max-Age` de `AUTH_SESSION_DAYS` (30 por padrão) e é
  renovado a cada uso, então fechar o navegador não desloga: quem abre o painel ao menos uma
  vez por mês nunca refaz login.
- **Revogação imediata.** Desativar, excluir ou trocar o papel de alguém derruba as sessões
  abertas dessa pessoa na hora — é a vantagem concreta da sessão sobre um JWT, que só expira.
- **Senhas com Argon2id** (`pwdlib`), e rate limit progressivo por (e-mail, IP) no login.
- O último administrador ativo não pode ser rebaixado, desativado nem excluído — senão o
  painel ficaria sem ninguém capaz de administrá-lo, e não há auto-cadastro para recuperar.

### Gerenciar usuários
**Configurações → Usuários** (visível só para admin): criar acesso com senha provisória,
alternar leitura/admin, desativar, redefinir senha e remover. Quem recebe uma senha definida
por outra pessoa é obrigado a trocá-la ao entrar.

### ⚠️ TLS / HTTPS
Os containers servem **HTTP puro**, e a stack é operada assim de propósito. Saiba o que isso
significa: **a senha digitada no login e o cookie de sessão trafegam em texto claro** e podem
ser lidos por qualquer intermediário no caminho (provedor, Wi-Fi compartilhado, roteador
comprometido). Quem copiar o cookie entra sem precisar da senha.

A autenticação aqui protege contra **quem só conhece a URL**, não contra quem observa a rede.

Para fechar essa lacuna, coloque a stack atrás de um proxy TLS (Caddy, Traefik, nginx ou
Cloudflare) apontando para `WEB_PORT` e, no `server/.env`, troque:
```ini
AUTH_COOKIE_SECURE=true
```
É a única mudança necessária do lado da aplicação — o resto já está pronto. Não ligue essa
flag antes de ter HTTPS: um cookie `Secure` não é enviado por HTTP e ninguém consegue entrar.

> ℹ️ O backend roda como **um único processo uvicorn** de propósito: o worker do Telegram
> compartilha o event loop do FastAPI, então rodar múltiplos workers duplicaria o listener.

## Documentação

- [`server/README.md`](server/README.md) — setup detalhado, variáveis de ambiente, endpoints da API, fluxo de dados e estrutura do banco.
- [`web/README.md`](web/README.md) — estrutura do frontend, rotas e scripts.
- [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) — notas de arquitetura para agentes/contribuidores.

## Licença

MIT
