# stepik_api.py (или твой GetUserId.py, если там уже класс StepikAPI)

import requests
import logging

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import Base, SessionLocal, engine
from app.models import StepikModule, StepikLesson
from app.config import Config

from stepik.stepik_api import StepikAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StepikTablesAPI:
    BASE_URL = "https://stepik.org/api"
    DEFAULT_COURSE_ID = 247644

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id or Config.STEPIK_CLIENT_ID
        self.client_secret = client_secret or Config.STEPIK_CLIENT_SECRET
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Нужны STEPIK_CLIENT_ID и STEPIK_CLIENT_SECRET в конфигурации")
        self._access_token: str | None = None

    # ======== базовая авторизация ========

    @property
    def access_token(self) -> str:
        if self._access_token is None:
            self._access_token = self._request_access_token()
        return self._access_token

    def _request_access_token(self) -> str:
        resp = requests.post(
            "https://stepik.org/oauth2/token/",
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    # ======== маленькие обёртки над API ========

    def get_course(self, course_id: int) -> dict:
        url = f"{self.BASE_URL}/courses/{course_id}"
        r = requests.get(url, headers=self._auth_headers())
        r.raise_for_status()
        data = r.json()
        return data["courses"][0]

    def get_section(self, section_id: int) -> dict:
        url = f"{self.BASE_URL}/sections/{section_id}"
        r = requests.get(url, headers=self._auth_headers())
        r.raise_for_status()
        data = r.json()
        return data["sections"][0]

    def get_unit(self, unit_id: int) -> dict:
        url = f"{self.BASE_URL}/units/{unit_id}"
        r = requests.get(url, headers=self._auth_headers())
        r.raise_for_status()
        data = r.json()
        return data["units"][0]

    def get_lesson(self, lesson_id: int) -> dict:
        url = f"{self.BASE_URL}/lessons/{lesson_id}"
        r = requests.get(url, headers=self._auth_headers())
        r.raise_for_status()
        data = r.json()
        return data["lessons"][0]
    def get_lesson_steps(self, lesson_id: int) -> dict:
        url = f"{self.BASE_URL}/steps?lesson={lesson_id}"
        r = requests.get(url, headers=self._auth_headers())
        r.raise_for_status()
        data = r.json()
        return data["steps"]
    # ======== основной метод: заполнение таблиц ========

    def sync_course_structure_to_db(
        self,
        course_id: int | None = None,
        clear_before: bool = False,
    ) -> None:
        """
        Подтягивает структуру курса (модули и уроки) из Stepik
        и заполняет таблицы stepik_modules и stepik_lessons.

        Логика:
          - /courses/{course_id} -> sections[]
          - для каждого section:
              /sections/{id} -> id, title, position, units[]
              создать/обновить StepikModule
              для каждого unit:
                 /units/{id} -> lesson, position
                 /lessons/{lesson} -> id, title
                 создать/обновить StepikLesson
        """
        course_id = course_id or self.DEFAULT_COURSE_ID

        db = SessionLocal()
        try:
            if clear_before:
                # сначала чистим уроки, потом модули (из-за FK)
                db.query(StepikLesson).delete()
                db.query(StepikModule).delete()
                db.commit()

            # 1. Курс -> список секций
            course = self.get_course(course_id)
            section_ids = course.get("sections", [])

            for section_id in section_ids:
                section = self.get_section(section_id)

                module_id = section["id"]
                module_title = section.get("title", "")
                module_position = section.get("position", 0)
                unit_ids = section.get("units", [])

                logger.info("Обработка модуля %s", module_title)
                # 2. создаём/обновляем модуль
                module = db.get(StepikModule, module_id)
                if module is None:
                    module = StepikModule(
                        id=module_id,
                        title=module_title,
                        position=module_position,
                    )
                    db.add(module)
                else:
                    module.title = module_title
                    module.position = module_position

                # 3. по всем юнитам внутри модуля
                for unit_id in unit_ids:
                    unit = self.get_unit(unit_id)

                    lesson_id = unit["lesson"]
                    lesson_position = unit.get("position", 0)

                    # запрос урока
                    lesson_data = self.get_lesson(lesson_id)
                    lesson_title = lesson_data.get("title", "")
                    lesson_steps = self.get_lesson_steps(lesson_id)
                    steps_amount = len(lesson_steps) 
                    # создаём/обновляем урок
                    lesson = db.get(StepikLesson, lesson_id)
                    if lesson is None:
                        lesson = StepikLesson(
                            id=lesson_id,
                            module_id=module_id,
                            title=lesson_title,
                            position=lesson_position,
                            steps_amount=steps_amount,
                        )
                        db.add(lesson)
                    else:
                        lesson.module_id = module_id
                        #lesson.title = lesson_title
                        lesson.position = lesson_position
                        lesson.steps_amount = steps_amount

            db.commit()
            print("Структура курса успешно синхронизирована с БД.")
        finally:
            db.close()


if __name__ == "__main__":
    # на всякий случай убедиться, что таблицы созданы
    Base.metadata.create_all(bind=engine)

    api = StepikTablesAPI()
    api.sync_course_structure_to_db(clear_before=True)