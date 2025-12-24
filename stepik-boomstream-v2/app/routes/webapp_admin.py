# app/webapp_admin.py
import json

from flask import Blueprint, render_template, render_template_string, request, redirect, url_for
from ..db import SessionLocal
from ..models import User, TelegramUser
from ..auth import admin_required
from ..telegram_service import edit_message_text, edit_message_reply_markup

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@admin_required
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
@admin_required
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


TELEGRAM_EDIT_TEMPLATE = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Редактирование сообщения Telegram</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
    .card { background: white; padding: 20px; border-radius: 10px; max-width: 720px; margin: 0 auto; }
    label { display: block; margin: 12px 0 6px; font-weight: 600; }
    input, textarea { width: 100%; padding: 8px 10px; border: 1px solid #ccc; border-radius: 6px; }
    textarea { min-height: 120px; font-family: monospace; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .actions { margin-top: 16px; display: flex; gap: 10px; flex-wrap: wrap; }
    .btn { background: #1976d2; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; }
    .msg { margin-top: 12px; padding: 10px; border-radius: 6px; background: #eef7ee; }
    .err { background: #ffecec; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Редактирование сообщения Telegram</h2>
    {% if message %}
      <div class="msg {{ 'err' if not success else '' }}">{{ message }}</div>
    {% endif %}
    <form method="post">
    <div class="row">
        <div>
          <label>Ссылка на сообщение (t.me/...)</label>
          <input name="link" value="{{ link or '' }}" placeholder="https://t.me/c/3320447395/159/160">
        </div>
      </div>
      <div class="row">
        <div>
          <label>message_id</label>
          <input name="message_id" value="{{ message_id or '' }}">
        </div>
        <div>
          <label>thread_id</label>
          <input name="thread_id" value="{{ thread_id or '' }}" placeholder="например 42">
        </div>
      </div>
      <label>Новый текст (HTML)</label>
      <textarea name="text" required>{{ text or '' }}</textarea>
      <label>Клавиатура (JSON inline_keyboard)</label>
      <textarea name="keyboard">{{ keyboard or '' }}</textarea>
      <div class="actions">
        <button class="btn" type="submit" name="action" value="both">Обновить</button>
        <button class="btn" type="submit" name="action" value="text">Обновить только текст</button>
        <button class="btn" type="submit" name="action" value="keyboard">Обновить только клавиатуру</button>
      </div>
    </form>
  </div>
</body>
</html>
"""


@admin_bp.route("/telegram/edit", methods=["GET", "POST"])
@admin_required
def edit_telegram_message():
    message = None
    success = True
    link = request.form.get("link") if request.method == "POST" else ""
    message_id = request.form.get("message_id") if request.method == "POST" else ""
    thread_id = request.form.get("thread_id") if request.method == "POST" else ""
    text = request.form.get("text") if request.method == "POST" else ""
    keyboard = request.form.get("keyboard") if request.method == "POST" else ""
    action = request.form.get("action") if request.method == "POST" else "both"

    if request.method == "POST":
        if link and (not message_id or not thread_id):
            try:
                path = link.split("t.me/")[-1]
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 3 and parts[0] == "c":
                    if len(parts) >= 4:
                        thread_id = thread_id or parts[2]
                        message_id = message_id or parts[3]
                    else:
                        message_id = message_id or parts[2]
                else:
                    return render_template_string(
                        TELEGRAM_EDIT_TEMPLATE,
                        message="Ссылка не распознана. Пример: https://t.me/c/3320447395/159/160",
                        success=False,
                        link=link,
                        message_id=message_id,
                        thread_id=thread_id,
                        text=text,
                        keyboard=keyboard,
                    )
            except Exception:
                return render_template_string(
                    TELEGRAM_EDIT_TEMPLATE,
                    message="Не удалось разобрать ссылку.",
                    success=False,
                    link=link,
                    message_id=message_id,
                    thread_id=thread_id,
                    text=text,
                    keyboard=keyboard,
                )

        try:
            message_id_int = int(message_id)
        except (TypeError, ValueError):
            return render_template_string(
                TELEGRAM_EDIT_TEMPLATE,
                message="Некорректный message_id.",
                success=False,
                link=link,
                message_id=message_id,
                thread_id=thread_id,
                text=text,
                keyboard=keyboard,
            )

        thread_id_int = None
        if thread_id:
            try:
                thread_id_int = int(thread_id)
            except (TypeError, ValueError):
                return render_template_string(
                    TELEGRAM_EDIT_TEMPLATE,
                    message="Некорректный thread_id.",
                    success=False,
                    link=link,
                    message_id=message_id,
                    thread_id=thread_id,
                    text=text,
                    keyboard=keyboard,
                )

        reply_markup = None
        if keyboard:
            try:
                reply_markup = json.loads(keyboard)
            except json.JSONDecodeError:
                return render_template_string(
                    TELEGRAM_EDIT_TEMPLATE,
                    message="Некорректный JSON для клавиатуры.",
                    success=False,
                    link=link,
                    message_id=message_id,
                    thread_id=thread_id,
                    text=text,
                    keyboard=keyboard,
                )

        if action in ("both", "text"):
            text_result = edit_message_text(
                message_id=message_id_int,
                text=text,
                parse_mode="HTML",
                message_thread_id=thread_id_int,
            )
            if not text_result.get("ok"):
                return render_template_string(
                    TELEGRAM_EDIT_TEMPLATE,
                    message=f"Ошибка обновления текста: {text_result.get('body')}",
                    success=False,
                    link=link,
                    message_id=message_id,
                    thread_id=thread_id,
                    text=text,
                    keyboard=keyboard,
                )

        if action in ("both", "keyboard"):
            markup_result = edit_message_reply_markup(
                message_id=message_id_int,
                reply_markup=reply_markup,
                message_thread_id=thread_id_int,
            )
            if not markup_result.get("ok"):
                return render_template_string(
                    TELEGRAM_EDIT_TEMPLATE,
                    message=f"Ошибка обновления клавиатуры: {markup_result.get('body')}",
                    success=False,
                    link=link,
                    message_id=message_id,
                    thread_id=thread_id,
                    text=text,
                    keyboard=keyboard,
                )

        if action == "text":
            message = "Текст обновлен."
        elif action == "keyboard":
            message = "Клавиатура обновлена."
        else:
            message = "Сообщение обновлено."

    return render_template_string(
        TELEGRAM_EDIT_TEMPLATE,
        message=message,
        success=success,
        link=link,
        message_id=message_id,
        thread_id=thread_id,
        text=text,
        keyboard=keyboard,
    )

