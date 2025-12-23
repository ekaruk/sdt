# app/auth.py
from flask import session, redirect, url_for, abort, request
from functools import wraps
from app.db import SessionLocal
from app.models import User, TelegramUser, ROLE_CURATOR, ROLE_ADMIN

import logging
logger = logging.getLogger(__name__)


def login_required(f):
    """Декоратор: требует авторизации пользователя."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def curator_required(f):
    """Декоратор: требует прав куратора (role >= 1)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        
        # Если не залогинен - редирект на логин
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Проверяем роль
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            if not user or user.role < ROLE_CURATOR:
                abort(403, description="У вас недостаточно прав для доступа к этой странице")
        finally:
            db.close()
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Декоратор: требует прав администратора (role >= 2)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        
        # Если не залогинен - редирект на логин
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Проверяем роль
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            if not user or user.role < ROLE_ADMIN:
                abort(403, description="У вас недостаточно прав для доступа к этой странице")
        finally:
            db.close()
        
        return f(*args, **kwargs)
    return decorated_function


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
    def _tg_get(obj, key):
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    tg_user_id = _tg_get(tg_user, "id")
    if not tg_user_id:
        return

    session = SessionLocal()
    try:
        db_tg = session.get(TelegramUser, tg_user_id)

        if db_tg is None:
            # Новый пользователь
            db_tg = TelegramUser(
                id=tg_user_id,
                first_name=_tg_get(tg_user, "first_name"),
                last_name=_tg_get(tg_user, "last_name"),
                username=_tg_get(tg_user, "username"),
                phone=None,  # Телефон может приходить отдельно (CSV/импорт)
            )
            session.add(db_tg)
        else:
            # Обновляем, если что-то изменилось
            changed = False
            first_name = _tg_get(tg_user, "first_name")
            last_name = _tg_get(tg_user, "last_name")
            username = _tg_get(tg_user, "username")
            if db_tg.first_name != first_name:
                db_tg.first_name = first_name
                changed = True
            if db_tg.last_name != last_name:
                db_tg.last_name = last_name
                changed = True
            if db_tg.username != username:
                db_tg.username = username
                changed = True
            # phone не обновляем здесь

            if not changed:
                session.commit()
                return

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(
            f"Ошибка при сохранении telegram_user ID={tg_user_id}: {e}",
            exc_info=True
        )
    finally:
        session.close()
