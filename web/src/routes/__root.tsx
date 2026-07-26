import { useEffect, useState } from 'react'
import { Outlet, createRootRoute, useRouter } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import { Toaster } from '@/components/ui/sonner'
import { Sidebar, MobileNav } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  const [navOpen, setNavOpen] = useState(false)
  const router = useRouter()

  // Os itens do menu já fecham o drawer no clique; isto cobre navegação que
  // não passa por eles (botão voltar/avançar do navegador). É uma inscrição
  // num sistema externo — não um setState síncrono no corpo do efeito.
  useEffect(
    () => router.subscribe('onResolved', () => setNavOpen(false)),
    [router],
  )

  return (
    <div className="flex min-h-screen bg-zinc-900 text-zinc-100">
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
