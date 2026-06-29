# Promo Monitor — Web

Painel de gerenciamento do [Promo Monitor](../README.md). Consome a API REST do [`server/`](../server/README.md) para cadastrar interesses de produto, acompanhar os matches encontrados, navegar pelas mensagens capturadas e configurar o destino dos alertas.

## Stack

- **React 19** + **TypeScript** + **Vite**
- **TanStack Router** — roteamento file-based (`src/routes/`); `routeTree.gen.ts` é gerado automaticamente, **não edite à mão**
- **TanStack Query** — estado de servidor (hooks em `src/hooks/`)
- **Tailwind CSS v4** via `@tailwindcss/vite`
- **shadcn/ui** — componentes em `src/components/ui/`
- **sonner** — toasts; **lucide-react** — ícones
- Alias de path `@/` → `src/`

## Pré-requisitos

- Node + [pnpm](https://pnpm.io) (o `pnpm-lock.yaml` é commitado)
- O backend rodando em `http://localhost:3333` (a base da API está fixada em `src/lib/api.ts`). O backend libera CORS apenas para `http://localhost:3000`.

## Comandos

```bash
pnpm install
pnpm dev       # servidor de desenvolvimento do Vite (porta 3000)
pnpm build     # tsc -b && vite build
pnpm preview   # serve o build de produção
pnpm lint      # eslint
```

## Estrutura

```
src/
├── routes/              # Rotas file-based (TanStack Router)
│   ├── index.tsx        #   Dashboard
│   ├── interests/       #   Listar / criar / editar interesses
│   ├── matches/         #   Matches encontrados
│   ├── messages/        #   Mensagens capturadas
│   └── settings.tsx     #   Destino dos alertas + guia de setup do bot
├── components/
│   ├── features/        # Componentes de domínio (InterestForm, MatchTable, ...)
│   ├── layout/          # Header, Sidebar
│   └── ui/              # Componentes shadcn/ui
├── hooks/               # Hooks TanStack Query (useInterests, useMatches, ...)
├── lib/                 # api.ts (client REST), utils.ts (cn helper)
├── types/               # Tipos das entidades (interest, match, message, settings, ...)
└── routeTree.gen.ts     # Gerado pelo TanStack Router (não editar)
```

## Páginas

| Rota | Descrição |
|------|-----------|
| `/` | Dashboard com visão geral |
| `/interests` | CRUD de interesses (produto, preço máximo, palavras-chave, exclusões) |
| `/matches` | Promoções que bateram com seus interesses |
| `/messages` | Mensagens brutas capturadas dos grupos |
| `/settings` | Define o `alert_target` (destino dos alertas) e mostra o guia de configuração do bot |

## Notas

- A URL da API fica em `src/lib/api.ts` (`BASE_URL`). Ajuste ali se o backend rodar em outro host/porta.
- ESLint configurado com os plugins de React Hooks e React Refresh. Não há test runner configurado.
