import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path

# Подключаем корень проекта
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import SessionLocal
from app.models import User
from sqlalchemy import func


def import_boom_passwords(xml_file: str):
    """
    Импорт Boomstream email + Hash в таблицу users.
    Если email существует → обновить boom_password
    Если нет → добавить нового пользователя
    """

    tree = ET.parse(xml_file)
    root = tree.getroot()

    db = SessionLocal()

    created = 0
    updated = 0

    try:
        for item in root.findall(".//Item"):
            email = item.findtext("Email", "").strip()
            boom_hash = item.findtext("Hash", "").strip()

            if not email:
                continue

            # поиск без учёта регистра
            user = (
                db.query(User)
                .filter(func.lower(User.email) == email.lower())
                .first()
            )

            if user:
                # обновляем пароль
                user.boom_password = boom_hash
                updated += 1

            else:
                # создаём нового пользователя
                user = User(
                    email=email,
                    boom_password=boom_hash,
                )
                db.add(user)
                created += 1

        db.commit()

    finally:
        db.close()

    print(f"Готово: обновлено {updated}, создано новых {created}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python utils/import_boom_passwords.py boom_names_site.json")
        sys.exit(1)

    import_boom_passwords(sys.argv[1])
