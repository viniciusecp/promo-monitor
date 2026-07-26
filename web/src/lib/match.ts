import type { MatchDetailResponse } from '@/types'

export function scoreColor(score: number) {
  if (score >= 0.8) return 'text-green-400'
  if (score >= 0.6) return 'text-amber-400'
  return 'text-zinc-400'
}

export function formatScore(score: number) {
  return `${Math.round(score * 100)}%`
}

export function formatPreco(preco: number | null | undefined) {
  if (preco === null || preco === undefined) return '—'
  return `R$ ${preco.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
}

export type AlertState = 'sent' | 'failed' | 'skipped'

/**
 * Derivação pura sobre colunas que já vêm na linha — de propósito não é um
 * campo do backend. Persistir isso exigiria mais uma coluna que poderia ficar
 * dessincronizada, sem ganho.
 *
 * `failed` é inferência ("aprovado mas não alertado"), não fato registrado:
 * não distingue "sem destino configurado" de "bot offline" de "envio falhou".
 */
export function alertState(match: MatchDetailResponse): AlertState {
  if (match.alerted) return 'sent'
  const approved = match.preco_ok !== false && match.llm_aprovado === true
  return approved ? 'failed' : 'skipped'
}

/** Data curta para o card mobile: "hoje 14:32", "ontem 09:10" ou "12/07 09:10". */
export function formatRelativeDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const hasTz = /[zZ]|[+-]\d{2}:?\d{2}$/.test(value)
  const date = new Date(hasTz ? value : value.replace(' ', 'T') + 'Z')
  if (Number.isNaN(date.getTime())) return '—'

  const hora = date.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  })

  const hoje = new Date()
  const meiaNoite = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate())
  const diffDias = Math.floor(
    (meiaNoite.getTime() - new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()) /
      86_400_000,
  )

  if (diffDias === 0) return `hoje ${hora}`
  if (diffDias === 1) return `ontem ${hora}`
  return `${date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })} ${hora}`
}
