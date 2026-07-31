import { AlertTriangle } from 'lucide-react'
import { Alert } from '@/components/ui/alert'

const messages: Record<string, string> = {
  code_invalid: 'Código incorreto. Confira e tente de novo.',
  code_expired: 'O código expirou. Peça um novo.',
  password_invalid: 'Senha de duas etapas incorreta.',
  phone_invalid:
    'Número de telefone inválido. Corrija TELEGRAM_PHONE no server/.env e reinicie o backend.',
  phone_no_account: 'Não existe conta do Telegram para esse número.',
  api_credentials_invalid:
    'TELEGRAM_API_ID / TELEGRAM_API_HASH inválidos. Confira o server/.env.',
  flood_wait: 'Muitas tentativas seguidas. Aguarde antes de tentar de novo.',
  not_connected: 'Sem conexão com o Telegram. Verifique a rede do servidor.',
  session_revoked: 'A sessão foi encerrada pelo Telegram. Entre de novo.',
  auth_busy: 'Outra operação de login está em andamento. Aguarde um instante.',
  wrong_state: 'O login mudou de etapa. A tela já foi atualizada.',

  credentials_invalid: 'E-mail ou senha incorretos.',
  user_disabled: 'Este acesso foi desativado. Fale com o administrador.',
  too_many_attempts: 'Muitas tentativas seguidas. Aguarde para tentar de novo.',
  not_authenticated: 'Sua sessão terminou. Entre de novo.',
  session_expired: 'Sua sessão expirou. Entre de novo.',
  password_weak: 'A senha é curta demais.',
  password_reused: 'A nova senha precisa ser diferente da atual.',
  forbidden: 'Você não tem permissão para esta ação.',
  cross_origin: 'Origem não permitida.',
  email_taken: 'Já existe um usuário com este e-mail.',
  last_owner: 'Este é o único administrador ativo. Promova outro antes.',
  self_delete: 'Você não pode excluir a própria conta.',
  user_not_found: 'Usuário não encontrado.',
}

interface Props {
  code?: string | null
  fallback?: string | null
}

export function AuthErrorAlert({ code, fallback }: Props) {
  if (!code && !fallback) return null
  const text = (code && messages[code]) || fallback || 'Não foi possível continuar.'

  return (
    <Alert
      variant={
        code === 'flood_wait' || code === 'too_many_attempts'
          ? 'warning'
          : 'destructive'
      }
    >
      <AlertTriangle />
      <span>{text}</span>
    </Alert>
  )
}
