"""Construção de links do Telegram.

Vive em `core` porque tanto o pipeline de ingestão (`message_service`) quanto a
leitura (`match_service`) precisam disso, e importar um service do outro só por
esse helper arrastaria LangChain e o cliente do bot junto.
"""

from __future__ import annotations


def build_message_link(chat_id: int, message_id: int) -> str:
    chat_id_str = str(chat_id)
    if chat_id_str.startswith("-100"):
        chat_id_str = chat_id_str[4:]
    elif chat_id_str.startswith("-"):
        chat_id_str = chat_id_str[1:]
    return f"https://t.me/c/{chat_id_str}/{message_id}"
