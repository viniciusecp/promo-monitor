import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
  type InfiniteData,
} from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import type {
  MatchChatResponse,
  MatchFilters,
  MatchListResponse,
  MatchReadResponse,
  MatchStatsResponse,
} from '@/types'

const TZ = Intl.DateTimeFormat().resolvedOptions().timeZone
const PAGE_SIZE = 30

const matchKeys = {
  all: ['matches'] as const,
  list: (filters: MatchFilters) => ['matches', 'list', filters] as const,
  lists: () => ['matches', 'list'] as const,
  stats: () => ['matches', 'stats', TZ] as const,
  chats: () => ['matches', 'chats'] as const,
}

function buildMatchQuery(filters: MatchFilters, skip: number, limit: number) {
  const p = new URLSearchParams()
  p.set('periodo', filters.periodo)
  p.set('tz', TZ)
  if (filters.nao_lidos) p.set('nao_lidos', 'true')
  filters.status.forEach((s) => p.append('status', s))
  if (filters.chat_id !== undefined) p.set('chat_id', String(filters.chat_id))
  if (filters.preco_min !== undefined) p.set('preco_min', String(filters.preco_min))
  if (filters.preco_max !== undefined) p.set('preco_max', String(filters.preco_max))
  p.set('order_by', filters.order_by)
  p.set('order_dir', filters.order_dir)
  p.set('skip', String(skip))
  p.set('limit', String(limit))
  return p.toString()
}

function toReadAllBody(filters: MatchFilters) {
  return {
    periodo: filters.periodo,
    tz: TZ,
    nao_lidos: filters.nao_lidos,
    status: filters.status,
    chat_id: filters.chat_id ?? null,
    preco_min: filters.preco_min ?? null,
    preco_max: filters.preco_max ?? null,
  }
}

export function useMatchesInfinite(filters: MatchFilters) {
  return useInfiniteQuery({
    queryKey: matchKeys.list(filters),
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      api.get<MatchListResponse>(
        `/matches?${buildMatchQuery(filters, pageParam, PAGE_SIZE)}`,
      ),
    getNextPageParam: (last, all) =>
      last.has_more ? all.reduce((n, p) => n + p.items.length, 0) : undefined,
    refetchOnWindowFocus: (query) => (query.state.data?.pages.length ?? 1) === 1,
  })
}

export function useMatchStats() {
  return useQuery({
    queryKey: matchKeys.stats(),
    queryFn: () =>
      api.get<MatchStatsResponse>(
        `/matches/stats?tz=${encodeURIComponent(TZ)}`,
      ),
    refetchOnWindowFocus: true,
  })
}

export function useMatchChats() {
  return useQuery({
    queryKey: matchKeys.chats(),
    queryFn: () => api.get<MatchChatResponse[]>('/matches/chats'),
    staleTime: 5 * 60_000,
  })
}

export function useMarkRead() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ id, lido }: { id: number; lido: boolean }) =>
      api.post<MatchReadResponse>(`/matches/${id}/${lido ? 'read' : 'unread'}`, {}),

    onMutate: async ({ id, lido }) => {
      await qc.cancelQueries({ queryKey: matchKeys.lists() })

      const snapshot = qc.getQueriesData<InfiniteData<MatchListResponse>>({
        queryKey: matchKeys.lists(),
      })

      for (const [key, data] of snapshot) {
        if (!data) continue
        qc.setQueryData(key, {
          ...data,
          pages: data.pages.map((page) => ({
            ...page,
            items: page.items.map((m) =>
              m.id === id
                ? { ...m, lido, lido_em: lido ? new Date().toISOString() : null }
                : m,
            ),
          })),
        })
      }

      qc.setQueryData<MatchStatsResponse>(matchKeys.stats(), (s) =>
        s ? { ...s, nao_lidos: Math.max(0, s.nao_lidos + (lido ? -1 : 1)) } : s,
      )

      return { snapshot }
    },

    onError: (_err, _vars, ctx) => {
      ctx?.snapshot.forEach(([key, data]) => qc.setQueryData(key, data))
      toast.error('Não foi possível atualizar o estado de leitura.')
    },

    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['matches', 'stats'] })
    },
  })
}

export function useMarkAllRead() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (filters: MatchFilters) =>
      api.post<{ updated: number }>('/matches/read-all', toReadAllBody(filters)),
    onSuccess: (res) => {
      toast.success(
        res.updated === 0
          ? 'Nenhum match não lido no filtro atual.'
          : `${res.updated} match(es) marcado(s) como lido(s).`,
      )
      qc.invalidateQueries({ queryKey: matchKeys.all })
    },
    onError: () => toast.error('Não foi possível marcar todos como lidos.'),
  })
}
