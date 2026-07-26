import { useState } from 'react'
import { SlidersHorizontal, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { useMatchChats } from '@/hooks/useMatches'
import { DEFAULT_MATCH_FILTERS } from '@/types'
import type {
  MatchFilters,
  MatchOrderBy,
  MatchOrderDir,
  MatchPeriod,
  MatchStatus,
} from '@/types'

// Sentinela para "sem filtro" nos Selects. Nunca usar value="" — no base-ui
// isso não lança (como lançaria no Radix) mas sombreia o placeholder de vez.
const TODOS = 'todos'

const PERIODOS: { value: MatchPeriod; label: string }[] = [
  { value: 'hoje', label: 'Hoje' },
  { value: '7d', label: '7 dias' },
  { value: '30d', label: '30 dias' },
  { value: 'tudo', label: 'Tudo' },
]

const ORDENACOES: {
  value: `${MatchOrderBy}:${MatchOrderDir}`
  label: string
}[] = [
  { value: 'data:desc', label: 'Mais recentes' },
  { value: 'data:asc', label: 'Mais antigos' },
  { value: 'preco:asc', label: 'Menor preço' },
  { value: 'preco:desc', label: 'Maior preço' },
  { value: 'score:desc', label: 'Maior score' },
]

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <Button
      variant={active ? 'default' : 'outline'}
      size="sm"
      onClick={onClick}
      className="shrink-0"
    >
      {children}
    </Button>
  )
}

/** Quantos filtros "avançados" estão ativos — vira badge no botão do mobile. */
function countAdvanced(filters: MatchFilters) {
  let n = 0
  if (filters.chat_id !== undefined) n++
  if (filters.preco_min !== undefined) n++
  if (filters.preco_max !== undefined) n++
  if (
    filters.order_by !== DEFAULT_MATCH_FILTERS.order_by ||
    filters.order_dir !== DEFAULT_MATCH_FILTERS.order_dir
  )
    n++
  return n
}

function toNumberOrUndefined(value: string) {
  if (value.trim() === '') return undefined
  const n = Number(value)
  return Number.isFinite(n) ? n : undefined
}

export function MatchFilterBar({
  filters,
  onChange,
}: {
  filters: MatchFilters
  onChange: (filters: MatchFilters) => void
}) {
  const [sheetOpen, setSheetOpen] = useState(false)
  const { data: chats } = useMatchChats()

  const set = (patch: Partial<MatchFilters>) => onChange({ ...filters, ...patch })

  const toggleStatus = (status: MatchStatus) =>
    set({
      status: filters.status.includes(status)
        ? filters.status.filter((s) => s !== status)
        : [...filters.status, status],
    })

  const advancedCount = countAdvanced(filters)

  // O base-ui só resolve rótulo em vez do valor cru no <SelectValue> quando o
  // Root recebe `items`. Sem isso o trigger mostraria "todos" e "data:desc".
  const chatItems = [
    { value: TODOS, label: 'Todos os grupos' },
    ...(chats ?? []).map((c) => ({
      value: String(c.chat_id),
      label: `${c.chat_name || `chat-${c.chat_id}`} (${c.total})`,
    })),
  ]

  // Período + status são as interações mais frequentes e ficam sempre a um
  // toque. Grupo/preço/ordenação são set-and-forget e vão para o sheet no
  // mobile.
  const chipsPrincipais = (
    <>
      {PERIODOS.map((p) => (
        <Chip
          key={p.value}
          active={filters.periodo === p.value}
          onClick={() => set({ periodo: p.value })}
        >
          {p.label}
        </Chip>
      ))}

      <span aria-hidden className="mx-1 h-5 w-px shrink-0 self-center bg-zinc-800" />

      <Chip
        active={filters.nao_lidos}
        onClick={() => set({ nao_lidos: !filters.nao_lidos })}
      >
        Não lidos
      </Chip>
      <Chip
        active={filters.status.includes('alertado')}
        onClick={() => toggleStatus('alertado')}
      >
        Alertados
      </Chip>
      <Chip
        active={filters.status.includes('reprovado')}
        onClick={() => toggleStatus('reprovado')}
      >
        Reprovados IA
      </Chip>
    </>
  )

  const camposAvancados = (
    <>
      <div className="space-y-1.5">
        <Label className="text-xs text-zinc-400">Grupo</Label>
        <Select
          items={chatItems}
          value={filters.chat_id !== undefined ? String(filters.chat_id) : TODOS}
          onValueChange={(v) =>
            set({ chat_id: v === TODOS ? undefined : Number(v) })
          }
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Todos os grupos" />
          </SelectTrigger>
          <SelectContent>
            {chatItems.map((item) => (
              <SelectItem key={item.value} value={item.value}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="preco_min" className="text-xs text-zinc-400">
            Preço mín.
          </Label>
          <Input
            id="preco_min"
            type="number"
            min={0}
            inputMode="decimal"
            placeholder="0"
            value={filters.preco_min ?? ''}
            onChange={(e) =>
              set({ preco_min: toNumberOrUndefined(e.target.value) })
            }
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="preco_max" className="text-xs text-zinc-400">
            Preço máx.
          </Label>
          <Input
            id="preco_max"
            type="number"
            min={0}
            inputMode="decimal"
            placeholder="—"
            value={filters.preco_max ?? ''}
            onChange={(e) =>
              set({ preco_max: toNumberOrUndefined(e.target.value) })
            }
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label className="text-xs text-zinc-400">Ordenar por</Label>
        <Select
          items={ORDENACOES}
          value={`${filters.order_by}:${filters.order_dir}`}
          onValueChange={(v) => {
            const [order_by, order_dir] = String(v).split(':')
            set({
              order_by: order_by as MatchOrderBy,
              order_dir: order_dir as MatchOrderDir,
            })
          }}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ORDENACOES.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </>
  )

  return (
    <div className="space-y-3">
      {/* Faixa de chips. O par -mx-4/px-4 faz ela sangrar até a borda da tela
          no mobile, sinalizando que rola. */}
      <div className="flex items-center gap-2">
        <div className="-mx-4 flex flex-1 gap-2 overflow-x-auto px-4 [scrollbar-width:none] md:mx-0 md:flex-wrap md:px-0 [&::-webkit-scrollbar]:hidden">
          {chipsPrincipais}
        </div>

        <Button
          variant="outline"
          size="sm"
          className="shrink-0 md:hidden"
          onClick={() => setSheetOpen(true)}
        >
          <SlidersHorizontal />
          Filtros
          {advancedCount > 0 && (
            <span className="ml-1 rounded-full bg-amber-400 px-1.5 text-[11px] font-semibold text-zinc-950">
              {advancedCount}
            </span>
          )}
        </Button>
      </div>

      {/* Desktop: os avançados ficam inline. */}
      <div className="hidden items-end gap-3 md:flex md:flex-wrap [&>*]:min-w-44">
        {camposAvancados}
        {(advancedCount > 0 || filters.nao_lidos || filters.status.length > 0) && (
          <Button
            variant="ghost"
            size="sm"
            className="min-w-0"
            onClick={() => onChange(DEFAULT_MATCH_FILTERS)}
          >
            <X />
            Limpar
          </Button>
        )}
      </div>

      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent
          side="bottom"
          className="border-zinc-800 bg-zinc-950 md:hidden"
        >
          <SheetHeader>
            <SheetTitle className="text-zinc-100">Filtros</SheetTitle>
          </SheetHeader>
          <div className="space-y-4 overflow-y-auto px-4">{camposAvancados}</div>
          <SheetFooter className="flex-row">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => onChange(DEFAULT_MATCH_FILTERS)}
            >
              Limpar
            </Button>
            <Button className="flex-1" onClick={() => setSheetOpen(false)}>
              Aplicar
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  )
}
