export interface SettingsResponse {
  alert_target: string | null
  updated_at: string
  telegram_bot_token_set: boolean
  telegram_bot_token_masked: string | null
  bot_connected: boolean
  bot_username: string | null
  bot_last_error: string | null
}

export type SettingsUpdate = Partial<{
  telegram_bot_token: string | null
}>

export interface AlertTestResponse {
  ok: boolean
  error: string | null
}
