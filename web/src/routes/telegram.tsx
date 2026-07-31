import { createFileRoute } from '@tanstack/react-router'
import { Send } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LoginCard } from '@/components/features/auth/LoginCard'

/** Conexão da conta do Telegram que o robô escuta. Restrita a `owner` no gate
 *  do __root e no backend: aqui se digita a senha de duas etapas da conta
 *  pessoal do dono. */
export const Route = createFileRoute('/telegram')({
  component: TelegramPage,
})

function TelegramPage() {
  return (
    <div className="mx-auto w-full max-w-sm space-y-6 py-6">
      <div className="flex flex-col items-center gap-3 text-center">
        <span className="flex size-11 items-center justify-center rounded-2xl bg-sky-500/15 text-sky-400">
          <Send className="size-5" />
        </span>
        <div>
          <h1 className="text-lg font-semibold text-zinc-100">
            Conectar o Telegram
          </h1>
          <p className="text-[13px] leading-relaxed text-zinc-500">
            É esta conta que lê os grupos e alimenta o feed de promoções.
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
