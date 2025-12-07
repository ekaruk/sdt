# Конспект проекта: Stepik → Boomstream → Telegram → Webapp → Render

---

## 1. Цель проекта

Создать систему, которая:

- получает прогресс пользователя на Stepik;
- открывает доступ к видео на Boomstream;
- показывает прогресс и уроки на сайте (Flask);
- позволяет пользоваться курсом через Telegram-бота и Telegram WebApp;
- хранит данные в PostgreSQL/SQLite;
- работает на Render.com.

---

## 2. Архитектура проекта

### Блоки:

1. Stepik API — получение студентов и прогресса.
2. Boomstream — показ защищённых видео.
3. Flask-сайт — личный кабинет, уроки, WebApp.
4. Telegram-бот — меню курса, запуск WebApp.
5. Общая база данных.
6. Deploy в Render.com.

---

## 3. Интеграция со Stepik

### Авторизация
OAuth2 access token.

### Получение участников:
GET https://stepik.org/api/members?group=<id>

markdown
Copy code

### Проверка прохождения:
1. Получить steps урока.
2. Для каждого step получить progress ID.
3. Запрашивать:
GET https://stepik.org/api/progresses/<progress_id>

yaml
Copy code
4. Если `is_passed = true` — открывать доступ к видео.

---

## 4. Интеграция Boomstream

- Каждое видео имеет код вида `HOP3CJoH`.
- Вставка видео:
```html
<iframe src="https://boomstream.com/iframe/<code>"></iframe>
В таблицу уроков добавлено поле boom_media.

5. Структура базы данных
Таблица users
поле	тип	описание
id	int PK	
email	str uniq	email из Boomstream
boom_password	str	9-значный пароль
stepik_user_id	int	привязка Stepik
telegram_id	int	привязка Telegram
google_sub	str	идентификатор Google
first_name	str	
last_name	str	
created_at	datetime	

Таблица passwords
| user_id | password | end_date | active |

Таблица stepik_modules
| id | title | position |

Таблица stepik_lessons
| id | module_id | title | position | boom_media |

Таблица telegram_users
| id | first_name | last_name | username | phone |

6. Структура файлов проекта
markdown
Copy code
app/
    __init__.py
    db.py
    models.py
    auth.py
    routes.py
    telegram_webapp_routes.py
bots/
    bot_dev.py
    bot_prod.py
utils/
    create_tables.py
    dump_load.py
    import_boom_users.py
    import_telegram_users.py
stepik_client.py
boomstream_client.py
menu_tree.py
render.yaml
7. Импорт / экспорт данных
Экспорт:
lua
Copy code
python utils/dump_load.py dump dump.json
Импорт:
pgsql
Copy code
python utils/dump_load.py import dump.json
Особенности:
SQLite требует преобразование строки → datetime.

Экспорт не включает отсутствующие поля.

8. Импорт CSV
Boomstream-пользователи
Обновляет email, имя, фамилию, boom_password.

Telegram-группа
Используется Telethon:

python
Copy code
participants = await client.get_participants(chat)
9. Telegram-бот
Возможности:
показать меню курса;

открыть урок;

перейти на Stepik;

открыть Boomstream;

запуск Telegram WebApp;

авторизация по telegram_id.

Telegram WebApp:
открывает сайт внутри Telegram;

сайт получает initData;

пользователь определяется по telegram_id.

Telegram Login Widget:
работает если домен добавлен в BotFather;

требует входа в Telegram Web.

10. menu_tree.py
Содержит дерево модулей и уроков.

Формат урока:

python
Copy code
{
    "title": "Урок 1",
    "lesson_id": 1855854,
    "boom_media": "RPBloIDb",
    "parent": "sec_561993"
}
Мы добавили boom_media для каждого урока.

11. Render.com
Сервисы:
Web Service (Flask + gunicorn)

Worker (Telegram bot)

PostgreSQL база

Переменные окружения:
DATABASE_URL

TELEGRAM_BOT_TOKEN_DEV

TELEGRAM_BOT_TOKEN_PROD

STEPIC_CLIENT_ID

STEPIC_SECRET

BOOMSTREAM_SECRET

APP_DOMAIN

12. Локальная разработка
Flask:
arduino
Copy code
export FLASK_ENV=development
python app.py
Telegram-бот:
yaml
Copy code
ngrok http 5000
База:
локально SQLite

продакшн: PostgreSQL

13. Основные проблемы и решения
Stepik API → нужно правильное формирование заголовков.

ReqBin → не должен содержать заголовок Host.

Длинный menu_tree.py → аккуратное обновление boom_media.

Ошибка SQLite с datetime → обработка строк.

Telegram ID не загружались → исправлено через обновление по email_list_id.

WebApp не открывался → домен не был добавлен в BotFather.

Множество версий уроков (например "часть 1/2") → корректное сопоставление media.

14. Авторизация
Email + пароль (Boomstream)
boom_password всегда 9 цифр.

Telegram Login Widget
ini
Copy code
data-auth-url="https://domain/login/telegram/callback"
Telegram WebApp
сайт получает telegram_id из initData;

быстрый вход без пароля.

15. Важные выводы
Бот и сайт используют одну и ту же БД.

Авторизация WebApp полностью автоматическая.

Нужны два бота: dev и prod.

Пути выносятся в переменные окружения.

Все уроки имеют boom_media.

16. Что этот файл позволяет восстановить
Загрузив этот Markdown-файл в новый чат, AI сможет восстановить:

структуру БД,

архитектуру проекта,

Telegram-бота,

Stepik-интеграцию,

WebApp,

menu_tree,

скрипты импорта/экспорта,

работу Boomstream,

конфигурацию Render.