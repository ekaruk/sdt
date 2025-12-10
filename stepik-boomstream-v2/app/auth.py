# app/auth.py
from app.db import SessionLocal
from app.models import User

import logging
logger = logging.getLogger(__name__)

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

def upsert_telegram_user(tg_user) -> None:
    """Создаёт или обновляет запись в таблице telegram_users по Telegram ID."""
    session = SessionLocal()
    try:
        db_tg = session.get(TelegramUser, tg_user.id)

        if db_tg is None:
            # новый пользователь
            db_tg = TelegramUser(
                id=tg_user.id,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                username=tg_user.username,
                phone=None,  # телефон можно дописать позже, если будешь его собирать
            )
            session.add(db_tg)
        else:
            # обновляем, если что-то поменялось
            changed = False
            if db_tg.first_name != tg_user.first_name:
                db_tg.first_name = tg_user.first_name
                changed = True
            if db_tg.last_name != tg_user.last_name:
                db_tg.last_name = tg_user.last_name
                changed = True
            if db_tg.username != tg_user.username:
                db_tg.username = tg_user.username
                changed = True
            # phone оставляем как есть (берёшь из CSV/формы), чтобы не затереть

            if not changed:
                # ничего не меняли — можно не дёргать commit
                session.commit()  # можно и убрать, если хочешь
                return

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(
            f"Ошибка при сохранении telegram_user ID={tg_user.id}: {e}",
            exc_info=True
        )    
    finally:
        session.close()
