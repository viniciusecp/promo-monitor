const steps = [
  {
    title: 'Abra o @BotFather',
    body: (
      <>
        No Telegram, procure por{' '}
        <a
          href="https://t.me/BotFather"
          target="_blank"
          rel="noreferrer"
          className="text-emerald-400 underline underline-offset-2 hover:text-emerald-300"
        >
          @BotFather
        </a>{' '}
        (com o selo de verificado azul) e inicie a conversa.
      </>
    ),
  },
  {
    title: 'Crie o bot',
    body: (
      <>
        Envie <Code>/newbot</Code>. Escolha um <strong>nome</strong> (qualquer um) e
        um <strong>username</strong> que termine em <Code>bot</Code> (ex.:{' '}
        <Code>minhas_promos_bot</Code>).
      </>
    ),
  },
  {
    title: 'Copie o token',
    body: (
      <>
        O BotFather responde com um <strong>token</strong> parecido com{' '}
        <Code>123456789:AAE...xyz</Code>. Copie esse valor.
      </>
    ),
  },
  {
    title: 'Configure no servidor',
    body: (
      <>
        No arquivo <Code>.env</Code> do backend, cole o token em{' '}
        <Code>TELEGRAM_BOT_TOKEN=</Code> e reinicie o servidor.
      </>
    ),
  },
  {
    title: 'Ative as notificações',
    body: (
      <>
        Abra o seu bot recém-criado no Telegram e mande <Code>/start</Code>. Ele
        confirma e preenche o campo abaixo automaticamente. Pronto — as promoções
        chegam na sua conversa com o bot, com notificação.
      </>
    ),
  },
]

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[12px] text-zinc-200">
      {children}
    </code>
  )
}

export function BotSetupGuide() {
  return (
    <div className="space-y-4">
      <p className="text-[13px] leading-relaxed text-zinc-400">
        As promoções são enviadas por um bot do Telegram — assim você recebe a
        notificação no celular (mensagens enviadas pela sua própria conta não
        notificam). Criar o bot é grátis e leva 1 minuto:
      </p>
      <ol className="space-y-3">
        {steps.map((step, i) => (
          <li key={step.title} className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500/15 text-[12px] font-semibold text-emerald-400">
              {i + 1}
            </span>
            <div className="space-y-0.5">
              <p className="text-[13px] font-medium text-zinc-200">{step.title}</p>
              <p className="text-[13px] leading-relaxed text-zinc-400">{step.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}
