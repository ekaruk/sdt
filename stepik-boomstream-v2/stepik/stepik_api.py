import os
import json
import requests
from dotenv import load_dotenv


class StepikAPI:
    """
    Класс для работы с Stepik API.

    Пример использования:

        api = StepikAPI(group_id="12259213")

        user_id = api.get_user_id_by_email("user@example.com")
        full_name = api.get_user_full_name(user_id)
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        group_id: str | None = None,
        save_last_response: bool = False,
    ) -> None:
        load_dotenv()

        self.client_id = client_id or os.getenv("STEPIK_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("STEPIK_CLIENT_SECRET")
        self.group_id = group_id or os.getenv("STEPIK_GROUP_ID") or "12259213"

        if not self.client_id or not self.client_secret:
            raise RuntimeError(
                "Не заданы STEPIK_CLIENT_ID / STEPIK_CLIENT_SECRET "
                "ни в .env, ни в параметрах StepikAPI()."
            )

        self.save_last_response = save_last_response
        self._access_token: str | None = None

    # ----------- служебные методы -----------

    @property
    def access_token(self) -> str:
        """Лениво получаем и кэшируем токен доступа."""
        if self._access_token is None:
            self._access_token = self._request_access_token()
        return self._access_token

    def _request_access_token(self) -> str:
        """Запрос нового access_token у Stepik."""
        resp = requests.post(
            "https://stepik.org/oauth2/token/",
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
        )
        resp.raise_for_status()
        new_token = resp.json()["access_token"]
        print("Получен новый access_token:", new_token)
        return new_token

    def _save_response(self, data: dict, filename: str = "response.json") -> None:
        """Опционально сохраняем ответ API в файл для отладки."""
        if not self.save_last_response:
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    # ----------- публичные методы API -----------



    def get_user_id_by_email(self, email: str) -> int:
        """
        Ищет пользователя по email в указанной группе Stepik.

        Использует эндпоинт:
            GET /api/members?group=<group_id>&search=<email>

        Возвращает user_id, если найдена ровно 1 запись.
        Если записей 0 или >1 — выбрасывает ValueError.
        """
        url = "https://stepik.org/api/members"
        params = {
            "group": self.group_id,
            "search": email,
        }

        response = requests.get(url, headers=self._auth_headers(), params=params)
        if response.status_code != 200:
            raise RuntimeError(
                f"Ошибка запроса Stepik API: {response.status_code}, {response.text}"
            )

        data = response.json()
        self._save_response(data, filename="members_response.json")

        members = data.get("members", [])

        if len(members) == 0:
            raise ValueError("Ошибка: пользователь не найден в группе (0 записей).")

        if len(members) > 1:
            raise ValueError(
                f"Ошибка: найдено несколько записей ({len(members)}), ожидалась одна."
            )

        user_id = members[0]["user"]
        return user_id

    def get_user_full_name(self, user_id: int) -> str:
        """
        Получает полное имя пользователя по его user_id Stepik.

        Эндпоинт:
            GET /api/users/{user_id}

        Возвращает full_name.
        """
        url = f"https://stepik.org/api/users/{user_id}"
        print("Запрос:", url)

        response = requests.get(url, headers=self._auth_headers())
        if response.status_code != 200:
            raise RuntimeError(
                f"Ошибка запроса Stepik API: {response.status_code}, {response.text}"
            )

        data = response.json()
        self._save_response(data, filename="user_response.json")

        users = data.get("users", [])

        if len(users) == 0:
            raise ValueError("Ошибка: пользователь не найден (0 записей).")

        if len(users) > 1:
            raise ValueError(
                f"Ошибка: найдено несколько записей ({len(users)}), ожидалась одна."
            )

        full_name = users[0]["full_name"]
        return full_name

    def is_exam_passed(
        self,
        stepik_user_id: int,
        lesson_id: int = 2071930,
        step_position: int = 1,
        course_id: int = 247644,
    ) -> bool:
        """
        Проверяет, пройден ли шаг урока пользователем в указанном курсе.

        Используется эндпоинт:
            GET /api/course-grades?user=<user_id>&course=<course_id>

        В ответе берётся:
            "course-grades"[0]["results"][f"{lesson_id}-{step_position}"]["is_passed"]

        :param stepik_user_id: ID пользователя на Stepik.
        :param lesson_id: ID урока Stepik (например, 1859688).
        :param step_position: Позиция шага в уроке (1, 2, 3, ...).
        :param course_id: ID курса Stepik (по умолчанию 247644).
        :return: True, если шаг пройден, иначе False.
        """
        url = "https://stepik.org/api/course-grades"
        params = {
            "user": stepik_user_id,
            "course": course_id,
        }

        response = requests.get(url, headers=self._auth_headers(), params=params)
        if response.status_code != 200:
            raise RuntimeError(
                f"Ошибка запроса Stepik API: {response.status_code}, {response.text}"
            )

        data = response.json()
        # Опционально сохраняем ответ для отладки
        self._save_response(data, filename="course_grades_response.json")

        course_grades = data.get("course-grades", [])
        if not course_grades:
            # Нет данных по этому курсу/пользователю
            return False

        results = course_grades[0].get("results", {})
        key = f"{lesson_id}-{step_position}"

        step_info = results.get(key)
        if not step_info:
            # Нет такого урока/шага в результатах — считаем, что не пройден
            return False

        return bool(step_info.get("is_passed", False))

# ---------------- пример использования ----------------
if __name__ == "__main__":
    # Пример быстрого теста из командной строки.
    api = StepikAPI(group_id="12259213", save_last_response=True)

    try:
        user_id = api.get_user_id_by_email("ekaruk@gmail.com")
        print("Найден user_id =", user_id)
    except Exception as e:
        print("Ошибка при поиске по email:", e)
    else:
        try:
            full_name = api.get_user_full_name(user_id)
            print("Найден full_name =", full_name)
        except Exception as e:
            print("Ошибка при получении full_name:", e)
