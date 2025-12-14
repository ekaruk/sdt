import asyncio
from telethon import TelegramClient

# ==== ЗАПОЛНИ СВОИ ДАННЫЕ ТУТ ====
api_id = 36007316          # <-- твой api_id с my.telegram.org
api_hash = '9ab4638ce92eb93b2411d5c4f8dbb9d8'  # <-- твой api_hash
session_name = "my_user_session"  # имя файла сессии, можно любое
# ================================

client = TelegramClient(session_name, api_id, api_hash)


async def main():
    # Запускаем клиент (при первом запуске спросит телефон/код)
    await client.start()
    print("Список каналов, где ты участник:\n")

    async for dialog in client.iter_dialogs():
        entity = dialog.entity

        # Нам нужны только КАНАЛЫ (broadcast), без чатов и групп
        is_channel = getattr(entity, "broadcast", False)

        if is_channel:
            title = dialog.name
            chat_id = entity.id
            username = getattr(entity, "username", None)

            print("———————")
            print(f"Название: {title}")
            print(f"ID:       {chat_id}")
            if username:
                print(f"Username: @{username}")
            else:
                print("Username: (нет, канал приватный)")

    print("\nГотово.")


if __name__ == "__main__":
    asyncio.run(main())
