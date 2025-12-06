# pip install telethon

import csv
from telethon import TelegramClient
from telethon.tl.types import User

# ----- НАСТРОЙКИ -----
api_id = 36007316          # <-- твой api_id с my.telegram.org
api_hash = '9ab4638ce92eb93b2411d5c4f8dbb9d8'  # <-- твой api_hash
chat = 'https://t.me/+plePWX6lMVU2NTk8'  # @username или ссылка/ID группы
csv_filename = 'members.csv'
# ----------------------


def user_to_row(u: User) -> dict:
    """Преобразуем объект User в словарь для CSV."""
    return {
        "id": u.id,
        "is_self": u.is_self,
        "is_contact": u.contact,
        "is_mutual_contact": u.mutual_contact,
        "is_deleted": u.deleted,
        "is_bot": u.bot,
        "is_verified": u.verified,
        "is_restricted": u.restricted,
        "is_scam": u.scam,
        "is_fake": u.fake,
        "first_name": u.first_name or "",
        "last_name": u.last_name or "",
        "username": u.username or "",
        "phone": u.phone or "",
        "lang_code": getattr(u, "lang_code", "") or "",
        "about": "",  # можно будет дополнить, если отдельно получать bio
    }


async def main():
    client = TelegramClient('user_session', api_id, api_hash)
    await client.start()   # при первом запуске попросит код из Telegram

    print("Загружаю участников…")
    participants = await client.get_participants(chat, limit=None)

    print(f"Найдено участников: {len(participants)}")

    # подготовим заголовки по первому пользователю
    if not participants:
        print("Группа пустая или нет доступа.")
        return

    first_row = user_to_row(participants[0])
    fieldnames = list(first_row.keys())

    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # первый уже преобразовали
        writer.writerow(first_row)

        for user in participants[1:]:
            writer.writerow(user_to_row(user))

    print(f"Готово! Данные сохранены в файл: {csv_filename}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
