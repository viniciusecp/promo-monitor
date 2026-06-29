import { useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { toast } from 'sonner'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { InterestTable } from '@/components/features/InterestTable'
import { DeleteDialog } from '@/components/features/DeleteDialog'
import { useInterests, useUpdateInterest, useDeleteInterest } from '@/hooks/useInterests'
import type { InterestResponse } from '@/types'

export const Route = createFileRoute('/interests/')({
  component: InterestsList,
})

function InterestsList() {
  const [deleteTarget, setDeleteTarget] = useState<InterestResponse | null>(null)
  const { data: interests, isLoading } = useInterests()
  const updateMutation = useUpdateInterest(0)
  const deleteMutation = useDeleteInterest()

  function handleToggle(id: number, ativo: boolean) {
    updateMutation.mutate(
      { ativo },
      {
        onSuccess: () => toast.success('Status atualizado'),
        onError: () => toast.error('Erro ao atualizar status'),
      },
    )
  }

  function handleDelete() {
    if (!deleteTarget) return
    deleteMutation.mutate(deleteTarget.id, {
      onSuccess: () => {
        toast.success('Interesse excluído')
        setDeleteTarget(null)
      },
      onError: () => toast.error('Erro ao excluir interesse'),
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-400">
          {interests?.length ?? 0} interesse(s) cadastrado(s)
        </p>
        <Link to="/interests/new">
          <Button size="sm">
            <Plus className="size-4" />
            Novo Interesse
          </Button>
        </Link>
      </div>

      <div className="rounded-lg border border-zinc-800 bg-zinc-950">
        <InterestTable
          interests={interests}
          isLoading={isLoading}
          onToggle={handleToggle}
          onDelete={setDeleteTarget}
        />
      </div>

      <DeleteDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        onConfirm={handleDelete}
        isPending={deleteMutation.isPending}
        nome={deleteTarget?.nome_produto}
      />
    </div>
  )
}
