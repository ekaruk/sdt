from flask import Flask
from .db import Base, engine
from .voting import voting_bp


def create_app() -> Flask:
    app = Flask(__name__)

    # Инициализация БД: создаём таблицы, если их ещё нет
    Base.metadata.create_all(bind=engine)

    # Регистрация blueprint'а расписания
    app.register_blueprint(voting_bp)

    return app
