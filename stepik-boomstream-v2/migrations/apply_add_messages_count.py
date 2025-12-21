import psycopg2
import os
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import Config

# Применяем миграцию
conn = psycopg2.connect(Config.DATABASE_URL)
cur = conn.cursor()

with open('migrations/add_messages_count.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
    cur.execute(sql)

conn.commit()
cur.close()
conn.close()

print("✅ Миграция add_messages_count применена успешно!")
