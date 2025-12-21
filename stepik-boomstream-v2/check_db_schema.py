# Скрипт для сравнения структуры БД и моделей SQLAlchemy
# Сохрани этот файл как check_db_schema.py и запусти: python check_db_schema.py

from app.db import engine
from app import models
from sqlalchemy import inspect


def print_table_diff():
    inspector = inspect(engine)
    model_tables = set(models.Base.metadata.tables.keys())
    db_tables = set(inspector.get_table_names())

    print("=== Таблицы, определённые в моделях, но отсутствующие в БД ===")
    for t in sorted(model_tables - db_tables):
        print(f"  - {t}")
    print("=== Таблицы, присутствующие в БД, но отсутствующие в моделях ===")
    for t in sorted(db_tables - model_tables):
        print(f"  - {t}")

    print("\n=== Сравнение столбцов по таблицам ===")
    for table in sorted(model_tables & db_tables):
        model_cols = set(models.Base.metadata.tables[table].columns.keys())
        db_cols = set([col['name'] for col in inspector.get_columns(table)])
        if model_cols != db_cols:
            print(f"\nТаблица: {table}")
            print(f"  В моделях, но нет в БД: {model_cols - db_cols}")
            print(f"  В БД, но нет в моделях: {db_cols - model_cols}")

if __name__ == "__main__":
    print_table_diff()
