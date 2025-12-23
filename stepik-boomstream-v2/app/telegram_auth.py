import hashlib
import hmac
import json
import urllib.parse
from typing import Dict, Optional
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


def validate_webapp_init_data(init_data: str, bot_token: Optional[str] = None) -> Optional[Dict]:
    """
    Проверка подписи initData от Telegram WebApp.
    
    init_data — строка формата URL query string от Telegram.WebApp.initData
    bot_token — токен бота (если не указан, берется из Config)
    
    Возвращает словарь с данными пользователя, если подпись валидна.
    Возвращает None, если подпись невалидна.
    
    Документация:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not bot_token:
        bot_token = Config.TELEGRAM_BOT_TOKEN
    
    if not bot_token or not init_data:
        print("[WebAppAuth] Missing bot_token or init_data.")
        return None
    
    try:
        token_hash = hashlib.sha256(bot_token.encode()).hexdigest()[:8]
        print(f"[WebAppAuth] token_hash={token_hash} init_data_len={len(init_data)}")

        # Парсим параметры
        params = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))

        received_hash = params.get('hash')
        if not received_hash:
            print("[WebAppAuth] Missing hash in init_data.")
            return None

        data_check_items = []
        for key in sorted(params.keys()):
            if key != 'hash':
                data_check_items.append(f"{key}={params[key]}")
        data_check_string = '\n'.join(data_check_items)

        secret_key = hmac.new(
            key="WebAppData".encode(),
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()

        computed_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            print("[WebAppAuth] Hash mismatch.")
            print(f"[WebAppAuth] received_hash={received_hash}")
            print(f"[WebAppAuth] computed_hash={computed_hash}")
            print(f"[WebAppAuth] data_check_string={data_check_string}")
            return None

        user_data = json.loads(urllib.parse.unquote(params.get('user', '{}')))
        
        return {
            'id': user_data.get('id'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'username': user_data.get('username'),
            'language_code': user_data.get('language_code'),
            'is_premium': user_data.get('is_premium', False),
            'auth_date': params.get('auth_date'),
            'query_id': params.get('query_id'),
        }
        
    except Exception as e:
        print(f"Error validating initData: {e}")
        return None

