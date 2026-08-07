export interface HealthResponse {
  status: string
  telegram_connected: boolean
  telegram_authenticated: boolean
  worker_running: boolean
  capture_active: boolean
  interests_count: number
  bot_connected: boolean
  uptime_seconds: number
}
