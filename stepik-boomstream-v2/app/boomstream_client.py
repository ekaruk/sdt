from typing import List
from .config import Config

# ВНИМАНИЕ: здесь заглушка. URL и структура тела нужно
# сверить с документацией Boomstream.
BOOMSTREAM_API_BASE = "https://api.boomstream.com/v1"


class BoomstreamClient:
    """
    Клиент Boomstream. Сейчас реализован как заглушка:
    выводит в консоль, что "выдал доступ".
    Реальные вызовы API нужно подставить по документации Boomstream.
    """

    def __init__(self) -> None:
        self.api_key = Config.BOOMSTREAM_API_KEY

    def grant_access(self, user_email: str, resource_ids: List[str]) -> None:
        """
        Заглушка: вместо реального вызова Boomstream API просто печатаем.
        Здесь позже можно сделать реальный POST запрос.
        """
        if not resource_ids:
            return

        print(f"[Boomstream] Выдаю доступ {user_email} к: {resource_ids}")
