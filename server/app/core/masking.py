"""Máscaras para segredos que não podem vazar em log nem em resposta HTTP.

O structlog serializa o que receber, então telefone e token só entram em log
depois de passar por aqui. O token do bot também nunca volta cru pelo `GET
/settings` — o frontend só precisa saber que existe e reconhecer qual é.
"""


def mask_phone(phone: str | None) -> str:
    """`+5511987654321` -> `+55119****4321`. Mantém o suficiente para o usuário
    reconhecer o número sem expô-lo por inteiro."""
    if not phone:
        return ""
    digits = phone.strip()
    if len(digits) <= 8:
        return "*" * len(digits)
    return f"{digits[:5]}{'*' * (len(digits) - 9)}{digits[-4:]}"


def mask_token(token: str | None) -> str | None:
    """`123456789:AAEabc...xyz` -> `123456789:AAE…3xyz`.

    A metade antes de `:` é o id público do bot; só a segunda metade é segredo.
    """
    if not token:
        return None
    token = token.strip()
    bot_id, _, secret = token.partition(":")
    if not secret:
        return f"{token[:3]}…{token[-4:]}" if len(token) > 10 else "…"
    if len(secret) <= 8:
        return f"{bot_id}:…"
    return f"{bot_id}:{secret[:3]}…{secret[-4:]}"
