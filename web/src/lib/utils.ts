import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const hasTz = /[zZ]|[+-]\d{2}:?\d{2}$/.test(value)
  const iso = hasTz ? value : value.replace(' ', 'T') + 'Z'
  return new Date(iso).toLocaleString('pt-BR')
}
