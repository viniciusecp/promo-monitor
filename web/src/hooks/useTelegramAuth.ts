import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AuthStatusResponse } from '@/types'

/** Chave-família: invalidar ['telegram','auth'] atinge status e derivados. */
export const authKeys = {
  all: ['telegram', 'auth'] as const,
  status: () => ['telegram', 'auth', 'status'] as const,
}

export function useAuthStatus() {
  return useQuery({
    queryKey: authKeys.status(),
    queryFn: () => api.get<AuthStatusResponse>('/telegram/auth/status'),
    // Enquanto não autenticado o polling é rápido: é ele que faz a tela de
    // login reagir a mudanças (2FA, código expirado, sessão revogada).
    refetchInterval: (query) =>
      query.state.data?.status === 'authenticated' ? 30_000 : 3_000,
    // O default global é retry:1 e staleTime:15s — aqui os dois atrapalham: o
    // gate do __root demoraria o dobro para decidir e um 503 pareceria travamento.
    retry: false,
    staleTime: 0,
  })
}

/** Toda mutação devolve o status completo, então dá para atualizar o cache sem
 *  um GET de volta. Ao autenticar, o resto do app precisa ser reavaliado. */
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
    // Um código errado muda o estado no servidor (mensagem de erro); sem isso a
    // tela ficaria mostrando o snapshot antigo até o próximo poll.
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

export function useLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<AuthStatusResponse>('/telegram/auth/logout', {}),
    onSuccess: (data) => {
      // Limpa tudo: matches, interesses e chats pertenciam à conta que saiu.
      qc.clear()
      qc.setQueryData(authKeys.status(), data)
    },
  })
}
