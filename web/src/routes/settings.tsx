import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertStatus } from '@/components/features/AlertStatus'
import { BotSetupGuide } from '@/components/features/BotSetupGuide'
import { BotTokenForm } from '@/components/features/BotTokenForm'
import { ConnectionCard } from '@/components/features/ConnectionCard'
import { useSettings } from '@/hooks/useSettings'

export const Route = createFileRoute('/settings')({
  component: Settings,
})

function Settings() {
  // poll: o handler `/start` do bot grava `alert_target` no servidor; sem o
  // refetch o estado do destino só mudaria depois de recarregar a página.
  const { data, isLoading } = useSettings({ poll: true })

  return (
    <div className="max-w-lg space-y-6">
      <Card className="border-zinc-800 bg-zinc-950 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-200">
            Conexão
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ConnectionCard />
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-950 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-200">
            Como criar o bot de notificações
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <BotSetupGuide />
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-9 w-full" />
            </div>
          ) : (
            <>
              <BotTokenForm settings={data} />
              <AlertStatus settings={data} />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
