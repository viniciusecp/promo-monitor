import { useState } from 'react'
import { Inbox, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useMatchesInfinite } from '@/hooks/useMatches'
import { MatchTable } from './MatchTable'
import { MatchCard } from './MatchCard'
import { MatchDetailModal } from './MatchDetailModal'
import type { MatchDetailResponse, MatchFilters } from '@/types'

export function MatchFeed({ filters }: { filters: MatchFilters }) {
  const [selected, setSelected] = useState<MatchDetailResponse | null>(null)
  const {
    data,
    isLoading,
    isError,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useMatchesInfinite(filters)

  const matches = data?.pages.flatMap((p) => p.items) ?? []
  const total = data?.pages[0]?.total ?? 0

  const selectedLive = selected
    ? (matches.find((m) => m.id === selected.id) ?? selected)
    : null

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full rounded-lg bg-zinc-800" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-6 text-center">
        <p className="text-sm text-red-400">Não foi possível carregar os matches.</p>
        <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
          Tentar novamente
        </Button>
      </div>
    )
  }

  if (matches.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-zinc-800 py-12 text-center">
        <Inbox className="mx-auto size-6 text-zinc-700" />
        <p className="mt-2 text-sm text-zinc-500">
          Nenhum match com os filtros atuais.
        </p>
      </div>
    )
  }

  return (
    <>
      <div className="hidden rounded-lg border border-zinc-800 bg-zinc-950 md:block">
        <MatchTable matches={matches} onSelect={setSelected} />
      </div>

      <div className="space-y-2 md:hidden">
        {matches.map((match) => (
          <MatchCard key={match.id} match={match} onSelect={setSelected} />
        ))}
      </div>

      <div className="flex flex-col items-center gap-2 pt-4">
        {hasNextPage ? (
          <Button
            variant="outline"
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
          >
            {isFetchingNextPage && <Loader2 className="animate-spin" />}
            Carregar mais
          </Button>
        ) : (
          matches.length > 0 && (
            <p className="text-xs text-zinc-600">Fim da lista.</p>
          )
        )}
        <p className="text-xs text-zinc-600">
          {matches.length} de {total}
        </p>
      </div>

      <MatchDetailModal
        match={selectedLive}
        open={selected !== null}
        onOpenChange={(open) => {
          if (!open) setSelected(null)
        }}
      />
    </>
  )
}
