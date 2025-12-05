import hashlib
import hmac
from typing import Dict
from .config import Config


def verify_telegram_auth(data: Dict[str, str]) -> bool:
    """
    Проверка подписи данных от Telegram Login Widget.

    data — словарь всех параметров из запроса (query string или form),
    включая 'hash'. Алгоритм как в оф. доке Telegram:
    https://core.telegram.org/widgets/login#checking-authorization

    Возвращает True, если подпись корректна.
    """
    bot_token = Config.TELEGRAM_BOT_TOKEN
    if not bot_token:
        return False

    received_hash = data.get("hash")
    if not received_hash:
        return False

    auth_data = {k: v for k, v in data.items() if k != "hash"}

    pieces = [f"{k}={auth_data[k]}" for k in sorted(auth_data.keys())]
    data_check_string = "\n".join(pieces)

    secret_key = hashlib.sha256(bot_token.encode()).digest()

    computed_hash = hmac.new(
        secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed_hash, received_hash)
