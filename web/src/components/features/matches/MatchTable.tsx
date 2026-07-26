import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'
import { formatDateTime } from '@/lib/utils'
import { alertState, formatPreco, formatScore, scoreColor } from '@/lib/match'
import { ReadToggle } from './ReadToggle'
import type { MatchDetailResponse } from '@/types'

function AlertBadge({ match }: { match: MatchDetailResponse }) {
  const st = alertState(match)
  if (st === 'sent') {
    return (
      <Badge variant="outline" className="border-green-500/30 text-green-400">
        Sim
      </Badge>
    )
  }
  if (st === 'failed') {
    return (
      <Badge
        variant="outline"
        className="border-red-500/40 bg-red-500/10 text-red-400"
      >
        Falhou
      </Badge>
    )
  }
  return (
    <Badge variant="secondary" className="text-zinc-500">
      Não
    </Badge>
  )
}

export function MatchTable({
  matches,
  onSelect,
}: {
  matches: MatchDetailResponse[]
  onSelect: (match: MatchDetailResponse) => void
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="border-zinc-800">
          <TableHead className="text-zinc-400">Produto</TableHead>
          <TableHead className="text-zinc-400">Preço</TableHead>
          <TableHead className="text-zinc-400">Score</TableHead>
          <TableHead className="text-zinc-400">Palavra</TableHead>
          <TableHead className="text-zinc-400">Grupo</TableHead>
          <TableHead className="text-zinc-400">Registrado</TableHead>
          <TableHead className="text-zinc-400">Alertado</TableHead>
          <TableHead className="w-10" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {matches.map((match) => (
          <TableRow
            key={match.id}
            role="button"
            tabIndex={0}
            className={cn(
              'cursor-pointer border-zinc-800 hover:bg-zinc-900',
              !match.lido && 'border-l-2 border-l-amber-400 bg-amber-400/[0.03]',
            )}
            onClick={() => onSelect(match)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onSelect(match)
              }
            }}
          >
            <TableCell
              className={cn(
                'font-medium',
                match.lido ? 'text-zinc-400' : 'text-zinc-100',
              )}
            >
              <span className="flex items-center gap-2">
                {!match.lido && (
                  <span
                    aria-hidden
                    className="size-1.5 shrink-0 rounded-full bg-amber-400"
                  />
                )}
                {match.produto_nome}
              </span>
            </TableCell>
            <TableCell className="font-mono text-zinc-300">
              {formatPreco(match.preco_encontrado)}
            </TableCell>
            <TableCell>
              <span
                className={`font-mono text-sm font-medium ${scoreColor(match.score)}`}
              >
                {formatScore(match.score)}
              </span>
            </TableCell>
            <TableCell>
              {match.matched_keyword ? (
                <Badge variant="outline" className="border-zinc-700 text-zinc-300">
                  {match.matched_keyword}
                </Badge>
              ) : (
                <span className="text-zinc-600">—</span>
              )}
            </TableCell>
            <TableCell className="max-w-32 truncate text-zinc-400 md:max-w-40">
              {match.chat_name || '—'}
            </TableCell>
            <TableCell className="whitespace-nowrap text-xs text-zinc-400">
              {formatDateTime(match.created_at)}
            </TableCell>
            <TableCell>
              <AlertBadge match={match} />
            </TableCell>
            <TableCell>
              <ReadToggle match={match} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
