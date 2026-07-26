import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AlertTestResponse, SettingsResponse, SettingsUpdate } from '@/types'

/**
 * `poll` liga um refetch de 5s. Só a tela de Configurações usa: é o que faz o
 * `/start` mandado ao bot refletir sozinho no estado dos alertas, sem recarregar
 * a página (o handler do bot grava `alert_target` no servidor).
 */
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
      // O token do bot afeta `bot_connected` no /health.
      qc.invalidateQueries({ queryKey: ['health'] })
    },
  })
}

export function useTestAlert() {
  return useMutation({
    mutationFn: () => api.post<AlertTestResponse>('/settings/alert/test', {}),
  })
}
