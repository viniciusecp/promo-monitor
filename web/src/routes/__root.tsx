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
import { useSession } from '@/hooks/useSession'
import { useSidebarCollapsed } from '@/hooks/useSidebarCollapsed'

export const Route = createRootRoute({
  component: RootLayout,
})

const SHELL = 'flex min-h-screen bg-zinc-900 text-zinc-100'

/** Rotas que se desenham sozinhas, fora do shell com sidebar. */
const BARE_ROUTES = ['/login']

/** `/settings` entra aqui porque é de onde se administra usuários e se corrige
 *  o token do bot — prender o dono na tela de conexão o deixaria sem fazer as
 *  duas coisas justamente quando algo quebrou. */
const SEM_TELEGRAM_OK = ['/telegram', '/trocar-senha', '/settings']

function RootLayout() {
  const [navOpen, setNavOpen] = useState(false)
  const { collapsed, toggle } = useSidebarCollapsed()
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
  //
  // Dois estágios nesta ordem: sessão do painel, depois conexão do Telegram —
  // um anônimo não pode nem saber se o Telegram está conectado.
  const {
    data: user,
    isLoading: sessionLoading,
    isError: sessionError,
    refetch: refetchSession,
  } = useSession()

  const onLogin = pathname === '/login'
  const logado = Boolean(user)

  // `enabled`: a rota exige sessão, e sem isso a tela de login dispararia um
  // 401 a cada 3s.
  const { data: auth } = useAuthStatus(logado)

  if (sessionLoading) {
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
  // a própria tela de login. `useSession` já traduz 401 para `null`, então cair
  // aqui significa mesmo falha de rede.
  if (sessionError) {
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
              e se o painel consegue alcançá-lo em{' '}
              <code className="text-zinc-400">/api</code>.
            </p>
          </div>
          <Button onClick={() => refetchSession()}>Tentar de novo</Button>
        </div>
        <Toaster richColors position="top-right" />
      </div>
    )
  }

  if (!logado && !onLogin) return <Navigate to="/login" replace />
  if (logado && onLogin) return <Navigate to="/" replace />

  // Senha definida por outra pessoa: trocar é o único caminho para frente.
  if (logado && user!.trocar_senha && pathname !== '/trocar-senha') {
    return <Navigate to="/trocar-senha" replace />
  }

  // Só o owner vai para a tela de conexão: um viewer não tem permissão para
  // completá-la, então lá seria um beco sem saída. Ele fica no feed com o
  // histórico, e o aviso aparece no Header.
  const telegramConectado = auth?.status === 'authenticated'
  const precisaConectar =
    logado && user!.papel === 'owner' && auth && !telegramConectado

  if (precisaConectar && !SEM_TELEGRAM_OK.includes(pathname)) {
    return <Navigate to="/telegram" replace />
  }

  if (BARE_ROUTES.includes(pathname)) {
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
      <Sidebar collapsed={collapsed} onToggle={toggle} />
      <MobileNav open={navOpen} onOpenChange={setNavOpen} />

      {/* min-w-0 é obrigatório: `flex-1` deixa min-width:auto, e aí o
          overflow-x-auto interno das tabelas nunca ativa — elas empurram o
          container além da viewport em vez de rolar sozinhas.
          A margem acompanha a largura da sidebar (fixed, fora do fluxo). */}
      <div
        className={`flex min-w-0 flex-1 flex-col transition-[margin] duration-200 ${
          collapsed ? 'md:ml-16' : 'md:ml-60'
        }`}
      >
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
