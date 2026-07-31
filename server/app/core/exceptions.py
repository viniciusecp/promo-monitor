class AppException(Exception):
    pass


class InterestNotFoundError(AppException):
    def __init__(self, interest_id: int) -> None:
        self.interest_id = interest_id
        super().__init__(f"Interest {interest_id} not found")


class MatchNotFoundError(AppException):
    def __init__(self, match_id: int) -> None:
        self.match_id = match_id
        super().__init__(f"Match {match_id} not found")


class TelegramNotConnectedError(AppException):
    def __init__(self) -> None:
        super().__init__("Telegram client is not connected")


class MessageNotFoundError(AppException):
    def __init__(self, message_id: int) -> None:
        self.message_id = message_id
        super().__init__(f"Message {message_id} not found")


class TelegramAuthBusyError(AppException):
    """Outra operação de login já está em andamento.

    Falha rápido em vez de enfileirar: duas submissões de código concorrentes
    disputariam o mesmo `phone_code_hash` e a segunda queimaria o da primeira.
    """

    def __init__(self) -> None:
        super().__init__("Another authentication operation is in progress")


class TelegramAuthStateError(AppException):
    """Operação incompatível com o estado atual da máquina de autenticação."""

    def __init__(self, expected: str, actual: str) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(f"Expected auth status {expected!r}, got {actual!r}")


class AuthError(AppException):
    """Falha de autenticação/autorização do painel, com código estável.

    Mesmo contrato de `TelegramAuthError`: o frontend decide a mensagem pelo
    `code`, não pelo status HTTP.
    """

    def __init__(self, code: str, message: str, retry_after: int | None = None) -> None:
        self.code = code
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)


class UserNotFoundError(AppException):
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")


class TelegramAuthError(AppException):
    """Erro do Telegram já traduzido para um código estável da API."""

    def __init__(self, code: str, message: str, retry_after: int | None = None) -> None:
        self.code = code
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)
