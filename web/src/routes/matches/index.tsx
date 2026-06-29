import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { MatchTable } from '@/components/features/MatchTable'
import { useMatches } from '@/hooks/useMatches'

export const Route = createFileRoute('/matches/')({
  component: MatchesList,
})

function MatchesList() {
  const [interestId, setInterestId] = useState<string>('')
  const [alerted, setAlerted] = useState<string>('')

  const filters: Parameters<typeof useMatches>[0] = {}
  if (interestId) filters.interest_id = Number(interestId)
  if (alerted === 'true') filters.alerted = true
  if (alerted === 'false') filters.alerted = false

  const { data: matches, isLoading } = useMatches(filters)

  return (
    <div className="space-y-4">
      <Card className="border-zinc-800 bg-zinc-950">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-200">
            Filtros
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="interestId" className="text-xs text-zinc-400">
                ID do Interesse
              </Label>
              <Input
                id="interestId"
                type="number"
                placeholder="Todos"
                value={interestId}
                onChange={(e) => setInterestId(e.target.value)}
                className="w-32"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="alerted" className="text-xs text-zinc-400">
                Alertado
              </Label>
              <Select value={alerted} onValueChange={(v) => setAlerted(v ?? '')}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Todos</SelectItem>
                  <SelectItem value="true">Sim</SelectItem>
                  <SelectItem value="false">Não</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-950">
        <CardContent className="pt-4">
          <MatchTable matches={matches} isLoading={isLoading} />
        </CardContent>
      </Card>
    </div>
  )
}
