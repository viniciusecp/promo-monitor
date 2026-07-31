import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api, ApiError } from '@/lib/api'
import type {
  ChangePasswordRequest,
  LoginRequest,
  SessionResponse,
  SessionUser,
} from '@/types'

export const sessionKeys = {
  all: ['session'] as const,
  me: () => ['session', 'me'] as const,
}

export function useSession() {
  return useQuery<SessionUser | null>({
    queryKey: sessionKeys.me(),
    queryFn: async () => {
      try {
        const data = await api.get<SessionResponse>('/auth/me')
        return data.user
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) return null
        throw e
      }
    },
    retry: false,
    staleTime: 0,
    refetchOnWindowFocus: true,
  })
}

export function useLogin() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: LoginRequest) =>
      api.post<SessionResponse>('/auth/login', body),
    onSuccess: (data) => {
      qc.setQueryData(sessionKeys.me(), data.user)
      qc.invalidateQueries()
    },
  })
}

export function useLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<{ ok: boolean }>('/auth/logout', {}),
    onSuccess: () => {
      qc.clear()
      qc.setQueryData(sessionKeys.me(), null)
    },
    onError: () => toast.error('Não foi possível sair. Tente de novo.'),
  })
}

export function useChangePassword() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: ChangePasswordRequest) =>
      api.post<SessionResponse>('/auth/password', body),
    onSuccess: (data) => {
      qc.setQueryData(sessionKeys.me(), data.user)
      toast.success('Senha alterada.')
    },
  })
}
