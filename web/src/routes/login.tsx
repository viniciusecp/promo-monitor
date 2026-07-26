import { createFileRoute } from '@tanstack/react-router'
import { Send } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LoginCard } from '@/components/features/auth/LoginCard'

export const Route = createFileRoute('/login')({
  component: LoginPage,
})

function LoginPage() {
  return (
    <div className="w-full max-w-sm space-y-6">
      <div className="flex flex-col items-center gap-3 text-center">
        <span className="flex size-11 items-center justify-center rounded-2xl bg-amber-500/15 text-amber-400">
          <Send className="size-5" />
        </span>
        <div>
          <h1 className="text-lg font-semibold text-zinc-100">Promo Monitor</h1>
          <p className="text-[13px] text-zinc-500">
            Conecte sua conta do Telegram para começar a monitorar.
          </p>
        </div>
      </div>

      <Card className="border-zinc-800 bg-zinc-950 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-200">
            Entrar no Telegram
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LoginCard />
        </CardContent>
      </Card>
    </div>
  )
}
