export interface SettingsResponse {
  alert_target: string | null
  updated_at: string
  telegram_bot_token_set: boolean
  telegram_bot_token_masked: string | null
  bot_connected: boolean
  bot_username: string | null
  bot_last_error: string | null
}

/** Só o token é editável pelo painel — `alert_target` é de leitura, gravado
 *  exclusivamente pelo handler `/start` do bot. Parcial de propósito: o backend
 *  usa `exclude_unset`, então omitir significa "não mexe" e `null` significa
 *  "limpa". */
export type SettingsUpdate = Partial<{
  telegram_bot_token: string | null
}>

export interface AlertTestResponse {
  ok: boolean
  error: string | null
}
