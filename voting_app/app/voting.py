import json
from flask import Blueprint, render_template, request, jsonify
from .db import SessionLocal
from .models import User

voting_bp = Blueprint("voting_bp", __name__)


# Страница голосования (WebApp)
# Один и тот же URL для всех — /voting
@voting_bp.get("/voting")
def voting_page():
    # Шаблон сам получит telegram_id через Telegram.WebApp.initDataUnsafe в JS
    return render_template("voting.html")


# API: получить текущие данные пользователя по telegram_id
@voting_bp.get("/api/voting/<int:telegram_id>")
def voting_get(telegram_id: int):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            schedule = user.schedule_json or {}
            offset_hours = user.timezone_offset_hours or 0
        else:
            schedule = {}
            offset_hours = 0
    finally:
        session.close()

    return jsonify({
        "telegram_id": telegram_id,
        "schedule": schedule,
        "offset_hours": offset_hours,
    })


# API: сохранить расписание по telegram_id
# Если пользователя нет — создаём
@voting_bp.post("/api/voting/<int:telegram_id>")
def voting_save(telegram_id: int):
    data = request.get_json(force=True)
    schedule = data.get("schedule")
    offset_hours = data.get("offset_hours", 0)

    if schedule is None:
        return jsonify({"ok": False, "error": "schedule is required"}), 400

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            user = User(
                telegram_id=telegram_id,
                schedule_json=schedule,
                timezone_offset_hours=int(offset_hours),
            )
            session.add(user)
        else:
            user.schedule_json = schedule
            user.timezone_offset_hours = int(offset_hours)

        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        session.close()

    return jsonify({"ok": True})
