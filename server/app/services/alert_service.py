from telethon import TelegramClient

from app.core.logging import logger


ALERT_TEMPLATE = """🚨 *Promo encontrada!*

*Produto:* {produto}
*Preço:* {preco}
*Grupo:* {grupo}
*Score:* {score:.2f}

*Mensagem original:*
{texto}

*Link:* {link}"""


class AlertService:
    def __init__(self, client: TelegramClient) -> None:
        self.client = client

    async def send_alert(
        self,
        produto: str,
        preco: str,
        grupo: str,
        score: float,
        texto: str,
        link: str,
    ) -> bool:
        try:
            me = await self.client.get_me()
            message = ALERT_TEMPLATE.format(
                produto=produto,
                preco=preco,
                grupo=grupo,
                score=score,
                texto=texto[:500],
                link=link,
            )
            await self.client.send_message(me.id, message)
            logger.info("alert_sent", produto=produto, score=score)
            return True
        except Exception as e:
            logger.error("alert_failed", error=str(e), produto=produto)
            return False
