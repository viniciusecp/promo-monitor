import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import type { MatchDetailResponse } from '@/types'

interface Props {
  matches: MatchDetailResponse[] | undefined
  isLoading: boolean
}

function scoreColor(score: number) {
  if (score >= 0.8) return 'text-green-400'
  if (score >= 0.6) return 'text-amber-400'
  return 'text-zinc-400'
}

function formatScore(score: number) {
  return `${Math.round(score * 100)}%`
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('pt-BR')
}

function MatchDetailModal({
  match,
  open,
  onOpenChange,
}: {
  match: MatchDetailResponse | null
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg border border-zinc-800 bg-zinc-950 text-zinc-100">
        <DialogTitle className="text-base font-medium text-zinc-100">
          {match?.produto_nome}
        </DialogTitle>
        <div className="space-y-3 text-sm">
          <div className="flex flex-wrap gap-4">
            <div>
              <span className="text-zinc-400">Preço: </span>
              <span className="font-mono text-zinc-100">
                {match?.preco_encontrado
                  ? `R$ ${match.preco_encontrado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                  : '—'}
              </span>
            </div>
            <div>
              <span className="text-zinc-400">Score: </span>
              <span className={`font-mono font-medium ${scoreColor(match?.score ?? 0)}`}>
                {match ? formatScore(match.score) : '—'}
              </span>
            </div>
            <div>
              <span className="text-zinc-400">Grupo: </span>
              <span className="text-zinc-100">{match?.chat_name || '—'}</span>
            </div>
            <div>
              <span className="text-zinc-400">Palavra: </span>
              <span className="text-zinc-100">{match?.matched_keyword || '—'}</span>
            </div>
            <div>
              <span className="text-zinc-400">Registrado: </span>
              <span className="text-zinc-100">
                {match ? formatDate(match.created_at) : '—'}
              </span>
            </div>
          </div>
          <div className="rounded-lg bg-zinc-900 p-3">
            <p className="whitespace-pre-wrap text-zinc-200">
              {match?.message_text || '—'}
            </p>
          </div>
          {match?.llm_motivo && (
            match.llm_aprovado ? (
              <div className="rounded-lg border border-zinc-800 p-3">
                <p className="mb-1 text-xs font-medium text-zinc-400">Validação da IA</p>
                <p className="whitespace-pre-wrap text-zinc-200">{match.llm_motivo}</p>
              </div>
            ) : (
              <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-3">
                <p className="mb-1 text-xs font-medium text-red-400">Reprovado pela IA</p>
                <p className="whitespace-pre-wrap text-zinc-200">{match.llm_motivo}</p>
              </div>
            )
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

export function MatchTable({ matches, isLoading }: Props) {
  const [selectedMatch, setSelectedMatch] = useState<MatchDetailResponse | null>(null)

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-lg bg-zinc-800" />
        ))}
      </div>
    )
  }

  if (!matches?.length) {
    return (
      <p className="py-8 text-center text-sm text-zinc-500">
        Nenhum match encontrado.
      </p>
    )
  }

  return (
    <>
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
          </TableRow>
        </TableHeader>
        <TableBody>
          {matches.map((match) => (
            <TableRow
              key={match.id}
              className="cursor-pointer border-zinc-800 hover:bg-zinc-900"
              onClick={() => setSelectedMatch(match)}
            >
              <TableCell className="font-medium text-zinc-200">
                {match.produto_nome}
              </TableCell>
              <TableCell className="font-mono text-zinc-300">
                {match.preco_encontrado
                  ? `R$ ${match.preco_encontrado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                  : '—'}
              </TableCell>
              <TableCell>
                <span className={`font-mono text-sm font-medium ${scoreColor(match.score)}`}>
                  {formatScore(match.score)}
                </span>
              </TableCell>
              <TableCell>
                {match.matched_keyword
                  ? <Badge variant="outline" className="border-zinc-700 text-zinc-300">{match.matched_keyword}</Badge>
                  : <span className="text-zinc-600">—</span>
                }
              </TableCell>
              <TableCell className="max-w-40 truncate text-zinc-400">
                {match.chat_name || '—'}
              </TableCell>
              <TableCell className="whitespace-nowrap text-xs text-zinc-400">
                {formatDate(match.created_at)}
              </TableCell>
              <TableCell>
                {match.alerted
                  ? <Badge variant="outline" className="border-green-500/30 text-green-400">Sim</Badge>
                  : <Badge variant="secondary" className="text-zinc-500">Não</Badge>
                }
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <MatchDetailModal
        match={selectedMatch}
        open={selectedMatch !== null}
        onOpenChange={(open) => { if (!open) setSelectedMatch(null) }}
      />
    </>
  )
}
