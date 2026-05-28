from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from app.core.logging import logger


async def ensure_authenticated(client: TelegramClient, phone: str) -> bool:
    if await client.is_user_authorized():
        me = await client.get_me()
        logger.info("already_authenticated", phone=me.phone)
        return True

    await client.send_code_request(phone)
    code = input(f"Código enviado para {phone}. Digite o código: ")

    try:
        await client.sign_in(phone=phone, code=code.strip())
    except SessionPasswordNeededError:
        password = input("Senha de dois fatores: ")
        await client.sign_in(password=password.strip())

    me = await client.get_me()
    logger.info("authenticated", phone=me.phone)
    return True
