import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AlertTestResponse, SettingsResponse, SettingsUpdate } from '@/types'

export function useSettings(opts?: { poll?: boolean }) {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => api.get<SettingsResponse>('/settings'),
    refetchInterval: opts?.poll ? 5_000 : false,
  })
}

export function useUpdateSettings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: SettingsUpdate) =>
      api.put<SettingsResponse>('/settings', data),
    onSuccess: (data) => {
      qc.setQueryData(['settings'], data)
      qc.invalidateQueries({ queryKey: ['health'] })
    },
  })
}

export function useTestAlert() {
  return useMutation({
    mutationFn: () => api.post<AlertTestResponse>('/settings/alert/test', {}),
  })
}
