import sys
import pandas as pd
from pathlib import Path

# --- подключаем проект ---
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import SessionLocal, engine, Base
from app.models import TelegramUser

# Ensure table exists when running this script standalone.
Base.metadata.create_all(bind=engine)


def normalize_phone(value):
    """
    Преобразует телефон в строку.
    В CSV телефон может быть в float формате 3.245616e+10 → '32456160000'
    """
    if pd.isna(value):
        return None
    try:
        # если float или scientific notation → превратим в целое число
        return str(int(value))
    except Exception:
        return str(value)


def import_telegram_users(csv_path: str):
    df = pd.read_csv(csv_path)

    # выводим первые строки для контроля
    print("Прочитано строк:", len(df))
    print(df.head())

    db = SessionLocal()

    imported = 0
    updated = 0

    try:
        for _, row in df.iterrows():
            tg_id = int(row["id"])

            first_name = row.get("first_name")
            last_name = row.get("last_name")
            username = row.get("username")
            phone = normalize_phone(row.get("phone"))

            # ищем существующую запись
            user = db.query(TelegramUser).filter_by(id=tg_id).first()

            if not user:
                # создаём нового
                user = TelegramUser(
                    id=tg_id,
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    phone=phone,
                )
                db.add(user)
                imported += 1
            else:
                # обновляем существующего
                user.first_name = first_name
                user.last_name = last_name
                user.username = username
                user.phone = phone
                updated += 1

        db.commit()

    finally:
        db.close()

    print(f"Готово! Новых: {imported}, обновлено: {updated}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python utils/import_telegram_users.py members.csv")
        sys.exit(1)

    csv_file = sys.argv[1]
    import_telegram_users(csv_file)
