import { Mail, MailOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useMarkRead } from '@/hooks/useMatches'
import type { MatchDetailResponse } from '@/types'

export function ReadToggle({
  match,
  className,
}: {
  match: MatchDetailResponse
  className?: string
}) {
  const markRead = useMarkRead()

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      className={className}
      aria-label={match.lido ? 'Marcar como não lido' : 'Marcar como lido'}
      title={match.lido ? 'Marcar como não lido' : 'Marcar como lido'}
      onClick={(e) => {
        e.stopPropagation()
        markRead.mutate({ id: match.id, lido: !match.lido })
      }}
    >
      {match.lido ? (
        <MailOpen className="text-zinc-500" />
      ) : (
        <Mail className="text-amber-400" />
      )}
    </Button>
  )
}
