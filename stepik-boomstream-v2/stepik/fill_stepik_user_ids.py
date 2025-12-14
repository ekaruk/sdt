import logging
import sys
from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session

from app.db import engine
from app.models import User
from stepik.stepik_api import StepikAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fill_missing_stepik_ids():
    api = StepikAPI()
    session = Session(bind=engine)

    try:
        users = (
            session.query(User)
            .filter(User.stepik_user_id.is_(None))
            .all()
        )

        logger.info("Найдено пользователей без stepik_user_id: %s", len(users))

        for user in users:
            email = user.email
            logger.info("Обработка пользователя id=%s email=%s", user.id, email)

            try:
                stepik_id = api.get_user_id_by_email(email)
            except ValueError as e:
                # 0 или >1 пользователей — логируем и пропускаем
                logger.warning(
                    "Пропуск пользователя email=%s: %s",
                    email,
                    str(e),
                )
                continue
            except Exception as e:
                # проблемы API / сети
                logger.error(
                    "Ошибка Stepik API для email=%s: %s",
                    email,
                    str(e),
                )
                continue

            user.stepik_user_id = stepik_id
            session.add(user)
            logger.info(
                "✅ Установлен stepik_user_id=%s для email=%s  - %s %s",
                stepik_id,
                email,
                user.last_name,
                user.first_name,    
            )

        session.commit()
        logger.info("✅ Обновление завершено успешно")

    except Exception:
        session.rollback()
        logger.exception("❌ Критическая ошибка, изменения отменены")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    fill_missing_stepik_ids()
