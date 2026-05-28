# Telegram Promo Monitor

Sistema de monitoramento de promoções no Telegram via MTProto. Escuta mensagens de grupos/canais em tempo real, faz matching com seus interesses e envia alertas para Saved Messages.

## Funcionalidades

- Login no Telegram via MTProto (Telethon) com persistência de sessão
- Monitoramento de mensagens em tempo real de grupos/canais que você já participa
- Sistema de interesses configuráveis (produto, preço máximo, palavras-chave, exclusões)
- Matching com fuzzy search (rapidfuzz) + extração de preços via regex
- Alertas enviados para Saved Messages do Telegram
- API REST para gerenciar interesses e consultar matches
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

### 3. Instale dependências

```bash
pip install -r requirements.txt
```

### 4. Execute

```bash
uvicorn app.main:app --reload
```

Na primeira execução, o sistema pedirá o código de verificação enviado ao Telegram. Após autenticar, a sessão é salva e reutilizada automaticamente.

### Docker

```bash
docker compose up --build
```

> **Importante no Docker:** O login interativo (código do Telegram) requer `stdin_open: true` e `tty: true` no docker-compose. Conecte no container com `docker attach telegram-promobot` para digitar o código na primeira execução.

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Status da aplicação |
| GET | `/interests` | Listar interesses |
| POST | `/interests` | Criar interesse |
| GET | `/interests/{id}` | Obter interesse |
| PUT | `/interests/{id}` | Atualizar interesse |
| DELETE | `/interests/{id}` | Remover interesse |
| GET | `/matches` | Listar matches |
| GET | `/messages` | Listar mensagens |

### Exemplos de requests

```bash
# Criar interesse
curl -X POST http://localhost:8000/interests \
  -H "Content-Type: application/json" \
  -d '{
    "nome_produto": "iphone 15 pro",
    "preco_maximo": 4500,
    "palavras_chave": ["iphone 15 pro", "iphone15pro", "apple iphone"],
    "palavras_excluidas": ["usado", "quebrado"]
  }'

# Listar interesses ativos
curl "http://localhost:8000/interests?ativo=true"

# Listar matches
curl "http://localhost:8000/matches?limit=10"

# Health check
curl http://localhost:8000/health
```

## Arquitetura

```
app/
├── api/routes/       # Endpoints REST (health, interests, matches, messages)
├── core/             # Config, logging, exceptions
├── database/         # SQLAlchemy engine, session, declarative base
├── models/           # ORM models (TelegramMessage, ProductInterest, PromotionMatch)
├── repositories/     # Repository pattern (base + específicos)
├── schemas/          # Pydantic schemas (request/response)
├── services/         # Business logic (interest, matcher, alert, message)
├── telegram/         # Telethon client, auth, listener
└── workers/          # Background worker (telegram_worker)
```

### Fluxo de dados

```
Telegram MTProto → listener.py → message_service.py (normalização)
                                      ↓
                               matcher_service.py (keyword + fuzzy + preço)
                                      ↓
                               alert_service.py → Saved Messages
                                      ↓
                               Database SQLite
                                      ↓
                               FastAPI → REST API
```

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

## Licença

MIT
