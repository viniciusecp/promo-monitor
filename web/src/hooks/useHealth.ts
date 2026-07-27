import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { HealthResponse } from '@/types'

/**
 * Diferente do feed, este continua em polling: é indicador de vida
 * (`telegram_connected`, `worker_running`, `bot_connected`), e esses três mudam
 * sem ação do usuário. Um status que só atualiza ao voltar para a aba fica
 * verde mentindo enquanto o usuário olha para ele.
 *
 * 30s casa com o watchdog do supervisor, que é o que gera boa parte dessas
 * mudanças — polar mais rápido que ele só gera request sem nada novo para ver.
 * `refetchIntervalInBackground` fica no default (false): com a aba escondida
 * não há request nenhuma.
 */
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<HealthResponse>('/health'),
    refetchInterval: 30_000,
  })
}
