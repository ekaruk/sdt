from typing import Dict, List
from sqlalchemy.orm import Session
from .db import SessionLocal
from .models import User, VideoGrant
from .stepik_client import StepikClient
from .boomstream_client import BoomstreamClient

# Маппинг: какой урок Stepik → какие ресурсы Boomstream
LESSON_TO_RESOURCE: Dict[int, List[str]] = {
    # пример: lesson_id: [resource_id1, resource_id2]
    11111: ["video_abc"],
    22222: ["video_def"],
}


def run_sync() -> None:
    """
    Основная функция синхронизации:
    - получаем зачисленных на курс из Stepik
    - определяем, завершены ли уроки
    - для завершённых уроков выдаём доступ к ресурсам Boomstream
    - записываем в таблицу VideoGrant
    """
    print("[SYNC] Запуск синхронизации")

    stepik = StepikClient()
    boom = BoomstreamClient()
    db: Session = SessionLocal()

    try:
        enrollments = stepik.get_course_enrollments()
        print(f"[SYNC] Найдено зачислений: {len(enrollments)}")

        for enr in enrollments:
            stepik_user_id = enr.get("user")
            if not stepik_user_id:
                continue

            # Получаем данные пользователя из Stepik
            stepik_user = stepik.get_user(stepik_user_id)
            email = stepik_user.get("email")

            if not email:
                # Если email недоступен, пропускаем (нужен для связи с локальным User и Boomstream)
                print(f"[SYNC] Нет email у stepik_user_id={stepik_user_id}, пропуск")
                continue

            # Локальный User
            user = db.query(User).filter_by(email=email).first()
            if not user:
                # Можно автоматически создавать запись локального пользователя,
                # либо пропускать — зависит от бизнес-логики.
                print(f"[SYNC] Локальный пользователь с email={email} не найден, создаю")
                user = User(email=email, password_hash="!", stepik_user_id=stepik_user_id)
                db.add(user)
                db.commit()
                db.refresh(user)

            # Проверяем все нужные уроки
            for lesson_id, resources in LESSON_TO_RESOURCE.items():
                if not resources:
                    continue

                completed = stepik.is_lesson_completed(stepik_user_id, lesson_id)
                if not completed:
                    continue

                for res in resources:
                    exists = (
                        db.query(VideoGrant)
                        .filter_by(
                            user_id=user.id,
                            stepik_lesson_id=lesson_id,
                            boomstream_resource_id=res,
                        )
                        .first()
                    )
                    if exists:
                        continue

                    # Выдаём доступ в Boomstream
                    boom.grant_access(user.email, [res])

                    # Записываем грант в БД
                    grant = VideoGrant(
                        user_id=user.id,
                        stepik_lesson_id=lesson_id,
                        boomstream_resource_id=res,
                    )
                    db.add(grant)

        db.commit()
        print("[SYNC] Синхронизация завершена")
    finally:
        db.close()
