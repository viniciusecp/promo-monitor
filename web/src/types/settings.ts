export interface SettingsResponse {
  alert_target: string | null
  updated_at: string
}

export interface SettingsUpdate {
  alert_target: string | null
}
