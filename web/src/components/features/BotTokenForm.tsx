import { useState } from 'react'
import { toast } from 'sonner'
import { CheckCircle2 } from 'lucide-react'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useUpdateSettings } from '@/hooks/useSettings'
import type { SettingsResponse } from '@/types'

interface Props {
  settings?: SettingsResponse
}

export function BotTokenForm({ settings }: Props) {
  const [token, setToken] = useState('')
  const update = useUpdateSettings()

  const isSet = !!settings?.telegram_bot_token_set

  function save(value: string | null) {
    update.mutate(
      { telegram_bot_token: value },
      {
        onSuccess: (data) => {
          setToken('')
          if (value === null) {
            toast.success('Token removido')
          } else if (data.bot_connected) {
            toast.success(
              data.bot_username
                ? `Bot @${data.bot_username} conectado`
                : 'Bot conectado',
            )
          } else {
            toast.error('Token salvo, mas o bot não conectou')
          }
        },
        onError: () => toast.error('Erro ao salvar o token'),
      },
    )
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (token.trim()) save(token.trim())
      }}
      className="space-y-4"
    >
      <div className="space-y-2">
        <Label htmlFor="bot_token">Token do bot</Label>
        <Input
          id="bot_token"
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder={
            settings?.telegram_bot_token_masked ?? '123456789:AAE...xyz'
          }
          autoComplete="off"
          className="font-mono"
        />
        <p className="text-[13px] leading-relaxed text-zinc-500">
          Salvar aqui vale na hora — não é preciso reiniciar o servidor. Deixe
          em branco e clique em <span className="text-zinc-400">Remover</span>{' '}
          para desativar as notificações.
        </p>
      </div>

      {settings?.bot_connected && settings.bot_username && (
        <Alert variant="success">
          <CheckCircle2 />
          <span>
            Conectado como{' '}
            <a
              href={`https://t.me/${settings.bot_username}`}
              target="_blank"
              rel="noreferrer"
              className="font-medium underline underline-offset-2"
            >
              @{settings.bot_username}
            </a>
          </span>
        </Alert>
      )}

      {settings?.bot_last_error && !settings.bot_connected && (
        <Alert variant="destructive">
          <span>
            O bot não conectou: {settings.bot_last_error}
          </span>
        </Alert>
      )}

      <div className="flex gap-3">
        <Button type="submit" disabled={update.isPending || !token.trim()}>
          {update.isPending ? 'Salvando…' : 'Salvar token'}
        </Button>
        {isSet && (
          <Button
            type="button"
            variant="outline"
            onClick={() => save(null)}
            disabled={update.isPending}
          >
            Remover
          </Button>
        )}
      </div>
    </form>
  )
}
