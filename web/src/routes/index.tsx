import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useHealth } from '@/hooks/useHealth'
import { useInterests } from '@/hooks/useInterests'
import { useMatches } from '@/hooks/useMatches'
import { Activity, ShoppingBag, ListChecks, Zap } from 'lucide-react'

export const Route = createFileRoute('/')({
  component: Dashboard,
})

function StatCard({
  icon: Icon,
  label,
  value,
  isLoading,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  isLoading: boolean
}) {
  return (
    <Card className="border-zinc-800 bg-zinc-950">
      <CardHeader className="flex-row items-center justify-between gap-4">
        <div className="space-y-1">
          <CardTitle className="text-sm font-medium text-zinc-400">
            {label}
          </CardTitle>
          <div className="text-2xl font-semibold tracking-tight text-zinc-100">
            {isLoading ? <Skeleton className="h-7 w-16 bg-zinc-800" /> : value}
          </div>
        </div>
        <div className="rounded-lg bg-amber-400/10 p-2.5">
          <Icon className="size-5 text-amber-400" />
        </div>
      </CardHeader>
    </Card>
  )
}

function Dashboard() {
  const { data: health, isLoading: healthLoading } = useHealth()
  const { data: interests, isLoading: interestsLoading } = useInterests()
  const { data: matches, isLoading: matchesLoading } = useMatches({ limit: 5 })

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-zinc-800 bg-zinc-950">
          <CardHeader className="flex-row items-center justify-between gap-4">
            <div className="space-y-1">
              <CardTitle className="text-sm font-medium text-zinc-400">
                Status
              </CardTitle>
              <div className="text-2xl font-semibold tracking-tight text-zinc-100">
                {healthLoading ? (
                  <Skeleton className="h-7 w-20 bg-zinc-800" />
                ) : (
                  <Badge
                    variant="outline"
                    className={
                      health?.status === 'ok'
                        ? 'border-green-500/30 text-green-400'
                        : 'border-red-500/30 text-red-400'
                    }
                  >
                    {health?.status === 'ok' ? 'Online' : 'Offline'}
                  </Badge>
                )}
              </div>
            </div>
            <div className="rounded-lg bg-amber-400/10 p-2.5">
              <Zap className="size-5 text-amber-400" />
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-1 text-xs text-zinc-500">
              <p>
                Telegram:{' '}
                {healthLoading ? (
                  <Skeleton className="inline-block h-3 w-12 bg-zinc-800" />
                ) : health?.telegram_connected ? (
                  <span className="text-green-400">Conectado</span>
                ) : (
                  <span className="text-red-400">Desconectado</span>
                )}
              </p>
              <p>
                Uptime:{' '}
                {healthLoading ? (
                  <Skeleton className="inline-block h-3 w-16 bg-zinc-800" />
                ) : health ? (
                  formatUptime(health.uptime_seconds)
                ) : (
                  '—'
                )}
              </p>
            </div>
          </CardContent>
        </Card>

        <StatCard
          icon={ShoppingBag}
          label="Interesses"
          value={String(interests?.length ?? 0)}
          isLoading={interestsLoading}
        />
        <StatCard
          icon={ListChecks}
          label="Matches"
          value={String(matches?.length ?? 0)}
          isLoading={matchesLoading}
        />
        <StatCard
          icon={Activity}
          label="Ativos"
          value={String(
            interests?.filter((i) => i.ativo).length ?? 0,
          )}
          isLoading={interestsLoading}
        />
      </div>

      <Card className="border-zinc-800 bg-zinc-950">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-200">
            Matches Recentes
          </CardTitle>
        </CardHeader>
        <CardContent>
          {matchesLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full bg-zinc-800" />
              ))}
            </div>
          ) : !matches?.length ? (
            <p className="py-4 text-center text-sm text-zinc-500">
              Nenhum match recente.
            </p>
          ) : (
            <div className="space-y-2">
              {matches.map((match) => (
                <div
                  key={match.id}
                  className="flex items-center justify-between rounded-lg border border-zinc-800 px-4 py-2.5"
                >
                  <div className="space-y-0.5">
                    <p className="text-sm font-medium text-zinc-200">
                      {match.produto_nome}
                    </p>
                    <p className="text-xs text-zinc-500">
                      {match.chat_name || 'Grupo desconhecido'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-sm text-amber-400">
                      {match.preco_encontrado
                        ? `R$ ${match.preco_encontrado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                        : '—'}
                    </p>
                    <p className="text-xs text-zinc-500">
                      {Math.round(match.score * 100)}% match
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function formatUptime(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  const parts: string[] = []
  if (h > 0) parts.push(`${h}h`)
  if (m > 0) parts.push(`${m}m`)
  parts.push(`${s}s`)
  return parts.join(' ')
}
