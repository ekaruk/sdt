from datetime import timedelta

import threading
import time

from flask import Flask
from .config import Config
from .db import Base, engine
from . import models  # чтобы модели зарегистрировались
from .routes.auth import auth_bp
from .routes.dashboard import dashboard_bp
from .routes.webapp_admin import admin_bp
from .routes.questions import questions_bp
from .routes.boom_media import boom_media_bp
from .similar_cache import warmup_similar_cache_async

def create_app() -> Flask:
    # Проверяем конфигурацию перед запуском
    Config.validate()
    
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY

    # Долгая сессия (можно поменять срок)
    app.permanent_session_lifetime = timedelta(days=30)


    # Создаём таблицы (для простоты, без миграций)
    Base.metadata.create_all(bind=engine)

    # Проверяем и создаём votes_count + триггер, если нужно
    from utils.ensure_votes_count_trigger import ensure_votes_count_trigger
    ensure_votes_count_trigger()
    from utils.ensure_telegram_notice_columns import ensure_telegram_notice_columns
    ensure_telegram_notice_columns()

    warmup_similar_cache_async()

    from .routes.questions import auto_close_due_discussions, auto_publish_daily_question

    def _auto_close_loop():
        while True:
            try:
                with app.app_context():
                    auto_close_due_discussions()
            except Exception as exc:
                print(f"[AutoClose] Error: {exc}")
            time.sleep(3600)

    threading.Thread(target=_auto_close_loop, daemon=True).start()

    def _auto_publish_loop():
        while True:
            try:
                with app.app_context():
                    auto_publish_daily_question()
            except Exception as exc:
                print(f"[AutoPublish] Error: {exc}")
            time.sleep(10800)

    threading.Thread(target=_auto_publish_loop, daemon=True).start()

    # Регистрируем blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(boom_media_bp)

    return app
