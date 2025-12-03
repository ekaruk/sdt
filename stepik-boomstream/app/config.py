import os
from dotenv import load_dotenv

# Загружаем переменные из .env локально (на Render можно не использовать .env)
load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # Пример для SQLite локально: sqlite:///local.db
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

    STEPIK_CLIENT_ID = os.getenv("STEPIK_CLIENT_ID")
    STEPIK_CLIENT_SECRET = os.getenv("STEPIK_CLIENT_SECRET")
    STEPIK_COURSE_ID = os.getenv("STEPIK_COURSE_ID")

    BOOMSTREAM_API_KEY = os.getenv("BOOMSTREAM_API_KEY", "")
