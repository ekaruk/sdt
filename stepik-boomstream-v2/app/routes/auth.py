from flask import Blueprint, request, render_template_string, redirect, session
from ..db import SessionLocal
from ..models import User
from ..telegram_auth import verify_telegram_auth

auth_bp = Blueprint("auth", __name__)

LOGIN_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Вход</title>
</head>
<body>
  <h1>Вход</h1>
  {% if error %}
    <p style="color: red;">{{ error }}</p>
  {% endif %}

  <h2>Вход по email + пароль (Boomstream-пароль)</h2>
  <form method="post" action="/login">
    <label>Email: <input type="email" name="email" required></label><br><br>
    <label>Пароль (9 цифр): <input type="password" name="password" required></label><br><br>
    <button type="submit">Войти</button>
  </form>

  <h2>Вход через Telegram</h2>
  <p>Ниже можно подключить Telegram Login Widget. Для теста используется простой callback.</p>
  
  <script async src="https://telegram.org/js/telegram-widget.js?22"
          data-telegram-login="sdt2025_bot"
          data-size="large"
          data-userpic="false"
          data-request-access="write"
          data-auth-url="https://vapid-agnus-unconversational.ngrok-free.dev/login/telegram/callback">
  </script>
  

</body>
</html>
"""


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        # Если уже авторизован — сразу в кабинет
        if session.get("user_id"):
            return redirect("/me")
        return render_template_string(LOGIN_TEMPLATE, error=None)

    # POST: вход по email + пароль (Boomstream-пароль, 9 цифр)
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template_string(LOGIN_TEMPLATE, error="Нужно ввести email и пароль")

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
    data = request.form.to_dict() if request.method == "POST" else request.args.to_dict()

    if not verify_telegram_auth(data):
        return "Неверная подпись Telegram, доступ запрещён", 403

    telegram_id_str = data.get("id")
    if not telegram_id_str:
        return "Не передан id пользователя Telegram", 400

    try:
        telegram_id = int(telegram_id_str)
    except ValueError:
        return f"Некорректный id {telegram_id_str} пользователя Telegram", 400

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            # В этом примере, если пользователя нет — отказываем.
            # Можно также создать пользователя и привязать email, если бизнес-логика это допускает.
            return f"Нет доступа: ваш Telegram {telegram_id_str} ещё не привязан к аккаунту", 403

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
