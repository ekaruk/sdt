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
        return None
    
    try:
        # Парсим параметры
        params = dict(item.split('=', 1) for item in init_data.split('&') if '=' in item)
        
        received_hash = params.get('hash')
        if not received_hash:
            return None
        
        # Создаем data_check_string из всех параметров кроме hash
        data_check_items = []
        for key in sorted(params.keys()):
            if key != 'hash':
                data_check_items.append(f"{key}={params[key]}")
        
        data_check_string = '\n'.join(data_check_items)
        
        # Создаем secret_key: HMAC-SHA256(bot_token, "WebAppData")
        secret_key = hmac.new(
            key="WebAppData".encode(),
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Вычисляем hash: HMAC-SHA256(secret_key, data_check_string)
        computed_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Проверяем подпись
        if not hmac.compare_digest(computed_hash, received_hash):
            return None
        
        # Извлекаем данные пользователя
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

