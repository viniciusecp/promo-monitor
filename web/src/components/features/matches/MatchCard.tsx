import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import {
  alertState,
  formatPreco,
  formatRelativeDateTime,
  formatScore,
  scoreColor,
} from '@/lib/match'
import { ReadToggle } from './ReadToggle'
import type { MatchDetailResponse } from '@/types'

/**
 * Versão mobile da linha da tabela. É um componente separado de propósito: um
 * <table> não vira cards empilhados só com CSS sem overrides de display:block
 * que quebram a semântica e o overflow-x-auto do wrapper. A lógica de fato
 * mora em `lib/match.ts`, então a duplicação aqui é só de layout.
 */
export function MatchCard({
  match,
  onSelect,
}: {
  match: MatchDetailResponse
  onSelect: (match: MatchDetailResponse) => void
}) {
  const st = alertState(match)

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onSelect(match)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect(match)
        }
      }}
      className={cn(
        'w-full cursor-pointer rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-left transition-colors active:bg-zinc-900',
        !match.lido && 'border-l-2 border-l-amber-400 bg-amber-400/[0.03]',
      )}
    >
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <p
            className={cn(
              'flex items-center gap-2 text-sm',
              match.lido
                ? 'font-medium text-zinc-400'
                : 'font-semibold text-zinc-100',
            )}
          >
            {!match.lido && (
              <span
                aria-hidden
                className="size-1.5 shrink-0 rounded-full bg-amber-400"
              />
            )}
            <span className="truncate">{match.produto_nome}</span>
          </p>
          <p className="mt-0.5 truncate text-xs text-zinc-500">
            {match.chat_name || 'Grupo desconhecido'}
          </p>
        </div>

        <div className="shrink-0 text-right">
          <p className="font-mono text-sm font-medium text-amber-400">
            {formatPreco(match.preco_encontrado)}
          </p>
          <p className={`font-mono text-xs ${scoreColor(match.score)}`}>
            {formatScore(match.score)}
          </p>
        </div>

        <ReadToggle match={match} className="-mr-1 -mt-1 shrink-0" />
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        {match.matched_keyword && (
          <Badge
            variant="outline"
            className="border-zinc-700 text-[11px] text-zinc-400"
          >
            {match.matched_keyword}
          </Badge>
        )}
        {st === 'sent' && (
          <Badge
            variant="outline"
            className="border-green-500/30 text-[11px] text-green-400"
          >
            Alertado
          </Badge>
        )}
        {st === 'failed' && (
          <Badge
            variant="outline"
            className="border-red-500/40 bg-red-500/10 text-[11px] text-red-400"
          >
            Alerta falhou
          </Badge>
        )}
        {match.preco_ok === false && (
          <Badge
            variant="outline"
            className="border-amber-500/30 text-[11px] text-amber-400"
          >
            Acima do máx.
          </Badge>
        )}
        {match.llm_validado && !match.llm_aprovado && (
          <Badge
            variant="outline"
            className="border-red-500/30 text-[11px] text-red-400"
          >
            Reprovado IA
          </Badge>
        )}
        <span className="ml-auto text-[11px] text-zinc-500">
          {formatRelativeDateTime(match.created_at)}
        </span>
      </div>
    </div>
  )
}
