import os
import sys
from dotenv import load_dotenv

# Загружаем переменные из .env локально (на Render можно не использовать .env)
load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # Пример для SQLite локально: sqlite:///local.db
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # WEBAPP_URL используется как основной домен для Mini App и Telegram Widget
    #WEBAPP_URL = os.getenv("WEBAPP_URL")
    APP_DOMAIN = os.getenv("APP_DOMAIN")
    

    STEPIK_CLIENT_ID = os.getenv("STEPIK_CLIENT_ID")
    STEPIK_CLIENT_SECRET = os.getenv("STEPIK_CLIENT_SECRET")
    STEPIK_COURSE_ID = os.getenv("STEPIK_COURSE_ID")
    STEPIK_GROUP_ID = os.getenv("STEPIK_GROUP_ID")

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # ID форум-группы для публикации вопросов
    BOT_USERNAME = os.getenv("BOT_USERNAME")

    BOOMSTREAM_API_KEY = os.getenv("BOOM_API_KEY")
    BOOMSTREAM_CODE_SUBSCRIPTION = os.getenv("BOOM_CODE_SUBSCRIPTION")
    BOOMSTREAM_MEDIA_CODE = os.getenv("BOOM_MEDIA_CODE")
    
    # OpenAI API для генерации заголовков
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    @classmethod
    def validate(cls):
        """Проверка критических параметров при старте приложения"""
        errors = []
        
        # Критические параметры
        if not cls.DATABASE_URL:
            errors.append("❌ DATABASE_URL не задан!")
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("❌ TELEGRAM_BOT_TOKEN не задан!")
        
        if not cls.APP_DOMAIN:
            errors.append("❌ APP_DOMAIN не задан! (необходим для Mini App)")
        
        # Предупреждения о необязательных параметрах
        warnings = []
        
        if not cls.STEPIK_CLIENT_ID or not cls.STEPIK_CLIENT_SECRET:
            warnings.append("⚠️  STEPIK_CLIENT_ID/STEPIK_CLIENT_SECRET не заданы (функции Stepik будут недоступны)")
        
        if not cls.BOOMSTREAM_API_KEY:
            warnings.append("⚠️  BOOMSTREAM_API_KEY (BOOM_API_KEY) не задан (функции Boomstream будут недоступны)")
        
        # Вывод ошибок
        if errors:
            print("\n" + "="*60)
            print("ОШИБКИ КОНФИГУРАЦИИ:")
            for error in errors:
                print(error)
            print("="*60 + "\n")
            sys.exit(1)
        
        # Вывод предупреждений
        if warnings:
            print("\n" + "="*60)
            print("ПРЕДУПРЕЖДЕНИЯ КОНФИГУРАЦИИ:")
            for warning in warnings:
                print(warning)
            print("="*60 + "\n")
        else:
            print("✅ Конфигурация проверена успешно")