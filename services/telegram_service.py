import time

import requests

from config import Config


class TelegramService:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._chat_id = chat_id
        self._url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send(self, message: str) -> None:
        chunks = self._split(message)
        for idx, chunk in enumerate(chunks, start=1):
            response = requests.post(
                self._url,
                json={
                    "chat_id": self._chat_id,
                    "text": chunk,
                    "disable_web_page_preview": True,
                },
                timeout=30,
            )
            response.raise_for_status()
            if idx < len(chunks):
                time.sleep(1)

    def _split(self, message: str) -> list[str]:
        if len(message) <= Config.TELEGRAM_MAX_CHARS:
            return [message]

        chunks: list[str] = []
        current = ""
        for block in message.split("\n\n"):
            candidate = f"{current}\n\n{block}".strip() if current else block
            if len(candidate) <= Config.TELEGRAM_MAX_CHARS:
                current = candidate
                continue
            if current:
                chunks.append(current)
            current = block[: Config.TELEGRAM_MAX_CHARS]
        if current:
            chunks.append(current)
        return chunks
