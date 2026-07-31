import { useEffect } from 'react'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { formatDateTime } from '@/lib/utils'
import { alertState, formatPreco, formatScore, scoreColor } from '@/lib/match'
import { useMarkRead } from '@/hooks/useMatches'
import type { MatchDetailResponse } from '@/types'

export function MatchDetailModal({
  match,
  open,
  onOpenChange,
}: {
  match: MatchDetailResponse | null
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const markRead = useMarkRead()
  const matchId = match?.id
  const jaLido = match?.lido

  useEffect(() => {
    if (open && matchId !== undefined && !jaLido) {
      markRead.mutate({ id: matchId, lido: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, matchId])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-full max-w-[calc(100%-2rem)] border border-zinc-800 bg-zinc-950 text-zinc-100 sm:max-w-lg">
        <DialogTitle className="pr-8 text-base font-medium text-zinc-100">
          {match?.produto_nome}
        </DialogTitle>

        <div className="max-h-[70vh] space-y-3 overflow-y-auto text-sm">
          <div className="flex flex-wrap gap-x-4 gap-y-2">
            <div>
              <span className="text-zinc-400">Preço: </span>
              <span className="font-mono text-zinc-100">
                {formatPreco(match?.preco_encontrado)}
              </span>
            </div>
            <div>
              <span className="text-zinc-400">Score: </span>
              <span
                className={`font-mono font-medium ${scoreColor(match?.score ?? 0)}`}
              >
                {match ? formatScore(match.score) : '—'}
              </span>
            </div>
            <div>
              <span className="text-zinc-400">Grupo: </span>
              <span className="text-zinc-100">{match?.chat_name || '—'}</span>
            </div>
            <div>
              <span className="text-zinc-400">Palavra: </span>
              <span className="text-zinc-100">
                {match?.matched_keyword || '—'}
              </span>
            </div>
            <div>
              <span className="text-zinc-400">Registrado: </span>
              <span className="text-zinc-100">
                {match ? formatDateTime(match.created_at) : '—'}
              </span>
            </div>
          </div>

          <div className="rounded-lg bg-zinc-900 p-3">
            <p className="whitespace-pre-wrap break-words text-zinc-200">
              {match?.message_text || '—'}
            </p>
          </div>

          {match && match.preco_ok === false && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
              <p className="text-xs font-medium text-amber-400">
                Acima do preço máximo
              </p>
              <p className="mt-1 text-zinc-300">
                Bateu localmente mas o preço excede o limite do interesse —
                registrado para auditoria, sem envio à IA e sem alerta.
              </p>
            </div>
          )}

          {match && match.preco_ok !== false && match.llm_validado === false && (
            <div className="rounded-lg border border-zinc-800 p-3">
              <p className="text-xs font-medium text-zinc-400">IA não validou</p>
              <p className="mt-1 text-zinc-300">
                A validação por IA estava desativada ou falhou — aprovado
                automaticamente (fail-open).
              </p>
            </div>
          )}

          {match?.llm_motivo &&
            match.llm_validado !== false &&
            (match.llm_aprovado ? (
              <div className="rounded-lg border border-zinc-800 p-3">
                <p className="mb-1 text-xs font-medium text-zinc-400">
                  Validação da IA
                </p>
                <p className="whitespace-pre-wrap break-words text-zinc-200">
                  {match.llm_motivo}
                </p>
              </div>
            ) : (
              <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-3">
                <p className="mb-1 text-xs font-medium text-red-400">
                  Reprovado pela IA
                </p>
                <p className="whitespace-pre-wrap break-words text-zinc-200">
                  {match.llm_motivo}
                </p>
              </div>
            ))}

          {match && alertState(match) === 'failed' && (
            <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-3">
              <p className="text-xs font-medium text-red-400">
                Alerta não enviado
              </p>
              <p className="mt-1 text-zinc-300">
                O match foi aprovado, mas o envio da notificação pelo bot
                falhou. Causa comum: o bot não consegue iniciar conversa — mande{' '}
                <span className="font-mono text-zinc-100">/start</span> ao bot
                pela conta configurada como destino dos alertas.
              </p>
            </div>
          )}

          {match?.message_link && (
            <a
              href={match.message_link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-xs text-blue-400 hover:text-blue-300 hover:underline"
            >
              Abrir no Telegram →
            </a>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
