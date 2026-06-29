import { createFileRoute } from '@tanstack/react-router'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { SettingsForm } from '@/components/features/SettingsForm'
import { BotSetupGuide } from '@/components/features/BotSetupGuide'
import { useSettings, useUpdateSettings } from '@/hooks/useSettings'

export const Route = createFileRoute('/settings')({
  component: Settings,
})

function Settings() {
  const { data, isLoading } = useSettings()
  const updateMutation = useUpdateSettings()

  function handleSubmit(payload: { alert_target: string | null }) {
    updateMutation.mutate(payload, {
      onSuccess: () => toast.success('Configurações salvas'),
      onError: () => toast.error('Erro ao salvar configurações'),
    })
  }

  return (
    <div className="max-w-lg space-y-6">
      <Card className="border-zinc-800 bg-zinc-950 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-200">
            Como criar o bot de notificações
          </CardTitle>
        </CardHeader>
        <CardContent>
          <BotSetupGuide />
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-950 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-200">
            Destino dos alertas
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-24" />
            </div>
          ) : (
            <SettingsForm
              defaultValues={data}
              onSubmit={handleSubmit}
              isPending={updateMutation.isPending}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
