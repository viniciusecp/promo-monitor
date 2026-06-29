export interface InterestResponse {
  id: number
  nome_produto: string
  preco_maximo: number | null
  limiar_match: number | null
  palavras_chave: string[]
  palavras_excluidas: string[]
  ativo: boolean
  created_at: string
  updated_at: string
}

export interface InterestCreate {
  nome_produto: string
  preco_maximo?: number | null
  limiar_match?: number | null
  palavras_chave?: string[]
  palavras_excluidas?: string[]
  ativo?: boolean
}

export interface InterestUpdate {
  nome_produto?: string
  preco_maximo?: number | null
  limiar_match?: number | null
  palavras_chave?: string[]
  palavras_excluidas?: string[]
  ativo?: boolean
}
