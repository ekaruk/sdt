# app/auth.py
from flask import session, redirect, url_for, abort, request
from functools import wraps
from app.db import SessionLocal
from app.models import User, TelegramUser, ROLE_CURATOR, ROLE_ADMIN
from app.telegram_auth import validate_webapp_init_data
from app.config import Config

import logging
import time
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


def ensure_session_user(init_data: str = ""):
    """
    Ensure session has user_id, user_role, telegram_id if possible.
    Returns dict with user, user_id, user_role, telegram_id, tg_user.
 
    """

    cache_ts = session.get("user_cache_ts")
    now_ts = int(time.time())
    session_start_ts = Config.SESSION_START_TS
    if (
        not cache_ts 
        or cache_ts < session_start_ts
        or now_ts - cache_ts > 86400
    ):  
        session.pop("user_role", None)
        session.pop("telegram_id", None)
        session["user_cache_ts"] = now_ts
        if init_data:
           session.pop("user_id", None)
    

    user_id = session.get("user_id")
    user_role = session.get("user_role")
    telegram_id = session.get("telegram_id")
    user = None
    tg_user = None

    if (
        user_id
        and user_role is not None
        and telegram_id is not None
    ):
        return {
            "user": None,
            "user_id": user_id,
            "user_role": user_role,
            "telegram_id": telegram_id,
            "tg_user": None,
        }

    db = SessionLocal()
    try:
        if user_id:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                session.pop("user_id", None)
                session.pop("user_role", None)
                session.pop("telegram_id", None)
                print(f"[DEBUG] return 2") 
                return {
                    "user": None,
                    "user_id": None,
                    "user_role": None,
                    "telegram_id": None,
                    "tg_user": None,
                }
            session["user_role"] = user.role
            session["telegram_id"] = user.telegram_id
            session["user_cache_ts"] = now_ts
            print(f"[DEBUG] return 3") 
            return {
                "user": user,
                "user_id": user.id,
                "user_role": user.role,
                "telegram_id": user.telegram_id,
                "tg_user": None,
            }

        if init_data:
            tg_user = validate_webapp_init_data(init_data)
            print(f"[DEBUG] tg_user from init_data: {tg_user}") 
            if tg_user and tg_user.get("id"):
                telegram_id = tg_user["id"]
                upsert_telegram_user(tg_user)
                session["telegram_id"] = telegram_id
                user = db.query(User).filter_by(telegram_id=telegram_id).first()
                print(
                    f"[DEBUG] ensure init_data:{session}, user_id:{user.id if user else None}, "
                    f"user_role:{user.role if user else None}, telegram_id:{telegram_id}, "
                    f"session_start_ts:{session_start_ts}, cache_ts{cache_ts}, now_ts{now_ts}, "
                    f"init_data:{init_data}"
                )

                if user:
                    session["user_id"] = user.id
                    session["user_role"] = user.role
                    session["user_cache_ts"] = now_ts
                    session.permanent = True
                    print(f"[DEBUG] return 4") 
                    return {
                        "user": user,
                        "user_id": user.id,
                        "user_role": user.role,
                        "telegram_id": telegram_id,
                        "tg_user": tg_user,
                    }
        print(f"[DEBUG] return 5") 
        return {
            "user": None,
            "user_id": session.get("user_id"),
            "user_role": session.get("user_role"),
            "telegram_id": session.get("telegram_id"),
            "tg_user": tg_user,
        }
    finally:
        db.close()
