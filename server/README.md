# Telegram Promo Monitor — Server

Backend do [Promo Monitor](../README.md): API REST + worker do Telegram. Para o painel web, veja [`web/`](../web/README.md).

Sistema de monitoramento de promoções no Telegram via MTProto. Escuta mensagens de grupos/canais em tempo real, faz matching com seus interesses e te notifica via **bot do Telegram** na sua DM (produto, preço, texto e link para a mensagem original).

## Funcionalidades

- Login no Telegram via MTProto (Telethon) com persistência de sessão
- Monitoramento de mensagens em tempo real de grupos/canais que você já participa
- Sistema de interesses configuráveis (produto, preço máximo, palavras-chave, exclusões)
- Matching com fuzzy search (rapidfuzz) + extração de preços via regex
- Ao encontrar um match, envia uma notificação via **bot do Telegram** (configure `TELEGRAM_BOT_TOKEN`, criado no @BotFather) para a sua DM — com produto, preço, trecho do texto e link para a mensagem original. Como a mensagem vem do bot, você recebe o push normalmente (o forward pela própria conta não notificava). Mande `/start` no bot para registrar o chat automaticamente (`alert_target`). Sem token ou sem destino configurado, nada é enviado
- API REST para gerenciar interesses, configurações e consultar matches
- SQLite com SQLAlchemy (pronto para migrar para PostgreSQL)

## Stack

- Python 3.12+ | Telethon | FastAPI | SQLAlchemy | Pydantic | SQLite | rapidfuzz

## Como obter API_ID e API_HASH

1. Acesse https://my.telegram.org/apps
2. Faça login com sua conta Telegram
3. Crie uma nova aplicação (qualquer nome, ex: "promo-monitor")
4. Copie `api_id` e `api_hash`

## Setup

### 1. Clone e ambiente

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
source .venv/bin/activate.fish  # Linux/Mac -> fish shell
# .venv\Scripts\activate   # Windows
```

### 2. Configure o .env

```bash
cp .env.example .env
# Edite .env com suas credenciais
```

Variáveis de ambiente:

| Variável | Obrigatória | Default | Descrição |
|----------|-------------|---------|-----------|
| `TELEGRAM_API_ID` | sim | — | API ID obtido em my.telegram.org/apps |
| `TELEGRAM_API_HASH` | sim | — | API hash obtido em my.telegram.org/apps |
| `TELEGRAM_PHONE` | sim | — | Telefone da conta que escuta os grupos (com DDI) |
| `TELEGRAM_BOT_TOKEN` | não* | vazio | Token do bot (@BotFather). **Só semeia o valor inicial** — depois da primeira subida o token vive no banco (`app_config`) e é editado em Configurações no painel, valendo na hora |
| `MATCH_SCORE_THRESHOLD` | não | `0.6` | Score mínimo (0–1) para considerar match |
| `OPENROUTER_API_KEY` | não | vazio | Ativa a validação por LLM. Sem ela, só o matcher decide |
| `LLM_MODEL` | não | `openrouter/free` | ID do modelo no OpenRouter (aceita variantes `:free`) |
| `API_HOST` / `API_PORT` | não | `0.0.0.0` / `3333` | Host/porta do servidor (lidos por `run.py`) |
| `DATABASE_URL` | não | `sqlite:///data/promobot.db` | URL do banco SQLAlchemy |
| `DEBUG` / `LOG_LEVEL` | não | `false` / `INFO` | Flags de depuração e nível de log |

\* Sem `TELEGRAM_BOT_TOKEN` a aplicação funciona (captura e registra matches), mas não envia alertas.

### 3. Instale dependências

```bash
pip install -r requirements.txt
```

### 4. Execute

```bash
python3 run.py
```

O `run.py` lê `API_HOST`/`API_PORT` do `.env` (porta padrão **3333**) e já sobe com `--reload`.

> O CLI do uvicorn **não** lê o `.env`: `uvicorn app.main:app --reload` sobe na porta padrão `8000`. Se preferir usar o CLI, informe a porta na mão: `uvicorn app.main:app --reload --port 3333`.

Na primeira execução não há sessão salva: o backend registra `telegram_login_required` e
segue servindo HTTP normalmente. O login é feito pelo painel (`/login` → **Enviar código**),
que fala com `POST /telegram/auth/request-code` e `/code`. Após autenticar, a sessão é
salva e reutilizada automaticamente, e o pipeline de captura sobe sozinho.

> Com `--reload`, salvar um arquivo `.py` reinicia o processo — e isso reinicia o worker do Telegram junto (ele sobe no `lifespan`). A sessão já está salva, então não pede o código de novo, mas há uma breve reconexão a cada reload.

### Docker

```bash
docker compose up --build
```

> O `docker-compose.yml` fica na **raiz** do repositório e o container do backend se chama
> `promo-monitor-backend`. Não é mais preciso `stdin_open`/`tty` nem `docker attach`: o
> código de verificação é digitado no painel web.

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Status: `telegram_connected`, `telegram_authenticated`, `worker_running`, `bot_connected` |
| GET | `/telegram/auth/status` | Estado do login (telefone mascarado, etapa atual, erro) |
| POST | `/telegram/auth/request-code` | Envia o código para `TELEGRAM_PHONE` |
| POST | `/telegram/auth/code` | Envia o código digitado (`{code}`) |
| POST | `/telegram/auth/password` | Senha de duas etapas (`{password}`) |
| POST | `/telegram/auth/logout` | Encerra a sessão e para a captura |
| GET | `/interests` | Listar interesses |
| POST | `/interests` | Criar interesse |
| GET | `/interests/{id}` | Obter interesse |
| PUT | `/interests/{id}` | Atualizar interesse |
| DELETE | `/interests/{id}` | Remover interesse |
| GET | `/matches` | Listar matches |
| GET | `/messages` | Listar mensagens |
| GET | `/settings` | Destino dos alertas (read-only) + estado do bot (token mascarado, nunca cru) |
| PUT | `/settings` | Atualização **parcial** do `telegram_bot_token` |
| POST | `/settings/alert/test` | Manda uma mensagem de teste para o destino configurado |

### Exemplos de requests

```bash
# Criar interesse
curl -X POST http://localhost:3333/interests \
  -H "Content-Type: application/json" \
  -d '{
    "nome_produto": "iphone 15 pro",
    "preco_maximo": 4500,
    "palavras_chave": ["iphone 15 pro", "iphone15pro", "apple iphone"],
    "palavras_excluidas": ["usado", "quebrado"]
  }'

# Listar interesses ativos
curl "http://localhost:3333/interests?ativo=true"

# Listar matches
curl "http://localhost:3333/matches?limit=10"

# Trocar o token do bot (vale na hora, sem restart). O destino dos alertas não
# é editável por aqui: mande /start ao bot pelo Telegram.
curl -X PUT http://localhost:3333/settings \
  -H "Content-Type: application/json" \
  -d '{"telegram_bot_token": "123456789:AAE...xyz"}'

# Health check
curl http://localhost:3333/health
```

## Arquitetura

```
app/
├── api/routes/       # Endpoints REST (health, interests, matches, messages, settings)
├── core/             # Config, logging, exceptions
├── database/         # SQLAlchemy engine, session, declarative base
├── models/           # ORM models (TelegramMessage, ProductInterest, PromotionMatch, AppConfig)
├── repositories/     # Repository pattern (base + específicos)
├── schemas/          # Pydantic schemas (request/response)
├── services/         # Business logic (interest, matcher, alert, message, app_config)
├── telegram/         # Telethon client, auth, listener
└── workers/          # Background worker (telegram_worker)
```

### Fluxo de dados

```
Telegram MTProto → listener.py → message_service.py (normalização)
                                      ↓
                               matcher_service.py (keyword + fuzzy + preço)
                                      ↓
                               llm_validator_service.py (validação opcional via LLM)
                                      ↓
                               alert_service.py → notifica via bot (app_config)
                                      ↓
                               Database SQLite
                                      ↓
                               FastAPI → REST API
```

O matcher é um filtro barato e abrangente; quando `OPENROUTER_API_KEY` está
configurada, cada candidato aprovado passa por uma **validação via LLM** (LangChain
+ OpenRouter, modelo em `LLM_MODEL`) que confirma se a mensagem é mesmo a promoção
do produto buscado. Se a LLM reprovar, o match **não** é criado nem alertado (fica
só no log como `llm_rejected`). É *fail-open*: sem a key, desabilitado, ou em
erro/timeout, o candidato é aprovado normalmente (nenhuma promo real é perdida por
falha transitória).

A notificação é enviada por um **segundo client Telethon logado como bot** (token em `app_config.telegram_bot_token`, semeado a partir de `TELEGRAM_BOT_TOKEN`), separado da conta de usuário que escuta os grupos. Trocar o token pelo painel derruba e sobe o client na hora — o `bot.session` é apagado nessa troca, senão o Telethon reaproveitaria a sessão do bot anterior e o token novo seria ignorado em silêncio. Os dois clients rodam no mesmo event loop dentro do processo FastAPI. O bot também responde `/start` (registra o chat em `alert_target`) e `/id`. **O `/start` é a única forma de definir o destino** — o painel só mostra o estado, nunca escreve o campo. Isso garante que o destino é sempre um chat onde o bot consegue escrever (escolher um grupo à mão do qual o bot não é membro só produzia erro no envio). O destino é lido do banco no momento do envio, então um `/start` novo vale na hora. Se estiver vazio, ou sem `TELEGRAM_BOT_TOKEN`, **nada é enviado**.

### Matching

O sistema usa duas estratégias combinadas:
1. **Keyword**: verifica se palavras-chave estão presentes no texto
2. **Fuzzy**: similaridade textual via rapidfuzz (partial_ratio)

Score final = máximo entre as estratégias. Se score >= threshold (0.6), é considerado match.

Extração de preços via regex: `R$ 1.234,56`, `1.234,56 reais`, etc.

### Preparado para futuro

- Estratégias de matching via interface (`MatchStrategy`) — fácil adicionar OpenAI, embeddings, etc.
- AlertService desacoplado — pronto para email, webhook, etc.
- Repository pattern — trocar SQLite por PostgreSQL sem alterar services

## Estrutura do banco

- **telegram_messages**: mensagens capturadas
- **product_interests**: seus interesses/produtos
- **promotion_matches**: matches encontrados
- **app_config**: configurações da aplicação (destino dos alertas)

## Licença

MIT
