import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { MessageList } from '@/components/features/MessageList'
import { useMessages } from '@/hooks/useMessages'

export const Route = createFileRoute('/messages/')({
  component: MessagesList,
})

function MessagesList() {
  const [chatId, setChatId] = useState<string>('')

  const filters: Parameters<typeof useMessages>[0] = {}
  if (chatId) filters.chat_id = Number(chatId)

  const { data: messages, isLoading } = useMessages(filters)

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
              <Label htmlFor="chatId" className="text-xs text-zinc-400">
                ID do Chat
              </Label>
              <Input
                id="chatId"
                type="number"
                placeholder="Todos"
                value={chatId}
                onChange={(e) => setChatId(e.target.value)}
                className="w-32"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-950">
        <CardContent className="pt-4">
          <MessageList messages={messages} isLoading={isLoading} />
        </CardContent>
      </Card>
    </div>
  )
}
