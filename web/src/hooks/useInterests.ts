import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { InterestResponse, InterestCreate, InterestUpdate } from '@/types'

export function useInterests(ativo?: boolean) {
  return useQuery({
    queryKey: ['interests', { ativo }],
    queryFn: () =>
      api.get<InterestResponse[]>(
        ativo !== undefined ? `/interests?ativo=${ativo}` : '/interests',
      ),
  })
}

export function useInterest(id: number) {
  return useQuery({
    queryKey: ['interests', id],
    queryFn: () => api.get<InterestResponse>(`/interests/${id}`),
    enabled: !!id,
  })
}

export function useCreateInterest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: InterestCreate) =>
      api.post<InterestResponse>('/interests', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['interests'] }),
  })
}

export function useUpdateInterest(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: InterestUpdate) =>
      api.put<InterestResponse>(`/interests/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['interests'] })
      qc.invalidateQueries({ queryKey: ['interests', id] })
    },
  })
}

export function useDeleteInterest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.delete(`/interests/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['interests'] }),
  })
}
