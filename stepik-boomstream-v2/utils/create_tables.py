#python scripts/create_tables.py
# отдельный скрипт, например scripts/create_tables.py
#(venv) PS C:\sdt\stepik-boomstream-v2> python -m utils.create_tables


import sys
from pathlib import Path

# Добавляем в sys.path корень проекта (там лежит папка app/)
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db import engine, Base  # Base = declarative_base() в app/db.py
from sqlalchemy import text
from app import models  # важно импортировать, чтобы модели зарегистрировались в Base


def main() -> None:
    print(f"Using database: {engine.url}")
    if engine.url.get_backend_name() == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created / updated")


if __name__ == "__main__":
    main()