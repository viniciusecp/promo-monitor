import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // O feed se atualiza no foco da aba (ver useMatches), então este
      // staleTime é o amortecedor: alternar de aba rapidinho não vira uma
      // cascata de requests, mas voltar depois de qualquer ausência real sim.
      staleTime: 15_000,
      retry: 1,
    },
  },
})

const router = createRouter({ routeTree, context: { queryClient } })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <ReactQueryDevtools />
    </QueryClientProvider>
  </StrictMode>,
)
