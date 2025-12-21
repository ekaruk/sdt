# Миграционный скрипт для синхронизации схемы БД с моделями SQLAlchemy
# Запуск: python -m migrations.manual_sync_schema

from app.db import engine
from app import models

def sync_schema():
    print("Создание недостающих таблиц и столбцов по моделям...")
    models.Base.metadata.create_all(bind=engine)
    print("Готово. Недостающие таблицы и поля добавлены.")

if __name__ == "__main__":
    sync_schema()
