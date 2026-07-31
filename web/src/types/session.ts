export type Papel = 'owner' | 'viewer'

export interface SessionUser {
  id: number
  email: string
  nome: string
  papel: Papel
  ativo: boolean
  trocar_senha: boolean
  ultimo_login: string | null
  created_at: string
}

export interface SessionResponse {
  user: SessionUser
}

export interface LoginRequest {
  email: string
  senha: string
}

export interface ChangePasswordRequest {
  senha_atual: string
  senha_nova: string
}
