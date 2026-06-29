import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.logging import logger
from app.models.product_interest import ProductInterest


SYSTEM_PROMPT = (
    "Você valida promoções do Telegram. Dada a definição de um produto que o "
    "usuário procura e o texto de uma mensagem, decida se a mensagem é realmente "
    "uma promoção desse produto (não um acessório, não outro item que apenas cita "
    "palavras parecidas). Responda APENAS com uma linha em JSON, sem mais nada, "
    'no formato: {"corresponde": true/false, "motivo": "explicação curta"}'
)

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def _build_prompt(texto: str, interest: ProductInterest) -> str:
    chave = ", ".join(interest.palavras_chave or []) or "(nenhuma)"
    excl = ", ".join(interest.palavras_excluidas or []) or "(nenhuma)"
    preco = (
        f"R$ {interest.preco_maximo:.2f}" if interest.preco_maximo else "(sem limite)"
    )
    return (
        f"Produto procurado: {interest.nome_produto}\n"
        f"Palavras-chave: {chave}\n"
        f"Palavras a excluir: {excl}\n"
        f"Preço máximo desejado: {preco}\n\n"
        f"Mensagem recebida:\n{texto}"
    )


def _parse_response(content: str) -> tuple[bool, str | None]:
    match = _JSON_BLOCK.search(content)
    if not match:
        raise ValueError(f"sem JSON na resposta: {content!r}")
    data = json.loads(match.group(0))
    return bool(data["corresponde"]), data.get("motivo")


class LLMValidator:
    """Verifica, via LLM, se um candidato do matcher é mesmo a promoção buscada.

    Fail-open: desativado, sem API key, ou em erro/timeout, aprova o candidato
    (retorna True) para não perder promoções reais por falha transitória.
    """

    def __init__(self) -> None:
        self.llm: ChatOpenAI | None = None
        if settings.llm_validation_enabled and settings.openrouter_api_key:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.openrouter_api_key,
                base_url=settings.llm_base_url,
                temperature=0,
                max_tokens=200,
                timeout=settings.llm_timeout,
            )
            logger.info("llm_validator_enabled", model=settings.llm_model)
        else:
            logger.info("llm_validator_disabled")

    async def validate(
        self, texto: str | None, interest: ProductInterest
    ) -> tuple[bool, str | None]:
        if self.llm is None or not texto:
            return True, None
        try:
            resp = await self.llm.ainvoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=_build_prompt(texto, interest)),
                ]
            )
            return _parse_response(str(resp.content))
        except Exception as e:
            logger.warning(
                "llm_validation_error",
                error=str(e),
                produto=interest.nome_produto,
            )
            return True, None
