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

  <p>Способ входа: {{ auth_method }}</p>

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
        auth_method = session.get("auth_method", "unknown")

        return render_template_string(
            DASHBOARD_TEMPLATE,
            user=user,
            grants=grants,
            auth_method=auth_method,
        )
    finally:
        db.close()

TELEGRAM_WEBAPP_TEMPLATE_old = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Boomstream WebApp</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root { color-scheme: dark; }

    body {
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      background: #111;
      color: #fff;
    }

    .container {
      padding: 12px;
      transition: padding 0.2s;
    }

    h1 {
      font-size: 18px;
      margin: 0 0 12px;
    }

    .user-info {
      font-size: 14px;
      margin-bottom: 12px;
      opacity: 0.8;
    }

    /* Рекомендованный Boomstream-подход: адаптивный iframe */
    .bs-player {
      position: relative;
      padding-bottom: 56.25%; /* 16:9 */
      height: 0;
      overflow: hidden;
      max-width: 100%;
      background: #000;
      border-radius: 8px;
      transition: border-radius 0.2s;
    }

    .bs-player iframe {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      border: 0;
    }

    /* Режим "почти фулскрин" в горизонтали */
    .landscape body {
      background: #000;
    }

    .landscape .container {
      padding: 0;
    }

    .landscape h1,
    .landscape .user-info {
      display: none;
    }

    .landscape .bs-player {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      padding-bottom: 0;
      border-radius: 0;
      max-width: 100vw;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Ваше видео</h1>
    <div class="user-info" id="user-info"></div>

    {% if video_code %}
      <div class="bs-player">
        <iframe
          src="https://play.boomstream.com/{{ video_code }}"
          allowfullscreen
          allow="autoplay; encrypted-media"
        ></iframe>
      </div>
    {% else %}
      <p>Видео пока недоступно.</p>
    {% endif %}
  </div>

  <script>
    const tg = window.Telegram.WebApp;
    tg.expand();

    const user = tg.initDataUnsafe?.user;
    const userInfo = document.getElementById('user-info');

    if (user) {
      userInfo.textContent =
        `Telegram: ${user.first_name || ''} ${user.last_name || ''} ` +
        `(@${user.username || ''}, id=${user.id})`;
    } else {
      userInfo.textContent = 'Авторизация Telegram не передана.';
    }

    function applyOrientationLayout() {
      const isLandscape = window.innerWidth > window.innerHeight;
      if (isLandscape) {
        document.documentElement.classList.add('landscape');
      } else {
        document.documentElement.classList.remove('landscape');
      }
    }

    window.addEventListener('resize', applyOrientationLayout);
    window.addEventListener('orientationchange', applyOrientationLayout);
    applyOrientationLayout();
  </script>
</body>
</html>
"""

TELEGRAM_WEBAPP_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Boomstream WebApp</title>
  <style>
      .embed-container {
          position: relative;
          height: 0;
          overflow: hidden;
          max-width: 100%;
      }

      @media (min-width: 0px) {
          .embed-container {
              padding-bottom: 56.25%;
          }
      }

      @media (min-width: 768px) {
          .embed-container {
              padding-bottom: 56.25%;
          }
      }

      .embed-container iframe {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
      }
  </style>
</head>
<body>
      {% if video_code %}
           <div class="embed-container">
           <iframe width="100%" height="355" src="https://play.boomstream.com/{{ video_code }}?id_recovery={{ HASH_TO_IDENTIFY_USER }}" frameborder="0" scrolling="no" allowfullscreen=""></iframe>
           </div>
      {% else %}
          <p>Видео пока недоступно.</p>
      {% endif %}
</body>
</html>
"""

@dashboard_bp.route("/telegram-widget")
def telegram_widget():
    """
    Маршрут, который будет открываться как WebApp из бота.
    Здесь можно:
      - использовать session["user_id"], если уже есть сессия
      - или подбирать Boomstream-видео по Telegram user_id (через initData, если ты его будешь валидировать на сервере).
    Пока для простоты — просто жёстко выдаём один video_code.
    """
    # Пока: один hardcoded код (потом возьмёшь из DB по user_id)
    video_code = "TsQAJHvj"  # TODO: заменить на реальный код Boomstream
    hash="sdt20252" 
    
    return render_template_string(TELEGRAM_WEBAPP_TEMPLATE, 
                                  video_code=video_code,
                                  HASH_TO_IDENTIFY_USER = hash)        
