import json
from flask import Blueprint, render_template, request, jsonify
from .db import SessionLocal
from .models import User

schedule_bp = Blueprint("schedule_bp", __name__, url_prefix="/schedule")


@schedule_bp.get("/<int:user_id>")
def schedule_form(user_id: int):
    session = SessionLocal()
    try:
        user = session.get(User, user_id)
        if not user:
            # На реальном проекте сделай шаблон ошибки
            return f"User {user_id} not found", 404

        schedule = user.schedule_json or {}
        offset_hours = user.timezone_offset_hours or 0

    finally:
        session.close()

    return render_template(
        "schedule.html",
        user_id=user_id,
        schedule_json=json.dumps(schedule),
        offset_hours=offset_hours,
    )


@schedule_bp.post("/<int:user_id>")
def schedule_save(user_id: int):
    data = request.get_json()
    schedule = data.get("schedule")
    offset_hours = data.get("offset_hours")

    if schedule is None:
        return jsonify({"ok": False, "error": "schedule is required"}), 400

    session = SessionLocal()
    try:
        user = session.get(User, user_id)
        if not user:
            return jsonify({"ok": False, "error": "User not found"}), 404

        user.schedule_json = schedule
        if offset_hours is not None:
            user.timezone_offset_hours = int(offset_hours)

        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        session.close()

    return jsonify({"ok": True})
