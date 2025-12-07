# app/auth.py
from app.db import SessionLocal
from app.models import User


def get_user_by_telegram_id(telegram_id: int):
    """
    Возвращает объект User по telegram_id или None, если не найден.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        return user
    finally:
        db.close()
