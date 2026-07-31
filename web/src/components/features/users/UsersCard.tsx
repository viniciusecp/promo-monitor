import { useState } from 'react'
import { KeyRound, Plus, ShieldCheck, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import {
  useDeleteUser,
  useResetUserPassword,
  useUpdateUser,
  useUsers,
} from '@/hooks/useUsers'
import { useSession } from '@/hooks/useSession'
import { formatDateTime } from '@/lib/utils'
import type { UserResponse } from '@/types'
import { UserFormDialog } from './UserFormDialog'

export function UsersCard() {
  const { data: users, isLoading } = useUsers()
  const { data: eu } = useSession()
  const [novoOpen, setNovoOpen] = useState(false)
  const [resetAlvo, setResetAlvo] = useState<UserResponse | null>(null)
  const [excluirAlvo, setExcluirAlvo] = useState<UserResponse | null>(null)

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-14 w-full" />
        <Skeleton className="h-14 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-[13px] leading-relaxed text-zinc-500">
        Não existe cadastro aberto: só quem aparece nesta lista consegue entrar.
      </p>

      <div className="divide-y divide-zinc-800/70">
        {users?.map((u) => (
          <UserRow
            key={u.id}
            user={u}
            souEu={u.id === eu?.id}
            onReset={() => setResetAlvo(u)}
            onExcluir={() => setExcluirAlvo(u)}
          />
        ))}
      </div>

      <Button variant="outline" onClick={() => setNovoOpen(true)}>
        <Plus className="size-4" />
        Novo acesso
      </Button>

      <UserFormDialog open={novoOpen} onOpenChange={setNovoOpen} />
      <ResetPasswordDialog
        user={resetAlvo}
        onOpenChange={(open) => !open && setResetAlvo(null)}
      />
      <DeleteUserDialog
        user={excluirAlvo}
        onOpenChange={(open) => !open && setExcluirAlvo(null)}
      />
    </div>
  )
}

function UserRow({
  user,
  souEu,
  onReset,
  onExcluir,
}: {
  user: UserResponse
  souEu: boolean
  onReset: () => void
  onExcluir: () => void
}) {
  const atualizar = useUpdateUser()

  return (
    <div className="flex flex-wrap items-center gap-3 py-3">
      <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-[13px] font-semibold text-zinc-300">
        {(user.nome || user.email).charAt(0).toUpperCase()}
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-[13px] font-medium text-zinc-200">
            {user.nome}
          </p>
          {souEu && (
            <Badge className="bg-zinc-700/40 text-zinc-400">você</Badge>
          )}
        </div>
        <p className="truncate text-[12px] text-zinc-500">{user.email}</p>
        <p className="text-[11px] text-zinc-600">
          {user.ultimo_login
            ? `último acesso ${formatDateTime(user.ultimo_login)}`
            : 'nunca acessou'}
          {user.trocar_senha && ' · senha provisória'}
        </p>
      </div>

      <Badge
        className={
          user.papel === 'owner'
            ? 'bg-amber-500/15 text-amber-400'
            : 'bg-zinc-700/40 text-zinc-400'
        }
      >
        {user.papel === 'owner' && <ShieldCheck className="size-3" />}
        {user.papel === 'owner' ? 'admin' : 'leitura'}
      </Badge>

      <div className="flex items-center gap-1">
        <Switch
          size="sm"
          checked={user.ativo}
          disabled={atualizar.isPending}
          onCheckedChange={(ativo) => atualizar.mutate({ id: user.id, ativo })}
          aria-label={user.ativo ? 'Desativar acesso' : 'Reativar acesso'}
          title={user.ativo ? 'Desativar acesso' : 'Reativar acesso'}
        />
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={onReset}
          aria-label="Redefinir senha"
          title="Redefinir senha"
        >
          <KeyRound className="size-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={onExcluir}
          disabled={souEu}
          aria-label="Remover acesso"
          title={souEu ? 'Você não pode remover a própria conta' : 'Remover acesso'}
        >
          <Trash2 className="size-4" />
        </Button>
      </div>
    </div>
  )
}

function ResetPasswordDialog({
  user,
  onOpenChange,
}: {
  user: UserResponse | null
  onOpenChange: (open: boolean) => void
}) {
  const redefinir = useResetUserPassword()
  const [senha, setSenha] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!user || !senha) return
    redefinir.mutate(
      { id: user.id, senha },
      {
        onSuccess: () => {
          setSenha('')
          onOpenChange(false)
        },
      },
    )
  }

  return (
    <Dialog open={Boolean(user)} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[calc(100%-2rem)] sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Redefinir senha</DialogTitle>
            <DialogDescription>
              Define uma senha provisória para <strong>{user?.nome}</strong>. As
              sessões abertas dessa pessoa caem, e ela terá que escolher uma
              senha nova ao entrar.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 py-4">
            <Label htmlFor="reset-senha">Senha provisória</Label>
            <Input
              id="reset-senha"
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              autoComplete="new-password"
              autoFocus
            />
          </div>

          <DialogFooter showCloseButton>
            <Button type="submit" disabled={redefinir.isPending || !senha}>
              {redefinir.isPending ? 'Salvando…' : 'Redefinir'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function DeleteUserDialog({
  user,
  onOpenChange,
}: {
  user: UserResponse | null
  onOpenChange: (open: boolean) => void
}) {
  const excluir = useDeleteUser()

  return (
    <Dialog open={Boolean(user)} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[calc(100%-2rem)] sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Remover acesso</DialogTitle>
          <DialogDescription>
            <strong>{user?.nome}</strong> perde o acesso ao painel imediatamente,
            inclusive nas abas já abertas. Os interesses e as promoções continuam
            salvos.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter showCloseButton>
          <Button
            variant="destructive"
            disabled={excluir.isPending}
            onClick={() =>
              user &&
              excluir.mutate(user.id, { onSuccess: () => onOpenChange(false) })
            }
          >
            {excluir.isPending ? 'Removendo…' : 'Remover'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
