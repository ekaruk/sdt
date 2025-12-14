# app/webapp_admin.py
from flask import Blueprint, render_template, request, redirect, url_for
from ..db import SessionLocal
from ..models import User, TelegramUser

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")


@admin_bp.route("/users")
def users_table():
    """Страница с таблицей users + telegram_users."""
    view = request.args.get("view", "combined")  # combined | users | telegram

    session = SessionLocal()
    try:
        # LEFT JOIN users <- telegram_users по telegram_id
        rows = (
            session.query(User, TelegramUser)
            .outerjoin(TelegramUser, User.telegram_id == TelegramUser.id)
            .order_by(User.id)
            .all()
        )
    finally:
        session.close()

    return render_template(
        "admin_users.html",
        rows=rows,
        view=view,
    )


@admin_bp.post("/users/<int:user_id>/video_access")
def set_video_access(user_id: int):
    """Обработчик кнопок 'дать/запретить доступ'."""
    action = request.form.get("action")  # allow | deny

    value = 1 if action == "allow" else 0

    session = SessionLocal()
    try:
        user = session.query(User).get(user_id)
        if user is None:
            return redirect(url_for("admin_bp.users_table"))

        user.video_access = value
        session.commit()
    finally:
        session.close()

    return redirect(url_for("admin_bp.users_table", view=request.args.get("view", "combined")))
