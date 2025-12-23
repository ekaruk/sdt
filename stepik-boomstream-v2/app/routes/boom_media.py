from flask import Blueprint, redirect, render_template_string, request

import urllib.parse

from ..auth import ensure_session_user
from ..db import SessionLocal
from ..models import User

boom_media_bp = Blueprint("boom_media", __name__, url_prefix="/boom")


@boom_media_bp.route("/miniapp", methods=["GET"])
def miniapp():
    return render_template_string(
        """\
        <!doctype html>
        <html lang="ru">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Открываем видео...</title>
        </head>
        <body>
          <script src="https://telegram.org/js/telegram-web-app.js"></script>
          <script>
            (function() {
              if (!(window.Telegram && Telegram.WebApp)) {
                document.body.textContent = 'Нет данных авторизации Telegram.';
                return;
              }
              const initData = Telegram.WebApp.initData || '';
              const startParam = Telegram.WebApp.initDataUnsafe?.start_param || '';
              let media = '';
              if (startParam.startsWith('boom_')) {
                media = startParam.slice('boom_'.length);
              } else {
                const urlParams = new URLSearchParams(window.location.search);
                media = urlParams.get('media') || '';
              }
              if (!initData || !media) {
                document.body.textContent = 'Нет данных для открытия видео.';
                return;
              }
              const url = `/boom/go?tg_init_data=${encodeURIComponent(initData)}&media=${encodeURIComponent(media)}`;
              window.location.replace(url);
            })();
          </script>
        </body>
        </html>
        """
    )


@boom_media_bp.route("/go", methods=["GET"])
def go_boom():
    init_data = request.args.get("tg_init_data") or request.headers.get("X-Telegram-Init-Data") or ""
    if request.args.get("tg_init_data"):
        init_data = urllib.parse.unquote(init_data)

    if not init_data:
        return render_template_string(
            """\
            <!doctype html>
            <html lang="ru">
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Открываем видео...</title>
            </head>
            <body>
              <script src="https://telegram.org/js/telegram-web-app.js"></script>
              <script>
                (function() {
                  if (window.Telegram && Telegram.WebApp) {
                    const initData = Telegram.WebApp.initData || '';
                    if (initData) {
                      const url = `/boom/go?tg_init_data=${encodeURIComponent(initData)}`;
                      window.location.replace(url);
                      return;
                    }
                  }
                  document.body.textContent = 'Нет данных авторизации Telegram.';
                })();
              </script>
            </body>
            </html>
            """
        )

    media = request.args.get("media")
    if not media:
        return "Не передан код видео.", 400

    auth = ensure_session_user(init_data)
    telegram_id = auth.get("telegram_id")
    if not telegram_id:
        return "Нет доступа.", 403

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return "Нет доступа.", 403
        if not user.boom_password:
            return "Для пользователя не задан пароль Boomstream.", 403

        video_url = f"https://play.boomstream.com/{media}?id_recovery={user.boom_password}"
        print(f"[INFO] Redirecting user_id={user.id} to video_url={video_url}") 
        
        return redirect(video_url)
    finally:
        db.close()
