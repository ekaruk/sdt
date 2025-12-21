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
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
      background: #f5f5f5;
    }
    .header {
      background: white;
      padding: 20px;
      border-radius: 10px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1 {
      margin: 0 0 10px 0;
      color: #333;
    }
    .user-info {
      color: #666;
      font-size: 14px;
    }
    .menu {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 20px;
    }
    .menu-item {
      background: white;
      padding: 20px;
      border-radius: 10px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      text-decoration: none;
      color: inherit;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .menu-item:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .menu-item h3 {
      margin: 0 0 8px 0;
      color: #667eea;
      font-size: 18px;
    }
    .menu-item p {
      margin: 0;
      color: #666;
      font-size: 14px;
    }
    .menu-item.admin {
      border-left: 4px solid #f59e0b;
    }
    .menu-item.curator {
      border-left: 4px solid #10b981;
    }
    .content {
      background: white;
      padding: 20px;
      border-radius: 10px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .logout-form {
      text-align: center;
    }
    .logout-btn {
      background: #ef4444;
      color: white;
      border: none;
      padding: 10px 30px;
      border-radius: 5px;
      cursor: pointer;
      font-size: 14px;
      transition: background 0.2s;
    }
    .logout-btn:hover {
      background: #dc2626;
    }
    .role-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
      margin-left: 10px;
    }
    .role-admin {
      background: #fef3c7;
      color: #92400e;
    }
    .role-curator {
      background: #d1fae5;
      color: #065f46;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>
      Здравствуйте, {{ user.first_name or '' }} {{ user.last_name or '' }}!
      {% if user.role == 2 %}
        <span class="role-badge role-admin">Администратор</span>
      {% elif user.role == 1 %}
        <span class="role-badge role-curator">Куратор</span>
      {% endif %}
    </h1>
    <div class="user-info">
      Способ входа: {{ auth_method }}
      {% if user.telegram_id %}
        | Telegram ID: {{ user.telegram_id }}
      {% endif %}
    </div>
  </div>

  <div class="menu">
    <a href="/questions" class="menu-item">
      <h3>📝 Вопросы</h3>
      <p>Просмотр и голосование за вопросы</p>
    </a>
    
    <a href="/questions/miniapp" class="menu-item">
      <h3>📱 Mini App</h3>
      <p>Telegram Mini App версия</p>
    </a>
    
    {% if user.role == 2 %}
    <a href="/admin/users" class="menu-item admin">
      <h3>👥 Пользователи</h3>
      <p>Управление пользователями и ролями</p>
    </a>
    {% endif %}
  </div>

  <div class="logout-form">
    <form method="post" action="/logout">
      <button type="submit" class="logout-btn">Выйти</button>
    </form>
  </div>
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

        print('DEBUG user.role:', type(user.role), user.role)
        print('DEBUG session user_id:', user_id, 'DB user.id:', user.id)
        return render_template_string(
          DASHBOARD_TEMPLATE + """
          <div style='color:red'>DEBUG: user.role={{ user.role }} (type: {{ user.role.__class__.__name__ }})<br>
          session user_id={{ session_user_id }} | db user.id={{ user.id }}</div>
          """,
          user=user,
          grants=grants,
          auth_method=auth_method,
          session_user_id=user_id
        )
    finally:
        db.close()

TELEGRAM_WEBAPP_TEMPLATE = """
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
          src="https://play.boomstream.com/{{ video_code }}?id_recovery={{ HASH_TO_IDENTIFY_USER }}"
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

TELEGRAM_WEBAPP_TEMPLATE_new = """
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
    
    

    TELEGRAM_WEBAPP = render_template_string(TELEGRAM_WEBAPP_TEMPLATE, 
                                  video_code=video_code,
                                  HASH_TO_IDENTIFY_USER = hash)        
    return TELEGRAM_WEBAPP