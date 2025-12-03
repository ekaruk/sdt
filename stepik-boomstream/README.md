# Stepik → Boomstream интеграция + мини-сайт

## Что есть

- Скрипт синхронизации прогресса с Stepik (через API) и записи доступов в БД.
- Мини-веб-сайт на Flask:
  - /register — регистрация (email + пароль)
  - /login — логин
  - /me — личный кабинет (список доступных видео)

## Переменные окружения

Обязательные:

- SECRET_KEY — секрет для Flask-сессий
- DATABASE_URL — строка подключения к БД (Postgres, либо SQLite локально)
- STEPIK_CLIENT_ID
- STEPIK_CLIENT_SECRET
- STEPIK_COURSE_ID

Опционально:

- BOOMSTREAM_API_KEY — ключ для API Boomstream (пока заглушка)

## Локальный запуск

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

export SECRET_KEY="dev-secret"
export DATABASE_URL="sqlite:///local.db"
export STEPIK_CLIENT_ID="..."
export STEPIK_CLIENT_SECRET="..."
export STEPIK_COURSE_ID="123456"

python web_app.py
```

Открыть: http://127.0.0.1:5000/login

Синк:

```bash
python sync_runner.py
```

## Render

- Web Service:
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `gunicorn web_app:app`

- Cron Job:
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `python sync_runner.py`
