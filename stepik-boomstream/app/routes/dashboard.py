from flask import Blueprint, session, redirect, render_template_string
from ..db import SessionLocal
from ..models import User, VideoGrant

dashboard_bp = Blueprint("dashboard", __name__)

DASHBOARD_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Личный кабинет</title>
</head>
<body>
  <h1>Привет, {{ user.email }}!</h1>

  <h2>Ваши доступные видео:</h2>
  {% if grants %}
    <ul>
      {% for grant in grants %}
        <li>
          {{ grant.boomstream_resource_id }}
          (урок {{ grant.stepik_lesson_id }}, выдано {{ grant.created_at }})
        </li>
      {% endfor %}
    </ul>
  {% else %}
    <p>Пока нет доступных видео.</p>
  {% endif %}

  <form method="post" action="/logout">
    <button type="submit">Выйти</button>
  </form>
</body>
</html>
"""


@dashboard_bp.route("/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            session.clear()
            return redirect("/login")

        grants = db.query(VideoGrant).filter_by(user_id=user.id).all()

        return render_template_string(
            DASHBOARD_TEMPLATE,
            user=user,
            grants=grants,
        )
    finally:
        db.close()
