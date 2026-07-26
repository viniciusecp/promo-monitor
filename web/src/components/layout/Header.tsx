import { useLocation } from '@tanstack/react-router'
import { Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useMatchStats } from '@/hooks/useMatches'

const titles: Record<string, string> = {
  '/': 'Matches',
  '/interests': 'Interesses',
  '/interests/new': 'Novo Interesse',
  '/messages': 'Mensagens',
  '/settings': 'Configurações',
}

function findTitle(pathname: string) {
  if (titles[pathname]) return titles[pathname]
  if (pathname.startsWith('/interests/') && pathname.endsWith('/edit')) {
    return 'Editar Interesse'
  }
  return 'Promo Monitor'
}

export function Header({ onMenuClick }: { onMenuClick: () => void }) {
  const { pathname } = useLocation()
  const { data: stats } = useMatchStats()
  const hasUnread = (stats?.nao_lidos ?? 0) > 0

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-zinc-800 bg-zinc-950/80 px-4 backdrop-blur-sm md:px-6">
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onMenuClick}
        aria-label="Abrir menu"
        className="relative shrink-0 md:hidden"
      >
        <Menu />
        {/* No mobile o badge da sidebar fica escondido atrás do drawer, então o
            sinal de "tem coisa nova" precisa aparecer no próprio gatilho. */}
        {hasUnread && (
          <span className="absolute right-1 top-1 size-1.5 rounded-full bg-amber-400" />
        )}
      </Button>

      <h1 className="truncate text-base font-semibold text-zinc-100">
        {findTitle(pathname)}
      </h1>
    </header>
  )
}
