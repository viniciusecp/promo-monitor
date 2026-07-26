import { createFileRoute, redirect } from '@tanstack/react-router'

// O feed de matches passou a ser a rota `/`. Mantido como redirect para não
// quebrar favoritos e links antigos.
export const Route = createFileRoute('/matches/')({
  beforeLoad: () => {
    throw redirect({ to: '/' })
  },
})
