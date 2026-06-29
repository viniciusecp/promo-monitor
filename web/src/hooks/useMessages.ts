import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { MessageResponse, MessageFilters } from '@/types'

export function useMessages(filters: MessageFilters = {}) {
  const params = new URLSearchParams()
  if (filters.chat_id !== undefined) params.set('chat_id', String(filters.chat_id))
  if (filters.skip !== undefined) params.set('skip', String(filters.skip))
  if (filters.limit !== undefined) params.set('limit', String(filters.limit))
  const qs = params.toString()

  return useQuery({
    queryKey: ['messages', filters],
    queryFn: () =>
      api.get<MessageResponse[]>(`/messages${qs ? `?${qs}` : ''}`),
  })
}
