# например, в отдельном скрипте, либо в модуле utils
import sys
from pathlib import Path
import logging

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stepik.stepik_api import StepikAPI
from app.models import User
from app.db import SessionLocal  # или откуда ты берёшь Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_video_access_for_all_users() -> None:
    api = StepikAPI()
    session = SessionLocal()

    try:
        # Берём всех пользователей, у которых есть stepik_user_id
        users = session.query(User).filter(User.video_access.is_(None), User.stepik_user_id.isnot(None)).all()

        logger.info("Найдено пользователей без video_access со stepik_user_id: %s", len(users))

        for user in users:
            
            logger.info("Обработка пользователя id=%s email=%s stepik_user_id=%s", user.id, user.email, user.stepik_user_id)
            # Если не заданы lesson/step – пропускаем (ничего обновлять не можем)
#            if user.stepik_lesson_id is None or user.stepik_step_id is None:
#                continue

            try:
                passed = api.is_exam_passed(
                    stepik_user_id=user.stepik_user_id,
                )
            except Exception as e:
                # Логируем, но не валим весь проход
                print(f"Ошибка при проверке пользователя id={user.id}: {e}")
                continue

            user.video_access = 1 if passed else 0
            logger.info(
                "✅ Установлен video_access=%s для email=%s - %s %s",
                user.video_access,
                user.email,
                user.last_name,
                user.first_name,
            )

        session.commit()
    finally:
        session.close()

if __name__ == "__main__":
    update_video_access_for_all_users()        
