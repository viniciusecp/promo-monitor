import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useAuthStatus, useTelegramLogout } from '@/hooks/useTelegramAuth'
import { useHealth } from '@/hooks/useHealth'

const TONES = {
  ok: 'bg-emerald-500/15 text-emerald-400',
  paused: 'bg-amber-500/15 text-amber-400',
  off: 'bg-zinc-700/40 text-zinc-400',
} as const

function StatusBadge({
  tone,
  children,
}: {
  tone: keyof typeof TONES
  children: React.ReactNode
}) {
  return <Badge className={TONES[tone]}>{children}</Badge>
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 py-1.5">
      <span className="text-[13px] text-zinc-500">{label}</span>
      <span className="text-right text-[13px] text-zinc-200">{children}</span>
    </div>
  )
}

export function ConnectionCard() {
  const { data: auth } = useAuthStatus()
  const { data: health } = useHealth()
  const logout = useTelegramLogout()
  const navigate = useNavigate()
  const [confirmOpen, setConfirmOpen] = useState(false)

  const name = auth?.user?.username
    ? `@${auth.user.username}`
    : (auth?.user?.first_name ?? '—')

  const captura: { tone: keyof typeof TONES; label: string } = !health?.worker_running
    ? { tone: 'off', label: 'parada' }
    : health.capture_active
      ? { tone: 'ok', label: 'ativa' }
      : { tone: 'paused', label: 'pausada (sem interesses ativos)' }

  function handleLogout() {
    logout.mutate(undefined, {
      onSuccess: () => {
        setConfirmOpen(false)
        toast.success('Conta desconectada')
        navigate({ to: '/telegram' })
      },
      onError: () => toast.error('Não foi possível desconectar'),
    })
  }

  return (
    <div className="space-y-4">
      <div className="divide-y divide-zinc-800/70">
        <Row label="Conta">{name}</Row>
        <Row label="Telefone">
          <span className="font-mono">{auth?.phone_masked || '—'}</span>
        </Row>
        <Row label="Conexão">
          <StatusBadge tone={health?.telegram_connected ? 'ok' : 'off'}>
            {health?.telegram_connected ? 'conectado' : 'offline'}
          </StatusBadge>
        </Row>
        <Row label="Captura de mensagens">
          <StatusBadge tone={captura.tone}>{captura.label}</StatusBadge>
        </Row>
        <Row label="Bot de alertas">
          <StatusBadge tone={health?.bot_connected ? 'ok' : 'off'}>
            {health?.bot_connected ? 'conectado' : 'não configurado'}
          </StatusBadge>
        </Row>
      </div>

      <Button variant="outline" onClick={() => setConfirmOpen(true)}>
        Desconectar conta
      </Button>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Desconectar do Telegram</DialogTitle>
            <DialogDescription>
              A sessão será encerrada e a captura de mensagens vai parar. Você
              precisará entrar de novo com o código de verificação. Os interesses
              e as promoções já capturadas continuam salvos.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter showCloseButton>
            <Button
              variant="destructive"
              onClick={handleLogout}
              disabled={logout.isPending}
            >
              {logout.isPending ? 'Desconectando…' : 'Desconectar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
