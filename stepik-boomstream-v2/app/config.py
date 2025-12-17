import os
from dotenv import load_dotenv

# Загружаем переменные из .env локально (на Render можно не использовать .env)
load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # Пример для SQLite локально: sqlite:///local.db
    DATABASE_URL = os.getenv("DATABASE_URL")

    STEPIK_CLIENT_ID = os.getenv("STEPIK_CLIENT_ID")
    STEPIK_CLIENT_SECRET = os.getenv("STEPIK_CLIENT_SECRET")
    STEPIK_COURSE_ID = os.getenv("STEPIK_COURSE_ID")

    BOOMSTREAM_API_KEY = os.getenv("BOOMSTREAM_API_KEY")

    TELEGRAM_BOT_VIDEO_TOKEN = os.getenv("TELEGRAM_BOT_VIDEO_TOKEN")

    BOOMSTREAM_API_KEY = os.getenv("BOOM_API_KEY")
    BOOMSTREAM_CODE_SUBSCRIPTION = os.getenv("BOOM_CODE_SUBSCRIPTION")
    BOOMSTREAM_MEDIA_CODE = os.getenv("BOOM_MEDIA_CODE")