import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { useMatchStats } from '@/hooks/useMatches'
import { useHealth } from '@/hooks/useHealth'

function Stat({
  label,
  value,
  isLoading,
  accent,
}: {
  label: string
  value: string
  isLoading?: boolean
  accent?: string
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2">
      <p className="text-[11px] text-zinc-500">{label}</p>
      {isLoading ? (
        <Skeleton className="mt-1 h-5 w-10 bg-zinc-800" />
      ) : (
        <p
          className={cn(
            'text-lg font-semibold tabular-nums text-zinc-100',
            accent,
          )}
        >
          {value}
        </p>
      )}
    </div>
  )
}

export function MatchStats() {
  const { data: stats, isLoading } = useMatchStats()
  const { data: health, isLoading: healthLoading } = useHealth()

  const online = health?.status === 'ok' && health?.telegram_connected

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      <Stat
        label="Não lidos"
        value={String(stats?.nao_lidos ?? 0)}
        isLoading={isLoading}
        accent={stats?.nao_lidos ? 'text-amber-400' : undefined}
      />
      <Stat
        label="Hoje"
        value={String(stats?.novos_hoje ?? 0)}
        isLoading={isLoading}
      />
      <Stat
        label="Últimas 24h"
        value={String(stats?.ultimas_24h ?? 0)}
        isLoading={isLoading}
      />
      <Stat
        label="Últimos 7 dias"
        value={String(stats?.ultimos_7d ?? 0)}
        isLoading={isLoading}
      />
      <div className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2">
        <p className="text-[11px] text-zinc-500">Telegram</p>
        {healthLoading ? (
          <Skeleton className="mt-1 h-5 w-16 bg-zinc-800" />
        ) : (
          <p className="flex items-center gap-1.5 pt-1 text-sm font-medium">
            <span
              className={cn(
                'size-2 rounded-full',
                online ? 'bg-green-400' : 'bg-red-400',
              )}
            />
            <span className={online ? 'text-green-400' : 'text-red-400'}>
              {online ? 'Conectado' : 'Offline'}
            </span>
            <span className="ml-auto text-[11px] text-zinc-600">
              {stats?.interesses_ativos ?? 0} ativos
            </span>
          </p>
        )}
      </div>
    </div>
  )
}
