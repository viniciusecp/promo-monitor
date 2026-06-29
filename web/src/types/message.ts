export interface MessageResponse {
  id: number
  message_id: number
  chat_id: number
  chat_name: string | null
  sender_id: number | null
  sender_name: string | null
  text: string | null
  links: string[] | null
  raw_date: string | null
  created_at: string
}

export interface MessageFilters {
  chat_id?: number
  skip?: number
  limit?: number
}
