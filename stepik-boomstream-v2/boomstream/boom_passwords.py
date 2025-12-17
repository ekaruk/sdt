# например, app/scripts/fill_boom_passwords.py

import sys
from pathlib import Path
import secrets
import string
import logging
import requests
import os
import xml.etree.ElementTree as ET

# add project root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

#from dotenv import load_dotenv
from sqlalchemy.orm import Session
#from sqlalchemy import select

from app.models import User
from app.db import SessionLocal
from app.config import Config
# -----------------------------------------------------------------------------

#load_dotenv(ROOT / ".env")

BOOM_URL = "https://boomstream.com/api/ppv/addbuyer"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------------
def generate_password(length: int = 9) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# -----------------------------------------------------------------------------
# 1) функция ДЛЯ ОДНОГО пользователя
# -----------------------------------------------------------------------------
def process_one_user(session: Session, user: User) -> None:
#    password = generate_password()
#    media = get_media_code(session, user)

    params = {
        "apikey": Config.BOOMSTREAM_API_KEY,
        "code": Config.BOOMSTREAM_CODE_SUBSCRIPTION,
        "media": Config.BOOMSTREAM_MEDIA_CODE,
        "email": user.email,
        "name": f"{user.last_name} {user.first_name}",
        "notification": 0,
#        "hash": password ,  # ← простой вариант
    }

    logger.info("Boomstream: user_id=%s email=%s", user.id, user.email)

    response = requests.get(BOOM_URL, params=params, timeout=20)

    if not response.ok:
        raise RuntimeError(
            f"Boomstream HTTP error {response.status_code}: {response.text}"
        )

    # --- парсим XML ---
    try:
        root = ET.fromstring(response.text)
    except ET.ParseError as e:
        raise RuntimeError(f"Boomstream invalid XML response: {e}")

    status = root.findtext("Status")
    if status != "Success":
        message = root.findtext(".//Message")
        raise RuntimeError(f"Boomstream error: {message or 'Unknown error'}")

    password = root.findtext(".//Hash")
    if not password:
        raise RuntimeError("Boomstream response does not contain <Hash>")

    # --- сохраняем пароль ---
    user.boom_password = password

    logger.info(
        "✅ Boomstream success: user_id=%s email=%s password=%s",
        user.id,
        user.email,
        password,
    )


# -----------------------------------------------------------------------------
# 2) ОБЁРТКА — обходит таблицу
# -----------------------------------------------------------------------------
def fill_boom_passwords_for_all_users() -> None:
    session = SessionLocal()

    try:
        users = (
            session.query(User)
            .filter(User.video_access == 1)
            .all()
        )

        logger.info("Найдено пользователей с video_access=1: %s", len(users))
        for user in users:
            try:
                process_one_user(session, user)
                logger.info("✅ Обработан user_id=%s email=%s", user.id, user.email)
            except Exception as e:
                logger.error("❌ Ошибка user_id=%s: %s", user.id, e)
                session.rollback()
                continue

        session.commit()

    finally:
        session.close()


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    fill_boom_passwords_for_all_users()
