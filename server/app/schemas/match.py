from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MatchResponse(BaseModel):
    id: int
    message_id: int
    interest_id: int
    preco_encontrado: float | None
    score: float
    raw_text_snippet: str | None
    matched_keyword: str | None
    llm_motivo: str | None
    llm_aprovado: bool
    llm_validado: bool
    preco_ok: bool
    alerted: bool
    alerted_at: datetime | None
    lido: bool
    lido_em: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchDetailResponse(MatchResponse):
    chat_name: str | None
    message_text: str | None
    message_link: str | None
    produto_nome: str


class MatchReadResponse(BaseModel):
    id: int
    lido: bool
    lido_em: datetime | None


class MatchBulkReadResponse(BaseModel):
    updated: int


class MatchPeriod(str, Enum):
    hoje = "hoje"
    d7 = "7d"
    d30 = "30d"
    tudo = "tudo"


class MatchStatus(str, Enum):
    alertado = "alertado"
    reprovado = "reprovado"


class MatchOrderBy(str, Enum):
    data = "data"
    preco = "preco"
    score = "score"


class MatchOrderDir(str, Enum):
    asc = "asc"
    desc = "desc"


class MatchFilterParams(BaseModel):
    """Filtros do feed de matches.

    Usado nos dois lados: como query-param model no `GET /matches` e como body
    do `POST /matches/read-all`. Um schema só é o que garante que "marcar todos
    como lidos" opere exatamente sobre o que está na tela.

    Sobre `status`: `nao_lidos` é o eixo de leitura e faz AND. `alertado` e
    `reprovado` são o eixo de resultado e fazem OR **entre si** — se todos
    fizessem AND, "alertado + reprovado" nunca retornaria nada, já que um match
    reprovado pela IA jamais é alertado.
    """

    periodo: MatchPeriod = MatchPeriod.tudo
    tz: str | None = None
    nao_lidos: bool = False
    status: list[MatchStatus] = Field(default_factory=list)
    chat_id: int | None = None
    preco_min: float | None = Field(None, ge=0)
    preco_max: float | None = Field(None, ge=0)
    order_by: MatchOrderBy = MatchOrderBy.data
    order_dir: MatchOrderDir = MatchOrderDir.desc


class MatchListQuery(MatchFilterParams):
    """Filtros + paginação para o `GET /matches`.

    Existe separado porque o FastAPI não aceita um query-param model convivendo
    com parâmetros `Query()` avulsos na mesma assinatura — ou tudo entra no
    modelo, ou a expansão do modelo não acontece. Herdar mantém o body do
    `read-all` (que é `MatchFilterParams`) sem campos de paginação.
    """

    skip: int = Field(0, ge=0)
    limit: int = Field(30, ge=1, le=200)


class MatchListResponse(BaseModel):
    items: list[MatchDetailResponse]
    total: int
    has_more: bool


class MatchStatsResponse(BaseModel):
    nao_lidos: int
    novos_hoje: int
    ultimas_24h: int
    ultimos_7d: int
    interesses_ativos: int


class MatchChatResponse(BaseModel):
    chat_id: int
    chat_name: str | None
    total: int
