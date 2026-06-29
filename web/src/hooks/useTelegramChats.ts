import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { TelegramChat } from '@/types'

export function useTelegramChats() {
  return useQuery({
    queryKey: ['telegram', 'chats'],
    queryFn: () => api.get<TelegramChat[]>('/telegram/chats'),
  })
}
