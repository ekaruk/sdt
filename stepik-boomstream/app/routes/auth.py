from flask import Blueprint, request, render_template_string, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from ..db import SessionLocal
from ..models import User

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
  <form method="post">
    <label>Email: <input type="email" name="email" required></label><br><br>
    <label>Пароль: <input type="password" name="password" required></label><br><br>
    <button type="submit">Войти</button>
  </form>
  <p>Нет аккаунта? <a href="/register">Зарегистрироваться</a></p>
</body>
</html>
"""

REGISTER_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Регистрация</title>
</head>
<body>
  <h1>Регистрация</h1>
  {% if error %}
    <p style="color: red;">{{ error }}</p>
  {% endif %}
  <form method="post">
    <label>Email: <input type="email" name="email" required></label><br><br>
    <label>Пароль: <input type="password" name="password" required></label><br><br>
    <button type="submit">Создать аккаунт</button>
  </form>
  <p>Уже есть аккаунт? <a href="/login">Войти</a></p>
</body>
</html>
"""


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect("/me")

    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        db = SessionLocal()
        try:
            user = db.query(User).filter_by(email=email).first()
            if not user or not check_password_hash(user.password_hash, password):
                error = "Неверный email или пароль"
            else:
                session["user_id"] = user.id
                return redirect("/me")
        finally:
            db.close()

    return render_template_string(LOGIN_TEMPLATE, error=error)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template_string(REGISTER_TEMPLATE, error=None)

    error = None
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        error = "Нужно ввести email и пароль"
        return render_template_string(REGISTER_TEMPLATE, error=error)

    db = SessionLocal()
    try:
        if db.query(User).filter_by(email=email).first():
            error = "Пользователь с таким email уже существует"
            return render_template_string(REGISTER_TEMPLATE, error=error)

        user = User(
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.add(user)
        db.commit()
    finally:
        db.close()

    return redirect("/login")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/login")
