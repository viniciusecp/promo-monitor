import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { InterestForm } from '@/components/features/InterestForm'
import { useCreateInterest } from '@/hooks/useInterests'

export const Route = createFileRoute('/interests/new')({
  component: NewInterest,
})

function NewInterest() {
  const navigate = useNavigate()
  const createMutation = useCreateInterest()

  function handleSubmit(data: Parameters<typeof createMutation.mutate>[0]) {
    createMutation.mutate(data, {
      onSuccess: (result) => {
        toast.success('Interesse criado com sucesso')
        navigate({ to: '/interests' })
      },
      onError: () => toast.error('Erro ao criar interesse'),
    })
  }

  return (
    <Card className="max-w-lg border-zinc-800 bg-zinc-950 text-zinc-100">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-zinc-200">
          Novo Interesse
        </CardTitle>
      </CardHeader>
      <CardContent>
        <InterestForm
          onSubmit={handleSubmit}
          isPending={createMutation.isPending}
          submitLabel="Criar Interesse"
        />
      </CardContent>
    </Card>
  )
}
