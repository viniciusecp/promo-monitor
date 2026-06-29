import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { HealthResponse } from '@/types'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<HealthResponse>('/health'),
    refetchInterval: 15_000,
  })
}
