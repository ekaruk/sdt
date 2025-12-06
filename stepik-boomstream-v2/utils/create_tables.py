#python scripts/create_tables.py
# отдельный скрипт, например scripts/create_tables.py

from app.db import engine, Base  # где Base = declarative_base()
from app import models  # важно импортнуть, чтобы модели зарегистрировались

def main():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    main()
