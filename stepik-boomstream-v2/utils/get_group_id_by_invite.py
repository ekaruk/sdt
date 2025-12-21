import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
try:
    from telethon.sync import TelegramClient
    from telethon.errors.rpcerrorlist import InviteHashInvalidError
except ImportError:
    print("Telethon не установлен. Установите через: pip install telethon")
    exit(1)

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
INVITE_LINK = 'https://t.me/+LccTWnV7lFEzMjUy'

if not API_ID or not API_HASH or not INVITE_LINK:
    print(f"Проверьте, что в .env заданы TG_API_ID {API_ID}, TG_API_HASH {API_HASH}, TG_INVITE_LINK {INVITE_LINK}")
    exit(1)

with TelegramClient('anon', API_ID, API_HASH) as client:
    try:
        entity = client.get_entity(INVITE_LINK)
        print(f"ID группы/канала: {entity.id}")
        print(f"Username: {getattr(entity, 'username', None)}")
        print(f"Title: {getattr(entity, 'title', None)}")
    except InviteHashInvalidError:
        print("Invite-ссылка недействительна или истекла.")
    except Exception as e:
        print(f"Ошибка: {e}")
