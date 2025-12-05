import requests
import json
import os


from dotenv import load_dotenv

from openai import OpenAI

# ---------------- НАСТРОЙКИ ----------------






def get_access_token():
    
    load_dotenv()

    STEPIK_CLIENT_ID = os.getenv("STEPIK_CLIENT_ID")
    STEPIK_CLIENT_SECRET = os.getenv("STEPIK_CLIENT_SECRET")
    
    resp = requests.post(
        "https://stepik.org/oauth2/token/",
        data={"grant_type": "client_credentials"},
        auth=(STEPIK_CLIENT_ID, STEPIK_CLIENT_SECRET)
    )
    resp.raise_for_status()
    new_token = resp.json()["access_token"]
    print("new_token:", new_token)

    return new_token

def get_user_from_email(email: str, access_token: str) -> int:
    """
    Делает запрос к Stepik API:
    /api/members?group=<group_id>&search=<email>

    Возвращает user_id, если найдена ровно одна запись.
    Иначе поднимает исключение.
    """

    group_id = "12259213"
    url = "https://stepik.org/api/members"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    params = {
        "group": group_id,
        "search": email
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise RuntimeError(f"Ошибка запроса Stepik API: {response.status_code}, {response.text}")

    data = response.json()

    # Полный путь к каталогу, где лежит сам скрипт
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Путь к файлу
    file_path = os.path.join(script_dir, "response.json")

    # Сохраняем в файл
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


    members = data.get("members", [])

    if len(members) == 0:
        raise ValueError("Ошибка: пользователь не найден в группе (0 записей).")

    if len(members) > 1:
        raise ValueError(f"Ошибка: найдено несколько записей ({len(members)}), ожидалась одна.")

    # единственная запись
    user_id =members[0]["user"]

    return user_id


def get_user_full_name_from_id(user_id: int, access_token: str) -> str:
    """
    Делает запрос к Stepik API:
    /api/members?group=<group_id>&search=<email>

    Возвращает user_id, если найдена ровно одна запись.
    Иначе поднимает исключение.
    """

    url = f"https://stepik.org/api/users/{user_id}"
    print("url:", url)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Ошибка запроса Stepik API: {response.status_code}, {response.text}")

    data = response.json()

    # Полный путь к каталогу, где лежит сам скрипт
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Путь к файлу
    file_path = os.path.join(script_dir, "response.json")

    # Сохраняем в файл
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


    users = data.get("users", [])

    if len(users) == 0:
        raise ValueError("Ошибка: пользователь не найден в группе (0 записей).")

    if len(users) > 1:
        raise ValueError(f"Ошибка: найдено несколько записей ({len(members)}), ожидалась одна.")

    # единственная запись
    full_name =users[0]["full_name"]

    return full_name

# ---------------- ТОЧКА ВХОДА ----------------
if __name__ == "__main__":
    token = get_access_token()

    try:
        user_id = get_user_from_email("ekaruk@gmail.com", token)
        print("Найден user_id =", user_id)
    except Exception as e:
        print("Ошибка:", e)

    try:
        full_name = get_user_full_name_from_id(user_id, token)
        print("Найден full_name =", full_name)
    except Exception as e:
        print("Ошибка:", e)        