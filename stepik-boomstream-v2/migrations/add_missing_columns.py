# Миграция: добавление недостающих столбцов в существующие таблицы
# Запуск: python -m migrations.add_missing_columns

from sqlalchemy import text
from app.db import engine

def add_column_if_not_exists(table, column_def):
    with engine.connect() as conn:
        # Проверяем наличие столбца
        res = conn.execute(text(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='{table}' AND column_name='{column_def.split()[0]}'
        """))
        if not res.fetchone():
            print(f"Добавляю столбец {column_def.split()[0]} в {table}...")
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_def}"))
        else:
            print(f"Столбец {column_def.split()[0]} уже есть в {table}")


def run():
    add_column_if_not_exists('stepik_lessons', 'steps_amount INTEGER')
    add_column_if_not_exists('stepik_modules', 'forum_topic_icon VARCHAR')
    add_column_if_not_exists('stepik_modules', 'short_title VARCHAR')
    add_column_if_not_exists('users', 'role INTEGER DEFAULT 0 NOT NULL')
    print('Миграция завершена.')

if __name__ == "__main__":
    run()
