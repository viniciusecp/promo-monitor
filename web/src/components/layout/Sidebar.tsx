import { Link, useLocation } from '@tanstack/react-router'
import {
  LayoutDashboard,
  ShoppingBag,
  ListChecks,
  MessageSquare,
  Cog,
  Percent,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/interests', label: 'Interesses', icon: ShoppingBag },
  { to: '/matches', label: 'Matches', icon: ListChecks },
  { to: '/messages', label: 'Mensagens', icon: MessageSquare },
  { to: '/settings', label: 'Configurações', icon: Cog },
]

export function Sidebar() {
  const { pathname } = useLocation()

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-60 flex-col border-r border-zinc-800 bg-zinc-950">
      <div className="flex items-center gap-2 border-b border-zinc-800 px-5 py-4">
        <Percent className="size-5 text-amber-400" />
        <span className="text-sm font-semibold tracking-tight text-zinc-100">
          Promo Monitor
        </span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const active = pathname === item.to ||
            (item.to !== '/' && pathname.startsWith(item.to))
          return (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-amber-400/10 text-amber-400'
                  : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200',
              )}
            >
              <item.icon className="size-4" />
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-zinc-800 px-5 py-3">
        <p className="text-[11px] text-zinc-600">
          Promo Monitor v1.0
        </p>
      </div>
    </aside>
  )
}
