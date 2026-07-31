import { useState } from 'react'
import { Loader2, MessageCircle, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert } from '@/components/ui/alert'
import {
  useAuthStatus,
  useRequestCode,
  useSubmitCode,
  useSubmitPassword,
} from '@/hooks/useTelegramAuth'
import { ApiError } from '@/lib/api'
import { AuthErrorAlert } from './AuthErrorAlert'
import { formatCountdown, useCountdown } from './useCountdown'

function errorCodeOf(error: unknown): string | null {
  return error instanceof ApiError ? error.code : null
}

export function LoginCard() {
  const { data: auth, isLoading } = useAuthStatus()

  if (isLoading || !auth) {
    return (
      <div className="flex items-center justify-center gap-2 py-8 text-[13px] text-zinc-500">
        <Loader2 className="size-4 animate-spin" />
        Conectando ao Telegram…
      </div>
    )
  }

  if (auth.status === 'awaiting_password') return <PasswordStep />
  if (auth.status === 'awaiting_code') return <CodeStep />
  return <PhoneStep />
}

function PhoneStep() {
  const { data: auth } = useAuthStatus()
  const requestCode = useRequestCode()

  const floodSeconds =
    errorCodeOf(requestCode.error) === 'flood_wait'
      ? (requestCode.error as ApiError).retryAfter
      : auth?.error_code === 'flood_wait'
        ? auth.retry_after_seconds
        : null
  const cooldown = useCountdown(floodSeconds)
  const blocked = cooldown > 0

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <Label>Telefone da conta</Label>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 font-mono text-sm text-zinc-200">
          {auth?.phone_masked || '—'}
        </div>
        <p className="text-[13px] leading-relaxed text-zinc-500">
          Este é o número em <Code>TELEGRAM_PHONE</Code> no{' '}
          <Code>server/.env</Code>. Para trocá-lo, edite o arquivo e reinicie o
          backend.
        </p>
      </div>

      <AuthErrorAlert
        code={errorCodeOf(requestCode.error) ?? auth?.error_code}
        fallback={auth?.error_message}
      />

      <Button
        onClick={() => requestCode.mutate()}
        disabled={requestCode.isPending || blocked}
        className="w-full"
      >
        {requestCode.isPending
          ? 'Enviando…'
          : blocked
            ? `Aguarde ${formatCountdown(cooldown)}`
            : 'Enviar código'}
      </Button>

      <p className="text-center text-[13px] text-zinc-500">
        O Telegram envia o código no próprio app, na conversa “Telegram”.
      </p>
    </div>
  )
}

function CodeStep() {
  const { data: auth } = useAuthStatus()
  const submitCode = useSubmitCode()
  const requestCode = useRequestCode()
  const [code, setCode] = useState('')

  const cooldown = useCountdown(60)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (code.trim().length < 4) return
    submitCode.mutate(code.trim(), { onError: () => setCode('') })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <Alert>
        <MessageCircle />
        <span>
          Enviamos um código para <strong>{auth?.phone_masked}</strong>. Ele chega
          no app do Telegram, não por SMS.
        </span>
      </Alert>

      <div className="space-y-2">
        <Label htmlFor="code">Código de verificação</Label>
        <Input
          id="code"
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          autoFocus
          placeholder="00000"
          className="text-center font-mono text-lg tracking-[0.4em]"
        />
      </div>

      <AuthErrorAlert
        code={errorCodeOf(submitCode.error) ?? auth?.error_code}
        fallback={auth?.error_message}
      />

      <Button
        type="submit"
        disabled={submitCode.isPending || code.trim().length < 4}
        className="w-full"
      >
        {submitCode.isPending ? 'Verificando…' : 'Entrar'}
      </Button>

      <div className="text-center">
        <button
          type="button"
          onClick={() => requestCode.mutate()}
          disabled={cooldown > 0 || requestCode.isPending}
          className="text-[13px] text-zinc-500 underline underline-offset-2 hover:text-zinc-300 disabled:cursor-not-allowed disabled:no-underline disabled:hover:text-zinc-500"
        >
          {cooldown > 0
            ? `Reenviar código em ${formatCountdown(cooldown)}`
            : 'Reenviar código'}
        </button>
      </div>
    </form>
  )
}

function PasswordStep() {
  const { data: auth } = useAuthStatus()
  const submitPassword = useSubmitPassword()
  const [password, setPassword] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!password) return
    submitPassword.mutate(password, { onError: () => setPassword('') })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <Alert>
        <ShieldCheck />
        <span>
          Esta conta tem verificação em duas etapas. Digite a senha que você
          cadastrou no Telegram.
        </span>
      </Alert>

      <div className="space-y-2">
        <Label htmlFor="password">Senha de duas etapas</Label>
        <Input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          autoFocus
        />
      </div>

      <AuthErrorAlert
        code={errorCodeOf(submitPassword.error) ?? auth?.error_code}
        fallback={auth?.error_message}
      />

      <Button
        type="submit"
        disabled={submitPassword.isPending || !password}
        className="w-full"
      >
        {submitPassword.isPending ? 'Verificando…' : 'Entrar'}
      </Button>
    </form>
  )
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[12px] text-zinc-200">
      {children}
    </code>
  )
}
