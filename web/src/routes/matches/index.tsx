import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/matches/')({
  beforeLoad: () => {
    throw redirect({ to: '/' })
  },
})
