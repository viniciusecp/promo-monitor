import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AuthStatusResponse } from '@/types'

export const authKeys = {
  all: ['telegram', 'auth'] as const,
  status: () => ['telegram', 'auth', 'status'] as const,
}

export function useAuthStatus(enabled = true) {
  return useQuery({
    queryKey: authKeys.status(),
    queryFn: () => api.get<AuthStatusResponse>('/telegram/auth/status'),
    enabled,
    refetchInterval: (query) =>
      query.state.data?.status === 'authenticated' ? 30_000 : 3_000,
    retry: false,
    staleTime: 0,
  })
}

function applyStatus(qc: QueryClient, data: AuthStatusResponse) {
  qc.setQueryData(authKeys.status(), data)
  if (data.status === 'authenticated') {
    qc.invalidateQueries({ queryKey: ['health'] })
    qc.invalidateQueries({ queryKey: ['telegram', 'chats'] })
    qc.invalidateQueries({ queryKey: ['settings'] })
  }
}

export function useRequestCode() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () =>
      api.post<AuthStatusResponse>('/telegram/auth/request-code', {}),
    onSuccess: (data) => applyStatus(qc, data),
  })
}

export function useSubmitCode() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (code: string) =>
      api.post<AuthStatusResponse>('/telegram/auth/code', { code }),
    onSuccess: (data) => applyStatus(qc, data),
    onError: () => qc.invalidateQueries({ queryKey: authKeys.status() }),
  })
}

export function useSubmitPassword() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (password: string) =>
      api.post<AuthStatusResponse>('/telegram/auth/password', { password }),
    onSuccess: (data) => applyStatus(qc, data),
    onError: () => qc.invalidateQueries({ queryKey: authKeys.status() }),
  })
}

export function useTelegramLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<AuthStatusResponse>('/telegram/auth/logout', {}),
    onSuccess: (data) => {
      qc.removeQueries({ queryKey: ['matches'] })
      qc.removeQueries({ queryKey: ['messages'] })
      qc.removeQueries({ queryKey: ['telegram', 'chats'] })
      qc.invalidateQueries({ queryKey: ['health'] })
      qc.setQueryData(authKeys.status(), data)
    },
  })
}
