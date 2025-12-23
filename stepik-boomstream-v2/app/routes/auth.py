from flask import Blueprint, request, render_template_string, redirect, session, url_for
from ..db import SessionLocal
from ..models import User
from ..telegram_auth import verify_telegram_auth
from ..config import Config

auth_bp = Blueprint("auth", __name__)

# Получаем домен приложения из Config или автоматически из request
def get_app_domain():
    # Приоритет: переменная из Config.APP_DOMAIN
    if Config.APP_DOMAIN:
        return Config.APP_DOMAIN.rstrip('/')
    
    # Fallback: определяем автоматически из текущего запроса
    if request:
        # request.host_url возвращает полный URL с протоколом (http:// или https://)
        return request.host_url.rstrip('/')
    
    # Последний fallback для случаев вне контекста запроса
    return 'http://localhost:5000'

LOGIN_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Вход</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .login-container {
      background: white;
      padding: 40px;
      border-radius: 10px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      text-align: center;
      max-width: 400px;
    }
    h1 {
      margin: 0 0 10px 0;
      color: #333;
    }
    p {
      color: #666;
      margin: 0 0 30px 0;
    }
    #telegram-widget-container {
      display: inline-block;
    }
  </style>
</head>
<body>
  <div class="login-container">
    <h1>Вход в систему</h1>
    <p>Для входа используйте свой Telegram аккаунт</p>
  
  <div id="telegram-widget-container">
        <script async src="https://telegram.org/js/telegram-widget.js?22"
          data-telegram-login="{{ telegram_bot_username }}"
          data-size="large"
          data-userpic="false"
          data-request-access="write"
          data-onauth="onTelegramAuth(user)">
        </script>
  </div>
  
  <script type="text/javascript">
    function onTelegramAuth(user) {
      
      // Отправляем данные на сервер через относительный URL
      const formData = new URLSearchParams();
      for (const key in user) {
        formData.append(key, user[key]);
      }
      
      const url = '/login/telegram/callback';
      
      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
        credentials: 'same-origin'
      })
      .then(response => {
        if (response.ok) {
          window.location.href = '/me';
        } else {
          return response.text().then(text => {
            alert('Ошибка авторизации (код ' + response.status + '): ' + text);
          });
        }
      })
      .catch(error => {
        alert('Ошибка при отправке данных на сервер');
      });
    }
  </script>
  </div>
</body>
</html>
"""


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        # Если уже авторизован — сразу в кабинет
        if session.get("user_id"):
            return redirect("/me")
        return render_template_string(LOGIN_TEMPLATE, error=None, app_domain=get_app_domain(), telegram_bot_username=Config.TELEGRAM_BOT_USERNAME)

    # POST: вход по email + пароль (Boomstream-пароль, 9 цифр)
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template_string(LOGIN_TEMPLATE, error="Нужно ввести email и пароль", app_domain=get_app_domain())

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email, boom_password=password).first()
        if not user:
            # Для теста: если пользователя нет, можно создать его на лету.
            # В боевой версии лучше заводить пользователей отдельно.
            user = User(email=email, boom_password=password)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Успешный логин
        session.permanent = True
        session["user_id"] = user.id
        session["auth_method"] = "password"
        return redirect("/me")
    finally:
        db.close()


@auth_bp.route("/login/telegram/callback", methods=["GET", "POST"])
def login_telegram_callback():
    """
    Callback от Telegram Login Widget.

    В реальности Telegram передаёт данные либо в query string, либо в POST.
    Здесь мы обрабатываем оба варианта.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    data = request.form.to_dict() if request.method == "POST" else request.args.to_dict()
    
    logger.info(f"Telegram callback received: method={request.method}, data={data}")

    if not verify_telegram_auth(data):
        logger.error(f"Invalid Telegram signature for data: {data}")
        return "Неверная подпись Telegram, доступ запрещён", 403

    telegram_id_str = data.get("id")
    if not telegram_id_str:
        logger.error("No telegram id in callback data")
        return "Не передан id пользователя Telegram", 400

    try:
        telegram_id = int(telegram_id_str)
    except ValueError:
        logger.error(f"Invalid telegram id: {telegram_id_str}")
        return f"Некорректный id {telegram_id_str} пользователя Telegram", 400

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            logger.warning(f"User with telegram_id={telegram_id} not found in database")
            # В этом примере, если пользователя нет — отказываем.
            # Можно также создать пользователя и привязать email, если бизнес-логика это допускает.
            return f"Нет доступа: ваш Telegram ID {telegram_id_str} ещё не привязан к аккаунту. Обратитесь к администратору.", 403

        logger.info(f"User {user.id} (telegram_id={telegram_id}) logged in via Telegram")
        session.permanent = True
        session["user_id"] = user.id
        session["auth_method"] = "telegram"
        return redirect("/me")
    finally:
        db.close()


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/login")


@auth_bp.route("/test-telegram-widget")
def test_telegram_widget():
    """Тестовая страница для отладки Telegram Login Widget"""
    TEST_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Test Telegram Login Widget</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .info { background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .result { background: #f0f0f0; padding: 15px; border-radius: 8px; margin-top: 20px; }
        pre { background: white; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>🧪 Тест Telegram Login Widget</h1>
    
    <div class="info">
        <strong>Информация:</strong><br>
        Домен приложения: <code>{{ app_domain }}</code><br>
        Бот: <code>@{{ telegram_bot_username }}</code><br>
        Callback URL: <code>{{ app_domain }}/login/telegram/callback</code>
    </div>
    
    <h2>Виджет авторизации:</h2>
    <script async src="https://telegram.org/js/telegram-widget.js?22"
          data-telegram-login="{{ telegram_bot_username }}"
            data-size="large"
            data-onauth="onTelegramAuth(user)"
            data-request-access="write">
    </script>
    
    <div class="result">
        <strong>Результат авторизации:</strong>
        <pre id="user-data">Ожидание авторизации...</pre>
    </div>
    
    <p><a href="/login">← Вернуться на страницу входа</a></p>
    
    <script type="text/javascript">
        function onTelegramAuth(user) {
            console.log('Telegram auth callback:', user);
            document.getElementById('user-data').innerHTML = JSON.stringify(user, null, 2);
            
            alert('✅ Авторизация успешна!\\n\\nИмя: ' + user.first_name + 
                  '\\nTelegram ID: ' + user.id +
                  '\\n\\nПроверьте консоль браузера для деталей.');
        }
    </script>
</body>
</html>
    """
    return render_template_string(TEST_PAGE, app_domain=get_app_domain())
