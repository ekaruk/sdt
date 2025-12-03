import requests
from typing import List, Dict
from .config import Config

STEPIK_API_BASE = "https://stepik.org/api"


class StepikClient:
    """
    Клиент для работы с Stepik API через client_credentials.
    Реальные поля в ответах нужно уточнить по /api/docs.
    """

    def __init__(self) -> None:
        self.client_id = Config.STEPIK_CLIENT_ID
        self.client_secret = Config.STEPIK_CLIENT_SECRET
        self.course_id = Config.STEPIK_COURSE_ID
        self._access_token: str | None = None

    def _auth(self) -> None:
        if self._access_token:
            return

        resp = requests.post(
            "https://stepik.org/oauth2/token/",
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]

    def _headers(self) -> Dict[str, str]:
        self._auth()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }

    def get_course_enrollments(self) -> List[Dict]:
        """
        Возвращает список записей о зачислении на курс.
        Здесь используется /api/course-enrollments?course=...
        """
        enrollments: List[Dict] = []
        page = 1

        while True:
            resp = requests.get(
                f"{STEPIK_API_BASE}/course-enrollments",
                headers=self._headers(),
                params={"course": self.course_id, "page": page},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            enrollments.extend(data.get("course-enrollments", []))

            meta = data.get("meta", {})
            if not meta.get("has_next"):
                break
            page += 1

        return enrollments

    def get_user(self, user_id: int) -> Dict:
        """
        Получение информации о пользователе.
        В реальности нужно проверить по /api/docs, какие поля доступны
        (email может быть не всегда).
        """
        resp = requests.get(
            f"{STEPIK_API_BASE}/users/{user_id}",
            headers=self._headers(),
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        users = data.get("users", [])
        return users[0] if users else {}

    def is_lesson_completed(self, user_id: int, lesson_id: int) -> bool:
        """
        Проверка, завершён ли урок:
        через прогресс "lesson-<lesson_id>-<user_id>".
        """
        progress_id = f"lesson-{lesson_id}-{user_id}"
        resp = requests.get(
            f"{STEPIK_API_BASE}/progresses",
            headers=self._headers(),
            params={"ids[]": progress_id},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        progresses = data.get("progresses", [])
        if not progresses:
            return False

        p = progresses[0]
        # Тут возможно другое имя поля, нужно проверить по реальному ответу:
        # is_passed / passed / score+cost
        return bool(p.get("is_passed") or p.get("passed") or False)
