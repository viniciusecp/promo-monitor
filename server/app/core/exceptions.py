class AppException(Exception):
    pass


class InterestNotFoundError(AppException):
    def __init__(self, interest_id: int) -> None:
        self.interest_id = interest_id
        super().__init__(f"Interest {interest_id} not found")


class TelegramNotConnectedError(AppException):
    def __init__(self) -> None:
        super().__init__("Telegram client is not connected")


class MessageNotFoundError(AppException):
    def __init__(self, message_id: int) -> None:
        self.message_id = message_id
        super().__init__(f"Message {message_id} not found")
