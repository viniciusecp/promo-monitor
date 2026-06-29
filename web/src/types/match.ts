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
  alerted: boolean
  alerted_at: string | null
  created_at: string
  chat_name: string | null
  message_text: string | null
  message_link: string | null
  produto_nome: string
}

export interface MatchFilters {
  interest_id?: number
  alerted?: boolean
  skip?: number
  limit?: number
}
