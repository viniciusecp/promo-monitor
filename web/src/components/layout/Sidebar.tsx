import { Link, useLocation } from '@tanstack/react-router'
import {
  ListChecks,
  ShoppingBag,
  MessageSquare,
  Cog,
  Percent,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { useMatchStats } from '@/hooks/useMatches'

// `/` é o feed de matches — não existe mais uma rota /matches separada
// (ela redireciona para cá).
const navItems = [
  { to: '/', label: 'Matches', icon: ListChecks, showUnread: true },
  { to: '/interests', label: 'Interesses', icon: ShoppingBag },
  { to: '/messages', label: 'Mensagens', icon: MessageSquare },
  { to: '/settings', label: 'Configurações', icon: Cog },
]

function Logo() {
  return (
    <div className="flex items-center gap-2 border-b border-zinc-800 px-5 py-4">
      <Percent className="size-5 text-amber-400" />
      <span className="text-sm font-semibold tracking-tight text-zinc-100">
        Promo Monitor
      </span>
    </div>
  )
}

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const { pathname } = useLocation()
  const { data: stats } = useMatchStats()
  const unread = stats?.nao_lidos ?? 0

  return (
    <nav className="flex-1 space-y-1 px-3 py-4">
      {navItems.map((item) => {
        const active =
          pathname === item.to ||
          (item.to !== '/' && pathname.startsWith(item.to))

        return (
          <Link
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              active
                ? 'bg-amber-400/10 text-amber-400'
                : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200',
            )}
          >
            <item.icon className="size-4 shrink-0" />
            <span className="flex-1">{item.label}</span>
            {item.showUnread && unread > 0 && (
              <span className="rounded-full bg-amber-400 px-1.5 py-0.5 text-[11px] font-semibold tabular-nums text-zinc-950">
                {unread > 99 ? '99+' : unread}
              </span>
            )}
          </Link>
        )
      })}
    </nav>
  )
}

function Footer() {
  return (
    <div className="border-t border-zinc-800 px-5 py-3">
      <p className="text-[11px] text-zinc-600">Promo Monitor v1.0</p>
    </div>
  )
}

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 hidden h-screen w-60 flex-col border-r border-zinc-800 bg-zinc-950 md:flex">
      <Logo />
      <SidebarNav />
      <Footer />
    </aside>
  )
}

export function MobileNav({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="left"
        showCloseButton={false}
        className="border-zinc-800 bg-zinc-950 p-0 md:hidden"
      >
        <SheetTitle className="sr-only">Navegação</SheetTitle>
        <Logo />
        <SidebarNav onNavigate={() => onOpenChange(false)} />
        <Footer />
      </SheetContent>
    </Sheet>
  )
}
