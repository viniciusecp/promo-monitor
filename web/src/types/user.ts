import type { Papel, SessionUser } from './session'

export type UserResponse = SessionUser

export interface UserCreate {
  email: string
  nome: string
  papel: Papel
  senha: string
}

export interface UserUpdate {
  nome?: string
  papel?: Papel
  ativo?: boolean
}

export interface UserPasswordReset {
  senha: string
}
