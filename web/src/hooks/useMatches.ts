import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { MatchDetailResponse, MatchFilters } from '@/types'

export function useMatches(filters: MatchFilters = {}) {
  const params = new URLSearchParams()
  if (filters.interest_id !== undefined) params.set('interest_id', String(filters.interest_id))
  if (filters.alerted !== undefined) params.set('alerted', String(filters.alerted))
  if (filters.skip !== undefined) params.set('skip', String(filters.skip))
  if (filters.limit !== undefined) params.set('limit', String(filters.limit))
  const qs = params.toString()

  return useQuery({
    queryKey: ['matches', filters],
    queryFn: () =>
      api.get<MatchDetailResponse[]>(`/matches${qs ? `?${qs}` : ''}`),
  })
}
