import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import SessionLocal
from app.models import StepikModule, StepikLesson


def delete_module(module_id: int):
    """Удаление модуля и всех связанных уроков."""
    db = SessionLocal()

    try:
        module = db.query(StepikModule).filter(StepikModule.id == module_id).first()

        if module is None:
            print(f"Модуль {module_id} не найден.")
            return

        # Покажем, сколько уроков будет удалено
        lessons_count = db.query(StepikLesson).filter(
            StepikLesson.module_id == module_id
        ).count()

        print(f"Удаляем модуль id={module_id}, уроков: {lessons_count}")

        # Удаление с каскадом (если в модели стоит cascade="all, delete-orphan")
        db.delete(module)
        db.commit()

        print("Удаление завершено.")

    except Exception as e:
        db.rollback()
        print("Ошибка:", e)

    finally:
        db.close()


if __name__ == "__main__":
    # Укажи ID модуля, который хочешь удалить
    delete_module(615126)
delete_module(563095)
delete_module(563095)
delete_module(617613)
delete_module(619524)
delete_module(619634)