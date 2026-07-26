import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { CheckCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { MatchStats } from '@/components/features/matches/MatchStats'
import { MatchFilterBar } from '@/components/features/matches/MatchFilterBar'
import { MatchFeed } from '@/components/features/matches/MatchFeed'
import { useMarkAllRead, useMatchStats } from '@/hooks/useMatches'
import { DEFAULT_MATCH_FILTERS } from '@/types'
import type { MatchFilters } from '@/types'

export const Route = createFileRoute('/')({
  component: MatchesFeedPage,
})

function MatchesFeedPage() {
  const [filters, setFilters] = useState<MatchFilters>(DEFAULT_MATCH_FILTERS)
  const { data: stats } = useMatchStats()
  const markAllRead = useMarkAllRead()

  const unread = stats?.nao_lidos ?? 0

  return (
    <div className="space-y-4">
      <MatchStats />

      <MatchFilterBar filters={filters} onChange={setFilters} />

      {unread > 0 && (
        <div className="sticky top-14 z-20 -mx-4 flex items-center justify-between gap-3 border-y border-amber-400/20 bg-zinc-900/95 px-4 py-2 backdrop-blur-sm md:mx-0 md:rounded-lg md:border md:px-3">
          <p className="text-sm text-amber-400">
            <span className="font-semibold tabular-nums">{unread}</span> não
            lido{unread > 1 ? 's' : ''}
          </p>
          <Button
            variant="outline"
            size="sm"
            disabled={markAllRead.isPending}
            onClick={() => markAllRead.mutate(filters)}
          >
            <CheckCheck />
            <span className="hidden sm:inline">Marcar todos como lidos</span>
            <span className="sm:hidden">Marcar lidos</span>
          </Button>
        </div>
      )}

      <MatchFeed filters={filters} />
    </div>
  )
}
