import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useTelegramChats } from '@/hooks/useTelegramChats'
import type { SettingsResponse } from '@/types'

interface Props {
  defaultValues?: SettingsResponse
  onSubmit: (data: { alert_target: string | null }) => void
  isPending: boolean
}

const typeLabels: Record<string, string> = {
  group: 'grupo',
  channel: 'canal',
  user: 'contato',
}

export function SettingsForm({ defaultValues, onSubmit, isPending }: Props) {
  const [alertTarget, setAlertTarget] = useState(defaultValues?.alert_target ?? '')
  const { data: chats, isLoading, isError } = useTelegramChats()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit({ alert_target: alertTarget.trim() || null })
  }

  const savedNotInList =
    alertTarget && chats && !chats.some((c) => c.id === alertTarget)

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="space-y-2">
        <Label htmlFor="alert_target">Chat de notificação (bot)</Label>
        <Select value={alertTarget} onValueChange={(value) => setAlertTarget(value ?? '')}>
          <SelectTrigger id="alert_target" className="w-full">
            <SelectValue placeholder="Nenhum (alertas desativados)" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Nenhum (alertas desativados)</SelectItem>
            {savedNotInList && (
              <SelectItem value={alertTarget}>
                {alertTarget} (atual)
              </SelectItem>
            )}
            {chats?.map((chat) => (
              <SelectItem key={chat.id} value={chat.id}>
                {chat.title}
                <span className="text-zinc-500"> ({typeLabels[chat.type] ?? chat.type})</span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-[13px] leading-relaxed text-zinc-500">
          As promoções são enviadas pelo bot. O jeito mais fácil é abrir o seu bot
          no Telegram e mandar <span className="text-zinc-400">/start</span> — isso
          preenche este campo automaticamente com a sua conversa (e garante a
          notificação no celular). Em branco (<span className="text-zinc-400">Nenhum</span>)
          os alertas ficam desativados — nada é enviado.
        </p>
        {isLoading && (
          <p className="text-[13px] text-zinc-500">Carregando seus grupos…</p>
        )}
        {(isError || (!isLoading && chats?.length === 0)) && (
          <p className="text-[13px] text-amber-500">
            Não foi possível listar seus grupos. Verifique se o backend está rodando e
            autenticado no Telegram.
          </p>
        )}
      </div>

      <div className="flex gap-3 pt-2">
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Salvando...' : 'Salvar'}
        </Button>
      </div>
    </form>
  )
}
