import { useLocation } from '@tanstack/react-router'
import { Menu, PlugZap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useMatchStats } from '@/hooks/useMatches'
import { useAuthStatus } from '@/hooks/useTelegramAuth'
import { useSession } from '@/hooks/useSession'

const titles: Record<string, string> = {
  '/': 'Matches',
  '/interests': 'Interesses',
  '/interests/new': 'Novo Interesse',
  '/messages': 'Mensagens',
  '/settings': 'Configurações',
  '/telegram': 'Conectar Telegram',
  '/trocar-senha': 'Trocar a senha',
  '/login': 'Entrar',
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
  const { data: user } = useSession()
  const { data: auth } = useAuthStatus(Boolean(user))
  const hasUnread = (stats?.nao_lidos ?? 0) > 0

  const telegramOffline =
    user?.papel === 'viewer' && auth != null && auth.status !== 'authenticated'

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
        {hasUnread && (
          <span className="absolute right-1 top-1 size-1.5 rounded-full bg-amber-400" />
        )}
      </Button>

      <h1 className="truncate text-base font-semibold text-zinc-100">
        {findTitle(pathname)}
      </h1>

      {telegramOffline && (
        <span
          className="ml-auto flex shrink-0 items-center gap-1.5 rounded-full bg-amber-500/15 px-2.5 py-1 text-[12px] font-medium text-amber-400"
          title="A conta do Telegram não está conectada. Só um administrador pode reconectá-la."
        >
          <PlugZap className="size-3.5" />
          <span className="hidden sm:inline">Telegram desconectado</span>
        </span>
      )}
    </header>
  )
}
