import { useState } from 'react'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useCreateUser } from '@/hooks/useUsers'
import type { Papel } from '@/types'

const PAPEIS = [
  { value: 'viewer', label: 'Leitura — vê promoções e interesses' },
  { value: 'owner', label: 'Administrador — mexe em tudo' },
]

export function UserFormDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[calc(100%-2rem)] sm:max-w-lg">
        {open && <UserForm onDone={() => onOpenChange(false)} />}
      </DialogContent>
    </Dialog>
  )
}

function UserForm({ onDone }: { onDone: () => void }) {
  const criar = useCreateUser()
  const [email, setEmail] = useState('')
  const [nome, setNome] = useState('')
  const [papel, setPapel] = useState<Papel>('viewer')
  const [senha, setSenha] = useState('')

  const podeEnviar = Boolean(email.trim() && nome.trim() && senha)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!podeEnviar) return
    criar.mutate(
      { email: email.trim(), nome: nome.trim(), papel, senha },
      { onSuccess: onDone },
    )
  }

  return (
    <form onSubmit={handleSubmit}>
      <DialogHeader>
        <DialogTitle>Novo acesso</DialogTitle>
        <DialogDescription>
          Defina uma senha provisória e passe para a pessoa. Ela será obrigada a
          trocá-la no primeiro acesso.
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-4 py-4">
        <div className="space-y-2">
          <Label htmlFor="novo-nome">Nome</Label>
          <Input
            id="novo-nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            autoFocus
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="novo-email">E-mail</Label>
          <Input
            id="novo-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="pessoa@exemplo.com"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="novo-papel">Permissão</Label>
          <Select
            items={PAPEIS}
            value={papel}
            onValueChange={(v) => setPapel(v as Papel)}
          >
            <SelectTrigger id="novo-papel" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PAPEIS.map((p) => (
                <SelectItem key={p.value} value={p.value}>
                  {p.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="nova-senha">Senha provisória</Label>
          <Input
            id="nova-senha"
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            autoComplete="new-password"
          />
        </div>
      </div>

      <DialogFooter showCloseButton>
        <Button type="submit" disabled={criar.isPending || !podeEnviar}>
          {criar.isPending ? 'Criando…' : 'Criar acesso'}
        </Button>
      </DialogFooter>
    </form>
  )
}
