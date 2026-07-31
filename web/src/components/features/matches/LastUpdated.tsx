import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useMatchesInfinite } from '@/hooks/useMatches'
import type { MatchFilters } from '@/types'

function formatAgo(ms: number) {
  const s = Math.floor(ms / 1000)
  if (s < 15) return 'agora mesmo'
  if (s < 60) return `há ${s}s`
  const min = Math.floor(s / 60)
  if (min < 60) return `há ${min} min`
  const h = Math.floor(min / 60)
  return `há ${h}h`
}

export function LastUpdated({ filters }: { filters: MatchFilters }) {
  const qc = useQueryClient()
  const { dataUpdatedAt, isFetching } = useMatchesInfinite(filters)

  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 5_000)
    return () => clearInterval(id)
  }, [])

  if (!dataUpdatedAt) return null

  return (
    <div className="flex items-center justify-end gap-1 text-[11px] text-zinc-600">
      <span
        aria-hidden
        className={cn(
          'size-1.5 rounded-full bg-zinc-700',
          isFetching && 'animate-pulse bg-amber-400',
        )}
      />
      <span>
        {isFetching
          ? 'atualizando…'
          : `atualizado ${formatAgo(Math.max(0, now - dataUpdatedAt))}`}
      </span>
      <Button
        variant="ghost"
        size="icon-xs"
        aria-label="Atualizar agora"
        title="Atualizar agora"
        disabled={isFetching}
        onClick={() => qc.invalidateQueries({ queryKey: ['matches'] })}
        className="text-zinc-600 hover:text-zinc-300"
      >
        <RefreshCw className={cn(isFetching && 'animate-spin')} />
      </Button>
    </div>
  )
}
