import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import type { MessageResponse } from '@/types'

interface Props {
  messages: MessageResponse[] | undefined
  isLoading: boolean
}

export function MessageList({ messages, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-lg bg-zinc-800" />
        ))}
      </div>
    )
  }

  if (!messages?.length) {
    return (
      <p className="py-8 text-center text-sm text-zinc-500">
        Nenhuma mensagem encontrada.
      </p>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow className="border-zinc-800">
          <TableHead className="text-zinc-400">Grupo</TableHead>
          <TableHead className="text-zinc-400">Remetente</TableHead>
          <TableHead className="w-96 text-zinc-400">Texto</TableHead>
          <TableHead className="text-zinc-400">Data</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {messages.map((msg) => (
          <TableRow key={msg.id} className="border-zinc-800">
            <TableCell className="text-zinc-300">
              <Badge variant="secondary" className="text-[11px]">
                {msg.chat_name || `chat-${msg.chat_id}`}
              </Badge>
            </TableCell>
            <TableCell className="text-zinc-400">
              {msg.sender_name || '—'}
            </TableCell>
            <TableCell className="max-w-96 truncate text-zinc-300">
              {msg.text || '—'}
            </TableCell>
            <TableCell className="text-xs text-zinc-500">
              {msg.raw_date
                ? new Date(msg.raw_date).toLocaleString('pt-BR')
                : '—'}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
