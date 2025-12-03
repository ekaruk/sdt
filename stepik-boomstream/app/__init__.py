from flask import Flask
from .config import Config
from .db import Base, engine
from . import models  # чтобы модели зарегистрировались
from .routes.auth import auth_bp
from .routes.dashboard import dashboard_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY

    # Создаём таблицы (для простоты, без миграций)
    Base.metadata.create_all(bind=engine)

    # Регистрируем blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    return app
