import { useLocation } from '@tanstack/react-router'

const titles: Record<string, string> = {
  '/': 'Dashboard',
  '/interests': 'Interesses',
  '/interests/new': 'Novo Interesse',
  '/matches': 'Matches',
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

export function Header() {
  const { pathname } = useLocation()
  const title = findTitle(pathname)

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center border-b border-zinc-800 bg-zinc-950/80 px-6 backdrop-blur-sm">
      <h1 className="text-base font-semibold text-zinc-100">{title}</h1>
    </header>
  )
}
