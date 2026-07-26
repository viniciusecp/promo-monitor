export type TelegramAuthStatus =
  | 'connecting'
  | 'unauthenticated'
  | 'awaiting_code'
  | 'awaiting_password'
  | 'authenticated'
  | 'error'

export interface AuthUser {
  id: number
  first_name: string | null
  username: string | null
}

export interface AuthStatusResponse {
  status: TelegramAuthStatus
  connected: boolean
  phone_masked: string
  worker_running: boolean
  user: AuthUser | null
  error_code: string | null
  error_message: string | null
  retry_after_seconds: number | null
  code_sent_at: string | null
  can_request_code: boolean
}
