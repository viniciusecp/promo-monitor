export interface HealthResponse {
  status: string
  telegram_connected: boolean
  telegram_authenticated: boolean
  worker_running: boolean
  bot_connected: boolean
  uptime_seconds: number
}
