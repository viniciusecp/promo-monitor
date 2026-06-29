import { createFileRoute, useNavigate, useParams } from '@tanstack/react-router'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { InterestForm } from '@/components/features/InterestForm'
import { useInterest, useUpdateInterest } from '@/hooks/useInterests'

export const Route = createFileRoute('/interests/$interestId/edit')({
  component: EditInterest,
})

function EditInterest() {
  const navigate = useNavigate()
  const { interestId } = useParams({ from: '/interests/$interestId/edit' })
  const id = Number(interestId)
  const { data: interest, isLoading } = useInterest(id)
  const updateMutation = useUpdateInterest(id)

  function handleSubmit(data: Parameters<typeof updateMutation.mutate>[0]) {
    updateMutation.mutate(data, {
      onSuccess: () => {
        toast.success('Interesse atualizado')
        navigate({ to: '/interests' })
      },
      onError: () => toast.error('Erro ao atualizar interesse'),
    })
  }

  if (isLoading) {
    return (
      <Card className="max-w-lg border-zinc-800 bg-zinc-950">
        <CardHeader>
          <Skeleton className="h-4 w-32 bg-zinc-800" />
        </CardHeader>
        <CardContent className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full bg-zinc-800" />
          ))}
        </CardContent>
      </Card>
    )
  }

  if (!interest) {
    return (
      <p className="py-8 text-center text-sm text-zinc-500">
        Interesse não encontrado.
      </p>
    )
  }

  return (
      <Card className="max-w-lg border-zinc-800 bg-zinc-950 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-200">
            Editar Interesse
          </CardTitle>
        </CardHeader>
      <CardContent>
        <InterestForm
          defaultValues={interest}
          onSubmit={handleSubmit}
          isPending={updateMutation.isPending}
          submitLabel="Salvar Alterações"
        />
      </CardContent>
    </Card>
  )
}
