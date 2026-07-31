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
- O backend rodando em `http://localhost:3333`. O painel chama `/api` na **própria origem**: em dev o `server.proxy` do `vite.config.ts` encaminha para a porta 3333, e em produção quem proxia é o nginx da imagem `web`. Mesma origem em ambos os modos — é o que faz o cookie de sessão (`HttpOnly`, `SameSite=Lax`) funcionar sem CORS.
- Antes de entrar, o backend precisa ter um usuário: defina `AUTH_SEED_EMAIL`/`AUTH_SEED_PASSWORD` no `server/.env` (não há cadastro aberto).

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
│   ├── index.tsx        #   Feed de matches
│   ├── login.tsx        #   Login do painel (e-mail + senha)
│   ├── trocar-senha.tsx #   Troca de senha (obrigatória em senha provisória)
│   ├── telegram.tsx     #   Conectar a conta do Telegram (só admin)
│   ├── interests/       #   Listar / criar / editar interesses
│   ├── matches/         #   Redireciona para `/`
│   ├── messages/        #   Mensagens capturadas
│   └── settings.tsx     #   Usuários + conexão + guia/token do bot (só admin)
├── components/
│   ├── features/        # Componentes de domínio (InterestForm, MatchTable, users/, ...)
│   ├── layout/          # Header, Sidebar, UserMenu
│   └── ui/              # Componentes shadcn/ui
├── hooks/               # Hooks TanStack Query (useSession, useUsers, useMatches, ...)
├── lib/                 # api.ts (client REST), utils.ts (cn helper)
├── types/               # Tipos das entidades (session, user, interest, match, ...)
└── routeTree.gen.ts     # Gerado pelo TanStack Router (não editar)
```

## Páginas

| Rota | Descrição |
|------|-----------|
| `/login` | Login do painel. Não há cadastro aberto — acessos são criados por um admin |
| `/trocar-senha` | Troca de senha; obrigatória quando a senha foi definida por outra pessoa |
| `/` | Feed das promoções que bateram com seus interesses |
| `/interests` | CRUD de interesses (produto, preço máximo, palavras-chave, exclusões) |
| `/messages` | Mensagens brutas capturadas dos grupos |
| `/telegram` | **Admin** — conectar a conta do Telegram que lê os grupos |
| `/settings` | **Admin** — usuários, conexão do Telegram, guia + token do bot e estado dos alertas (o destino é definido mandando `/start` ao bot, não pelo painel) |

O gate fica no componente do `__root.tsx`, não em `beforeLoad` — um guard assíncrono no
router bloquearia toda navegação numa chamada de rede e não daria para invalidar a partir
das mutações de login.

## Notas

- A base da API fica em `src/lib/api.ts` (`BASE_URL`), e é `/api` — relativa de propósito. Para apontar para outro host, defina `VITE_API_URL`; aí a chamada vira cross-origin e o backend precisa dessa origem em `CORS_ORIGINS` (`server/.env`), senão o cookie de sessão não viaja e o login não persiste.
- ESLint configurado com os plugins de React Hooks e React Refresh. Não há test runner configurado.
