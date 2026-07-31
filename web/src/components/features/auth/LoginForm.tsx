import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useLogin } from '@/hooks/useSession'
import { ApiError } from '@/lib/api'
import { AuthErrorAlert } from './AuthErrorAlert'
import { formatCountdown, useCountdown } from './useCountdown'

export function LoginForm() {
  const login = useLogin()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')

  const erro = login.error instanceof ApiError ? login.error : null
  const bloqueio = useCountdown(
    erro?.code === 'too_many_attempts' ? erro.retryAfter : null,
  )
  const bloqueado = bloqueio > 0

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim() || !senha || bloqueado) return
    login.mutate(
      { email: email.trim(), senha },
      { onError: () => setSenha('') },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="space-y-2">
        <Label htmlFor="email">E-mail</Label>
        <Input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="username"
          autoFocus
          placeholder="voce@exemplo.com"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="senha">Senha</Label>
        <Input
          id="senha"
          type="password"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          autoComplete="current-password"
        />
      </div>

      <AuthErrorAlert code={erro?.code} fallback={erro?.detailMessage} />

      <Button
        type="submit"
        disabled={login.isPending || bloqueado || !email.trim() || !senha}
        className="w-full"
      >
        {login.isPending
          ? 'Entrando…'
          : bloqueado
            ? `Aguarde ${formatCountdown(bloqueio)}`
            : 'Entrar'}
      </Button>

      <p className="text-center text-[13px] leading-relaxed text-zinc-500">
        Não há cadastro aberto. Peça o acesso a quem administra o painel.
      </p>
    </form>
  )
}
