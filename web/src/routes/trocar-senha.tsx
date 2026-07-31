import { useState } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { KeyRound } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert } from '@/components/ui/alert'
import { AuthErrorAlert } from '@/components/features/auth/AuthErrorAlert'
import { useChangePassword, useSession } from '@/hooks/useSession'
import { ApiError } from '@/lib/api'

export const Route = createFileRoute('/trocar-senha')({
  component: TrocarSenhaPage,
})

function TrocarSenhaPage() {
  const { data: user } = useSession()
  const navigate = useNavigate()
  const trocar = useChangePassword()

  const [atual, setAtual] = useState('')
  const [nova, setNova] = useState('')
  const [confirma, setConfirma] = useState('')

  const obrigatoria = user?.trocar_senha === true
  const naoConfere = confirma.length > 0 && nova !== confirma
  const podeEnviar = Boolean(atual && nova && nova === confirma)

  const erro = trocar.error instanceof ApiError ? trocar.error : null

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!podeEnviar) return
    trocar.mutate(
      { senha_atual: atual, senha_nova: nova },
      {
        onSuccess: () => navigate({ to: '/' }),
        onError: () => {
          setAtual('')
          setNova('')
          setConfirma('')
        },
      },
    )
  }

  return (
    <div className="mx-auto w-full max-w-sm space-y-6 py-6">
      <div className="flex flex-col items-center gap-3 text-center">
        <span className="flex size-11 items-center justify-center rounded-2xl bg-amber-500/15 text-amber-400">
          <KeyRound className="size-5" />
        </span>
        <div>
          <h1 className="text-lg font-semibold text-zinc-100">Trocar a senha</h1>
          <p className="text-[13px] text-zinc-500">{user?.email}</p>
        </div>
      </div>

      <Card className="border-zinc-800 bg-zinc-950 text-zinc-100">
        {obrigatoria && (
          <CardHeader>
            <Alert variant="warning">
              <KeyRound />
              <span>
                Sua senha atual foi definida por outra pessoa. Escolha uma que só
                você conheça para continuar.
              </span>
            </Alert>
          </CardHeader>
        )}
        {!obrigatoria && (
          <CardHeader>
            <CardTitle className="text-sm font-medium text-zinc-200">
              Nova senha
            </CardTitle>
          </CardHeader>
        )}
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="atual">Senha atual</Label>
              <Input
                id="atual"
                type="password"
                value={atual}
                onChange={(e) => setAtual(e.target.value)}
                autoComplete="current-password"
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="nova">Nova senha</Label>
              <Input
                id="nova"
                type="password"
                value={nova}
                onChange={(e) => setNova(e.target.value)}
                autoComplete="new-password"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirma">Repita a nova senha</Label>
              <Input
                id="confirma"
                type="password"
                value={confirma}
                onChange={(e) => setConfirma(e.target.value)}
                autoComplete="new-password"
              />
              {naoConfere && (
                <p className="text-[13px] text-red-400">As senhas não conferem.</p>
              )}
            </div>

            <AuthErrorAlert code={erro?.code} fallback={erro?.detailMessage} />

            <Button
              type="submit"
              disabled={trocar.isPending || !podeEnviar}
              className="w-full"
            >
              {trocar.isPending ? 'Salvando…' : 'Salvar nova senha'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
