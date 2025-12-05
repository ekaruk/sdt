# Stepik → Boomstream интеграция + мини-сайт (v2 с Telegram и auth_method)

## Что есть

- Скрипт синхронизации прогресса с Stepik (через API) и записи доступов в БД.
- Мини-веб-сайт на Flask:
  - /login — вход по email + пароль (под Boomstream-пароль) + заготовка для Telegram-логина.
  - /me — личный кабинет (список доступных видео, если есть в БД).
  - /logout — выход (сбрасывает сессию).

- Поддержка:
  - `session.permanent` + `app.permanent_session_lifetime` → "долгая" сессия.
  - `session["auth_method"]` — фиксируем способ входа (password/telegram и т.д.).
  - Заготовка под авторизацию через Telegram Login Widget (с проверкой подписи).

> В этом примере локальная регистрация не обязательна для боевого режима.
> Пользователей можно заводить напрямую в БД (email + boom_password + telegram_id и т.п.).

## Переменные окружения

Обязательные для работы синка и веба:

- SECRET_KEY — секрет для Flask-сессий.
- DATABASE_URL — строка подключения к БД.

Опциональные (но полезные):

- STEPIK_CLIENT_ID
- STEPIK_CLIENT_SECRET
- STEPIK_COURSE_ID
- BOOMSTREAM_API_KEY — ключ для API Boomstream (сейчас используется заглушка).
- TELEGRAM_BOT_TOKEN — токен вашего Telegram-бота (для проверки подписи Telegram Login Widget).

Пример для локального запуска (bash):

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

export SECRET_KEY="dev-secret"
export DATABASE_URL="sqlite:///local.db"
export STEPIK_CLIENT_ID="..."
export STEPIK_CLIENT_SECRET="..."
export STEPIK_COURSE_ID="123456"
export TELEGRAM_BOT_TOKEN="123456789:AAAA-BBB..."
```

## Локальный запуск

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# переменные окружения, см. выше
python web_app.py
```

Открыть: http://127.0.0.1:5000/login

Синк (при настроенных переменных для Stepik):

```bash
python sync_runner.py
```

## Кратко по авторизации

- Вход по email+пароль:
  - обрабатывается в `/login` (метод POST на тот же урл),
  - при успешном входе:
    - `session.permanent = True`
    - `session["user_id"] = user.id`
    - `session["auth_method"] = "password"`

- Вход через Telegram:
  - на странице логина можно повесить Telegram Login Widget с `data-auth-url="/login/telegram/callback"`,
  - callback `/login/telegram/callback` проверяет подпись данных,
  - ищет пользователя по `telegram_id` в таблице `users`,
  - если нашёл — делает то же самое, что и при логине по паролю:
    - `session.permanent = True`
    - `session["user_id"] = user.id`
    - `session["auth_method"] = "telegram"`

- Выход (`/logout`):
  - всегда делает `session.clear()`,
  - работает одинаково для любых способов входа.

## Render

- Web Service:
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `gunicorn web_app:app`

- Cron Job:
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `python sync_runner.py`
