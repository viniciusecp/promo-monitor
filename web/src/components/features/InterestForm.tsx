import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import type { InterestResponse } from '@/types'

interface InterestFormData {
  nome_produto: string
  preco_maximo: string
  limiar_match: string
  palavras_chave: string
  palavras_excluidas: string
  ativo: boolean
}

interface Props {
  defaultValues?: InterestResponse
  onSubmit: (data: {
    nome_produto: string
    preco_maximo: number | null
    limiar_match: number | null
    palavras_chave: string[]
    palavras_excluidas: string[]
    ativo: boolean
  }) => void
  isPending: boolean
  submitLabel: string
}

export function InterestForm({ defaultValues, onSubmit, isPending, submitLabel }: Props) {
  const [data, setData] = useState<InterestFormData>({
    nome_produto: defaultValues?.nome_produto ?? '',
    preco_maximo: defaultValues?.preco_maximo?.toString() ?? '',
    limiar_match: defaultValues?.limiar_match?.toString() ?? '',
    palavras_chave: defaultValues?.palavras_chave.join('\n') ?? '',
    palavras_excluidas: defaultValues?.palavras_excluidas.join('\n') ?? '',
    ativo: defaultValues?.ativo ?? true,
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit({
      nome_produto: data.nome_produto,
      preco_maximo: data.preco_maximo ? Number(data.preco_maximo) : null,
      limiar_match: data.limiar_match ? Number(data.limiar_match) : null,
      palavras_chave: data.palavras_chave
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean),
      palavras_excluidas: data.palavras_excluidas
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean),
      ativo: data.ativo,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="space-y-2">
        <Label htmlFor="nome_produto">Nome do Produto</Label>
        <Input
          id="nome_produto"
          value={data.nome_produto}
          onChange={(e) => setData({ ...data, nome_produto: e.target.value })}
          placeholder="Ex: iPhone 15"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="preco_maximo">Preço Máximo (R$)</Label>
        <Input
          id="preco_maximo"
          type="number"
          step="0.01"
          min="0"
          value={data.preco_maximo}
          onChange={(e) => setData({ ...data, preco_maximo: e.target.value })}
          placeholder="Ex: 2500.00"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="limiar_match">Limiar de match (0–1, opcional)</Label>
        <Input
          id="limiar_match"
          type="number"
          step="0.05"
          min="0"
          max="1"
          value={data.limiar_match}
          onChange={(e) => setData({ ...data, limiar_match: e.target.value })}
          placeholder="Padrão: 0.6 (global)"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="palavras_chave">Palavras-chave (uma por linha)</Label>
        <Textarea
          id="palavras_chave"
          value={data.palavras_chave}
          onChange={(e) => setData({ ...data, palavras_chave: e.target.value })}
          placeholder="iphone&#10;apple&#10;smartphone"
          rows={4}
        />
        <p className="text-xs text-zinc-500">
          Se você definir palavras-chave, a mensagem precisa conter uma delas para dar match.
          Sem palavras-chave, usamos a similaridade com o nome do produto.
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="palavras_excluidas">Palavras Excluídas (uma por linha)</Label>
        <Textarea
          id="palavras_excluidas"
          value={data.palavras_excluidas}
          onChange={(e) => setData({ ...data, palavras_excluidas: e.target.value })}
          placeholder="capinha&#10;fone&#10;carregador"
          rows={4}
        />
      </div>

      <div className="flex items-center gap-3">
        <Switch
          id="ativo"
          size="sm"
          checked={data.ativo}
          onCheckedChange={(checked) => setData({ ...data, ativo: checked })}
        />
        <Label htmlFor="ativo" className="cursor-pointer">Ativo</Label>
      </div>

      <div className="flex gap-3 pt-2">
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Salvando...' : submitLabel}
        </Button>
      </div>
    </form>
  )
}
