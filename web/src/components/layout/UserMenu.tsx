import { LogOut, ShieldCheck } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useLogout, useSession } from '@/hooks/useSession'

export function UserMenu({ collapsed = false }: { collapsed?: boolean }) {
  const { data: user } = useSession()
  const logout = useLogout()

  if (!user) return null

  const inicial = (user.nome || user.email).charAt(0).toUpperCase()
  const papelLabel = user.papel === 'owner' ? 'Administrador' : 'Leitura'

  if (collapsed) {
    return (
      <div className="border-t border-zinc-800 px-2 py-2">
        <button
          type="button"
          onClick={() => logout.mutate()}
          disabled={logout.isPending}
          aria-label="Sair"
          title={`${user.nome} (${papelLabel}) — sair`}
          className="flex w-full items-center justify-center rounded-lg py-2 text-zinc-400 transition-colors hover:bg-zinc-800/50 hover:text-zinc-200"
        >
          <LogOut className="size-4 shrink-0" />
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-2 border-t border-zinc-800 px-3 py-3">
      <div className="flex items-center gap-2.5">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-amber-400/15 text-[13px] font-semibold text-amber-400">
          {inicial}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-medium text-zinc-200">
            {user.nome}
          </p>
          <p className="truncate text-[11px] text-zinc-500" title={user.email}>
            {user.email}
          </p>
        </div>
        {user.papel === 'owner' && (
          <ShieldCheck
            className="size-3.5 shrink-0 text-zinc-600"
            aria-label={papelLabel}
          />
        )}
      </div>

      <button
        type="button"
        onClick={() => logout.mutate()}
        disabled={logout.isPending}
        className={cn(
          'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-zinc-400 transition-colors',
          'hover:bg-zinc-800/50 hover:text-zinc-200 disabled:opacity-60',
        )}
      >
        <LogOut className="size-4 shrink-0" />
        <span className="truncate">{logout.isPending ? 'Saindo…' : 'Sair'}</span>
      </button>
    </div>
  )
}
