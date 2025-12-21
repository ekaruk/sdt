# Telegram Mini App - Инструкция по развертыванию

## Описание

Telegram Mini App для системы вопросов и голосования. Позволяет студентам просматривать вопросы, голосовать за них и фильтровать по темам/статусам прямо в Telegram.

## Функционал

✅ Просмотр списка вопросов с фильтрами
✅ Голосование за вопросы (1 голос на пользователя)
✅ Фильтрация по темам курса (разделам)
✅ Фильтрация по статусу (VOTING, SCHEDULED, POSTED, CLOSED, ARCHIVED)
✅ Фильтрация по периоду (сегодня, неделя, месяц, все время)
✅ Адаптивный дизайн под темы Telegram
✅ Аутентификация через Telegram initData

## Архитектура

### Frontend
- Telegram WebApp SDK
- Vanilla JavaScript (AJAX)
- Адаптация под тему Telegram (tg.themeParams)
- Мобильный дизайн (card layout)

### Backend
- Flask роут: `/questions/miniapp`
- REST API: `/api/questions`, `/api/modules`
- Аутентификация через `X-Telegram-Init-Data` header
- PostgreSQL база данных

### Модели
- `Question`: вопросы с текстом, статусом, датами
- `QuestionVote`: голоса (composite PK: question_id + telegram_user_id)
- `QuestionStepikModule`: связь вопросов с темами курса
- `TelegramUser`: пользователи Telegram
- `TelegramTopic`: топики в Telegram Forum
- `QuestionAnswer`: ответы на закрытые вопросы

## Развертывание в Production

### 1. Deploy на Render.com

Веб-приложение уже развернуто на Render:
- URL: https://stepik-boomstream-v2.onrender.com
- Mini App URL: https://stepik-boomstream-v2.onrender.com/questions/miniapp

### 2. Настройка Telegram Bot

Бот уже настроен в файле `bot.py`:

```python
BOT_TOKEN = "8570792426:AAHlF4WaDjh-0NyqBsmngFCVM9QQazkVudY"
QUESTIONS_MINIAPP_URL = "https://stepik-boomstream-v2.onrender.com/questions/miniapp"
```

Команда `/questions` открывает Mini App через кнопку с WebAppInfo.

### 3. Запуск бота

```powershell
# В отдельном терминале
python bot.py
```

Или используйте существующий скрипт:
```powershell
python bots/bot.py
```

### 4. Тестирование в Telegram

1. Откройте бота в Telegram: @YourBotUsername
2. Отправьте команду `/questions`
3. Нажмите на кнопку "📋 Вопросы студентов"
4. Mini App откроется в полноэкранном режиме
5. Проверьте фильтры, голосование, отображение

### 5. Проверка аутентификации

Mini App получает данные пользователя через Telegram WebApp API:

```javascript
const tg = window.Telegram.WebApp;
const initData = tg.initData; // Подписанные данные от Telegram

// Отправляем в заголовке каждого запроса
headers: {
    'X-Telegram-Init-Data': initData
}
```

Backend извлекает `telegram_user_id` из initData:

```python
init_data = request.headers.get('X-Telegram-Init-Data')
params = dict(item.split('=') for item in init_data.split('&') if '=' in item)
user_data = json.loads(urllib.parse.unquote(params['user']))
telegram_user_id = user_data.get('id')
```

## Локальное тестирование

Для локального тестирования Mini App в браузере:

```powershell
# Запустите веб-сервер
python web_app.py

# Откройте в браузере
http://127.0.0.1:5000/questions/miniapp
```

**Важно**: В браузере не будет работать Telegram WebApp SDK и аутентификация через initData. Для полного тестирования нужен настоящий Telegram клиент.

### Использование ngrok для локального тестирования

Чтобы протестировать локальную версию в реальном Telegram:

```powershell
# Установите ngrok
# https://ngrok.com/download

# Запустите туннель
ngrok http 5000

# Скопируйте https URL из ngrok (например, https://abc123.ngrok.io)
# Обновите QUESTIONS_MINIAPP_URL в bot.py:
QUESTIONS_MINIAPP_URL = "https://abc123.ngrok.io/questions/miniapp"

# Перезапустите бота
python bot.py
```

Теперь Mini App будет работать с локальным сервером через ngrok.

## Безопасность

### Валидация initData

⚠️ **TODO**: Реализовать полную валидацию HMAC подписи initData

Текущая реализация извлекает данные без проверки подписи. Для production необходимо:

```python
import hmac
import hashlib

def validate_init_data(init_data: str, bot_token: str) -> dict:
    """
    Валидирует initData от Telegram и возвращает данные пользователя
    """
    params = dict(item.split('=', 1) for item in init_data.split('&') if '=' in item)
    
    # Извлекаем hash
    data_check_string_items = []
    for key in sorted(params.keys()):
        if key != 'hash':
            data_check_string_items.append(f"{key}={params[key]}")
    
    data_check_string = '\n'.join(data_check_string_items)
    
    # Создаем secret_key
    secret_key = hmac.new(
        "WebAppData".encode(), 
        bot_token.encode(), 
        hashlib.sha256
    ).digest()
    
    # Проверяем hash
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if expected_hash != params.get('hash'):
        raise ValueError("Invalid initData signature")
    
    # Извлекаем данные пользователя
    user_data = json.loads(urllib.parse.unquote(params['user']))
    return user_data
```

Добавьте эту функцию в `app/telegram_auth.py` и используйте в API endpoints.

## Мониторинг

### Логи на Render.com

1. Откройте дашборд: https://dashboard.render.com
2. Выберите ваш Web Service
3. Перейдите на вкладку "Logs"
4. Отслеживайте запросы к `/api/questions` и `/questions/miniapp`

### Проверка работы API

```powershell
# Проверка списка вопросов
curl https://stepik-boomstream-v2.onrender.com/api/questions

# Проверка списка модулей
curl https://stepik-boomstream-v2.onrender.com/api/modules
```

## Обновление и развертывание

### Автоматическое развертывание

Render.com автоматически деплоит при каждом push в main ветку:

```bash
git add .
git commit -m "Update Mini App"
git push origin main
```

### Ручное развертывание

1. Откройте Render.com Dashboard
2. Выберите Web Service
3. Нажмите "Manual Deploy" → "Deploy latest commit"

## Структура файлов

```
app/
  routes/
    questions.py          # Mini App роут + API endpoints
  models.py              # Database models
  telegram_auth.py       # TODO: HMAC validation
bot.py                   # Telegram Bot с командой /questions
MINIAPP_DEPLOYMENT.md    # Этот файл
```

## Следующие шаги

- [ ] Реализовать полную валидацию initData (HMAC signature)
- [ ] Добавить обработку ошибок в Mini App (например, сеть недоступна)
- [ ] Добавить загрузку следующих страниц (pagination)
- [ ] Добавить уведомления через Telegram Bot (новые вопросы, ответы)
- [ ] Добавить MainButton для быстрых действий
- [ ] Добавить BackButton для навигации
- [ ] Добавить Haptic Feedback при голосовании
- [ ] Оптимизировать запросы к API (кэширование)

## Troubleshooting

### Mini App не открывается в Telegram

1. Проверьте URL в `bot.py` (должен быть HTTPS)
2. Проверьте, что веб-сервер запущен на Render.com
3. Проверьте логи Render.com на наличие ошибок
4. Убедитесь, что бот запущен (`python bot.py`)

### Голосование не работает

1. Проверьте, что initData передается в заголовке `X-Telegram-Init-Data`
2. Проверьте логи Flask на наличие ошибок 401/500
3. Убедитесь, что пользователь существует в таблице `telegram_users`

### Фильтры не работают

1. Проверьте Developer Tools → Console на наличие JS ошибок
2. Проверьте Network tab, что запросы к `/api/questions` отправляются с правильными параметрами
3. Проверьте формат query string: `?topic=561993&status=voting&period=week`

## Контакты и поддержка

Для вопросов по развертыванию и настройке обращайтесь к разработчику.
