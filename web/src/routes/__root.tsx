import { useEffect, useState } from 'react'
import {
  Navigate,
  Outlet,
  createRootRoute,
  useLocation,
  useRouter,
} from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import { ServerCrash } from 'lucide-react'
import { Toaster } from '@/components/ui/sonner'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Sidebar, MobileNav } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { useAuthStatus } from '@/hooks/useTelegramAuth'

export const Route = createRootRoute({
  component: RootLayout,
})

const SHELL = 'flex min-h-screen bg-zinc-900 text-zinc-100'

function RootLayout() {
  const [navOpen, setNavOpen] = useState(false)
  const router = useRouter()
  const { pathname } = useLocation()

  // Os itens do menu já fecham o drawer no clique; isto cobre navegação que
  // não passa por eles (botão voltar/avançar do navegador). É uma inscrição
  // num sistema externo — não um setState síncrono no corpo do efeito.
  useEffect(
    () => router.subscribe('onResolved', () => setNavOpen(false)),
    [router],
  )

  // O gate fica no componente, não em `beforeLoad`: um guard assíncrono no
  // router bloquearia toda navegação numa chamada de rede e não dá para
  // invalidar a partir das mutações de login.
  const { data: auth, isLoading, isError, refetch } = useAuthStatus()
  const onLogin = pathname === '/login'

  if (isLoading) {
    return (
      <div className={`${SHELL} items-center justify-center p-6`}>
        <div className="w-full max-w-sm space-y-3">
          <Skeleton className="h-8 w-40" />
          <Skeleton className="h-32 w-full" />
        </div>
        <Toaster richColors position="top-right" />
      </div>
    )
  }

  // Backend fora do ar não pode virar redirect para /login — daria um loop com
  // a própria tela de login, que também depende do backend.
  if (isError) {
    return (
      <div className={`${SHELL} items-center justify-center p-6`}>
        <div className="max-w-sm space-y-4 text-center">
          <span className="mx-auto flex size-11 items-center justify-center rounded-2xl bg-red-500/15 text-red-400">
            <ServerCrash className="size-5" />
          </span>
          <div className="space-y-1">
            <h1 className="text-base font-semibold text-zinc-100">
              Backend indisponível
            </h1>
            <p className="text-[13px] leading-relaxed text-zinc-500">
              Não foi possível falar com a API. Verifique se o serviço está no ar
              e se <code className="text-zinc-400">VITE_API_URL</code> aponta
              para o endereço certo.
            </p>
          </div>
          <Button onClick={() => refetch()}>Tentar de novo</Button>
        </div>
        <Toaster richColors position="top-right" />
      </div>
    )
  }

  const authenticated = auth?.status === 'authenticated'

  if (!authenticated && !onLogin) return <Navigate to="/login" replace />
  if (authenticated && onLogin) return <Navigate to="/" replace />

  if (onLogin) {
    return (
      <div className={`${SHELL} items-center justify-center p-6`}>
        <Outlet />
        <Toaster richColors position="top-right" />
        <TanStackRouterDevtools />
      </div>
    )
  }

  return (
    <div className={SHELL}>
      <Sidebar />
      <MobileNav open={navOpen} onOpenChange={setNavOpen} />

      {/* min-w-0 é obrigatório: `flex-1` deixa min-width:auto, e aí o
          overflow-x-auto interno das tabelas nunca ativa — elas empurram o
          container além da viewport em vez de rolar sozinhas. */}
      <div className="flex min-w-0 flex-1 flex-col md:ml-60">
        <Header onMenuClick={() => setNavOpen(true)} />
        <main className="flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>

      <Toaster richColors position="top-right" />
      <TanStackRouterDevtools />
    </div>
  )
}
