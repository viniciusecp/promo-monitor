import { toast } from 'sonner'
import { CheckCircle2, Loader2 } from 'lucide-react'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { useTestAlert } from '@/hooks/useSettings'
import type { SettingsResponse } from '@/types'

interface Props {
  settings?: SettingsResponse
}

/**
 * Estado do destino dos alertas. Só leitura: o destino é definido exclusivamente
 * pelo `/start` mandado ao bot (o handler grava `alert_target` no servidor) e o
 * polling de 5s da tela traz o valor novo sozinho.
 */
export function AlertStatus({ settings }: Props) {
  const testAlert = useTestAlert()

  if (!settings?.bot_connected) return null

  function handleTest() {
    testAlert.mutate(undefined, {
      onSuccess: (result) =>
        result.ok
          ? toast.success('Mensagem de teste enviada')
          : toast.error(result.error ?? 'Não foi possível enviar'),
      onError: () => toast.error('Não foi possível enviar o teste'),
    })
  }

  if (!settings.alert_target) {
    return (
      <Alert variant="warning">
        <Loader2 className="animate-spin" />
        <span>
          Aguardando o <code className="font-mono">/start</code>…{' '}
          {settings.bot_username && (
            <a
              href={`https://t.me/${settings.bot_username}`}
              target="_blank"
              rel="noreferrer"
              className="font-medium underline underline-offset-2"
            >
              Abrir @{settings.bot_username}
            </a>
          )}{' '}
          — assim que você mandar, as promoções começam a chegar nessa conversa.
        </span>
      </Alert>
    )
  }

  return (
    <div className="space-y-3">
      <Alert variant="success">
        <CheckCircle2 />
        <span>
          Notificações ativas na sua conversa com o bot. Para mudar de conversa,
          mande <code className="font-mono">/start</code> de onde você quer
          receber.
        </span>
      </Alert>
      <Button
        variant="outline"
        onClick={handleTest}
        disabled={testAlert.isPending}
      >
        {testAlert.isPending ? 'Enviando…' : 'Enviar teste'}
      </Button>
    </div>
  )
}
