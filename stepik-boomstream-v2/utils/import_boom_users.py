import sys
import pandas as pd
from pathlib import Path

#$env:DATABASE_URL = "sqlite:///local.db"
#python utils/import_boom_users.py utils/boom_names.csv


# Подключаем корень проекта (чтобы import app.* работал)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import SessionLocal
from app.models import User


def import_boom_users(csv_path: str):
    df = pd.read_csv(csv_path)

    # Нормализуем названия колонок
    df.columns = [c.strip().lower() for c in df.columns]

    required = {"email", "first_name", "last_name"}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV должен содержать столбцы: {required}")

    db = SessionLocal()

    created = 0
    updated = 0

    try:
        for _, row in df.iterrows():
            email = str(row["email"]).strip().lower()
            first_name = row.get("first_name")
            last_name = row.get("last_name")

            if not email:
                continue  # пропускаем пустые строки

            # ищем пользователя по email
            user = db.query(User).filter_by(email=email).first()

            if not user:
                # создаём нового
                user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    boom_password=None,     # если нужно — добавь логику
                    stepik_user_id=None,
                )
                db.add(user)
                created += 1
            else:
                # обновляем
                user.first_name = first_name
                user.last_name = last_name
                updated += 1

        db.commit()

    finally:
        db.close()

    print(f"Готово! Создано новых: {created}, обновлено: {updated}")


if __name__ == "__main__":
    import_boom_users("utils/boom_names.csv")
    
    if len(sys.argv) < 2:
        print("Использование: python utils/import_boom_users.py boom_names.csv")
        sys.exit(1)

    import_boom_users(sys.argv[1])
