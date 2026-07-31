import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api, ApiError } from '@/lib/api'
import type {
  UserCreate,
  UserPasswordReset,
  UserResponse,
  UserUpdate,
} from '@/types'

export const userKeys = {
  all: ['users'] as const,
  list: () => ['users', 'list'] as const,
}

function erroDe(e: unknown, fallback: string): string {
  if (e instanceof ApiError) return e.detailMessage ?? fallback
  return fallback
}

export function useUsers(enabled = true) {
  return useQuery({
    queryKey: userKeys.list(),
    queryFn: () => api.get<UserResponse[]>('/users'),
    enabled,
    staleTime: 30_000,
  })
}

export function useCreateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: UserCreate) => api.post<UserResponse>('/users', body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.all })
      toast.success('Acesso criado.')
    },
    onError: (e) => toast.error(erroDe(e, 'Não foi possível criar o acesso.')),
  })
}

export function useUpdateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: UserUpdate & { id: number }) =>
      api.patch<UserResponse>(`/users/${id}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.all })
      toast.success('Acesso atualizado.')
    },
    onError: (e) => toast.error(erroDe(e, 'Não foi possível atualizar.')),
  })
}

export function useResetUserPassword() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: UserPasswordReset & { id: number }) =>
      api.post<UserResponse>(`/users/${id}/password`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.all })
      toast.success('Senha redefinida. A pessoa vai precisar entrar de novo.')
    },
    onError: (e) => toast.error(erroDe(e, 'Não foi possível redefinir a senha.')),
  })
}

export function useDeleteUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.delete(`/users/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: userKeys.all })
      toast.success('Acesso removido.')
    },
    onError: (e) => toast.error(erroDe(e, 'Não foi possível remover o acesso.')),
  })
}
