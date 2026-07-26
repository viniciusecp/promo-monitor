export interface MatchDetailResponse {
  id: number
  message_id: number
  interest_id: number
  preco_encontrado: number | null
  score: number
  raw_text_snippet: string | null
  matched_keyword: string | null
  llm_motivo: string | null
  llm_aprovado: boolean
  llm_validado: boolean
  preco_ok: boolean
  alerted: boolean
  alerted_at: string | null
  lido: boolean
  lido_em: string | null
  created_at: string
  chat_name: string | null
  message_text: string | null
  message_link: string | null
  produto_nome: string
}

export type MatchPeriod = 'hoje' | '7d' | '30d' | 'tudo'
export type MatchStatus = 'alertado' | 'reprovado'
export type MatchOrderBy = 'data' | 'preco' | 'score'
export type MatchOrderDir = 'asc' | 'desc'

/**
 * Filtros do feed. `nao_lidos` combina em AND com o resto; `alertado` e
 * `reprovado` combinam em OR entre si (ver o schema equivalente no backend).
 */
export interface MatchFilters {
  periodo: MatchPeriod
  status: MatchStatus[]
  nao_lidos: boolean
  chat_id?: number
  preco_min?: number
  preco_max?: number
  order_by: MatchOrderBy
  order_dir: MatchOrderDir
}

export const DEFAULT_MATCH_FILTERS: MatchFilters = {
  periodo: '7d',
  status: [],
  nao_lidos: false,
  order_by: 'data',
  order_dir: 'desc',
}

export interface MatchListResponse {
  items: MatchDetailResponse[]
  total: number
  has_more: boolean
}

export interface MatchStatsResponse {
  nao_lidos: number
  novos_hoje: number
  ultimas_24h: number
  ultimos_7d: number
  interesses_ativos: number
}

export interface MatchChatResponse {
  chat_id: number
  chat_name: string | null
  total: number
}

export interface MatchReadResponse {
  id: number
  lido: boolean
  lido_em: string | null
}
