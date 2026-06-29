import { Link } from '@tanstack/react-router'
import { Pencil, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import type { InterestResponse } from '@/types'

interface Props {
  interests: InterestResponse[] | undefined
  isLoading: boolean
  onToggle: (id: number, ativo: boolean) => void
  onDelete: (interest: InterestResponse) => void
}

export function InterestTable({ interests, isLoading, onToggle, onDelete }: Props) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-lg bg-zinc-800" />
        ))}
      </div>
    )
  }

  if (!interests?.length) {
    return (
      <p className="py-8 text-center text-sm text-zinc-500">
        Nenhum interesse cadastrado ainda.
      </p>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow className="border-zinc-800">
          <TableHead className="text-zinc-400">Produto</TableHead>
          <TableHead className="text-zinc-400">Preço Máx.</TableHead>
          <TableHead className="text-zinc-400">Palavras-chave</TableHead>
          <TableHead className="text-zinc-400">Ativo</TableHead>
          <TableHead className="w-24 text-zinc-400">Ações</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {interests.map((item) => (
          <TableRow key={item.id} className="border-zinc-800">
            <TableCell className="font-medium text-zinc-200">
              {item.nome_produto}
            </TableCell>
            <TableCell className="text-zinc-300">
              {item.preco_maximo
                ? `R$ ${item.preco_maximo.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                : '—'}
            </TableCell>
            <TableCell>
              <div className="flex flex-wrap gap-1">
                {item.palavras_chave.slice(0, 3).map((kw) => (
                  <Badge key={kw} variant="secondary" className="text-[11px]">
                    {kw}
                  </Badge>
                ))}
                {item.palavras_chave.length > 3 && (
                  <span className="text-[11px] text-zinc-500">
                    +{item.palavras_chave.length - 3}
                  </span>
                )}
              </div>
            </TableCell>
            <TableCell>
              <Switch
                size="sm"
                checked={item.ativo}
                onCheckedChange={(checked) => onToggle(item.id, checked)}
              />
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-1">
                <Link to="/interests/$interestId/edit" params={{ interestId: String(item.id) }}>
                  <Button variant="ghost" size="icon-xs">
                    <Pencil className="size-3.5" />
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  size="icon-xs"
                  onClick={() => onDelete(item)}
                >
                  <Trash2 className="size-3.5 text-red-400" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
