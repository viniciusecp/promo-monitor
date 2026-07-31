import { Link, useLocation } from '@tanstack/react-router'
import {
  ListChecks,
  ShoppingBag,
  MessageSquare,
  Cog,
  Percent,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { useMatchStats } from '@/hooks/useMatches'
import { useSession } from '@/hooks/useSession'
import { UserMenu } from './UserMenu'

const navItems = [
  { to: '/', label: 'Matches', icon: ListChecks, showUnread: true },
  { to: '/interests', label: 'Interesses', icon: ShoppingBag },
  { to: '/messages', label: 'Mensagens', icon: MessageSquare },
  { to: '/settings', label: 'Configurações', icon: Cog, ownerOnly: true },
]

function Logo({ collapsed = false }: { collapsed?: boolean }) {
  return (
    <div
      className={cn(
        'flex h-[57px] shrink-0 items-center gap-2 border-b border-zinc-800',
        collapsed ? 'justify-center px-0' : 'px-5',
      )}
    >
      <Percent className="size-5 shrink-0 text-amber-400" />
      {!collapsed && (
        <span className="truncate text-sm font-semibold tracking-tight text-zinc-100">
          Promo Monitor
        </span>
      )}
    </div>
  )
}

function SidebarNav({
  onNavigate,
  collapsed = false,
}: {
  onNavigate?: () => void
  collapsed?: boolean
}) {
  const { pathname } = useLocation()
  const { data: stats } = useMatchStats()
  const { data: user } = useSession()
  const unread = stats?.nao_lidos ?? 0

  const items = navItems.filter(
    (item) => !item.ownerOnly || user?.papel === 'owner',
  )

  return (
    <nav className={cn('flex-1 space-y-1 py-4', collapsed ? 'px-2' : 'px-3')}>
      {items.map((item) => {
        const active =
          pathname === item.to ||
          (item.to !== '/' && pathname.startsWith(item.to))
        const badge = item.showUnread && unread > 0

        return (
          <Link
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            title={collapsed ? item.label : undefined}
            className={cn(
              'flex items-center rounded-lg py-2 text-sm font-medium transition-colors',
              collapsed ? 'justify-center px-0' : 'gap-3 px-3',
              active
                ? 'bg-amber-400/10 text-amber-400'
                : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200',
            )}
          >
            <span className="relative flex shrink-0 items-center">
              <item.icon className="size-4" />
              {collapsed && badge && (
                <span className="absolute -right-1.5 -top-1 size-2 rounded-full bg-amber-400 ring-2 ring-zinc-950" />
              )}
            </span>
            {!collapsed && (
              <>
                <span className="flex-1 truncate">{item.label}</span>
                {badge && (
                  <span className="rounded-full bg-amber-400 px-1.5 py-0.5 text-[11px] font-semibold tabular-nums text-zinc-950">
                    {unread > 99 ? '99+' : unread}
                  </span>
                )}
              </>
            )}
          </Link>
        )
      })}
    </nav>
  )
}

function CollapseToggle({
  collapsed,
  onToggle,
}: {
  collapsed: boolean
  onToggle: () => void
}) {
  const Icon = collapsed ? PanelLeftOpen : PanelLeftClose
  const label = collapsed ? 'Expandir menu' : 'Comprimir menu'

  return (
    <div
      className={cn(
        'border-t border-zinc-800 py-2',
        collapsed ? 'px-2' : 'px-3',
      )}
    >
      <button
        type="button"
        onClick={onToggle}
        aria-label={label}
        title={label}
        className={cn(
          'flex w-full items-center rounded-lg py-2 text-sm font-medium text-zinc-400 transition-colors hover:bg-zinc-800/50 hover:text-zinc-200',
          collapsed ? 'justify-center px-0' : 'gap-3 px-3',
        )}
      >
        <Icon className="size-4 shrink-0" />
        {!collapsed && <span className="truncate">Comprimir</span>}
      </button>
    </div>
  )
}

export function Sidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean
  onToggle: () => void
}) {
  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 hidden h-screen flex-col border-r border-zinc-800 bg-zinc-950 transition-[width] duration-200 md:flex',
        collapsed ? 'w-16' : 'w-60',
      )}
    >
      <Logo collapsed={collapsed} />
      <SidebarNav collapsed={collapsed} />
      <UserMenu collapsed={collapsed} />
      <CollapseToggle collapsed={collapsed} onToggle={onToggle} />
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
        <UserMenu />
      </SheetContent>
    </Sheet>
  )
}
