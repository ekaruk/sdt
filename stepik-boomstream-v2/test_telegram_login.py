import os

BOT_USERNAME = os.getenv("BOT_USERNAME", "sdt_dev_bot")
"""
Тестовая страница для проверки Telegram Login Widget
"""
from flask import Flask, request, render_template_string
from app.config import Config

app = Flask(__name__)

TEST_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Test Telegram Login</title>
</head>
<body>
    <h1>Test Telegram Login Widget</h1>
    
    <p>Domain: {{ domain }}</p>
    <p>Bot: @{BOT_USERNAME}</p>
    
    <h2>Telegram Widget:</h2>
        <script async src="https://telegram.org/js/telegram-widget.js?22"
            data-telegram-login="{BOT_USERNAME}"
            data-size="large"
            data-onauth="onTelegramAuth(user)"
            data-request-access="write">
        </script>
    
    <div id="result" style="margin-top: 20px; padding: 10px; background: #f0f0f0;">
        <strong>Результат:</strong>
        <pre id="user-data">Ожидание авторизации...</pre>
    </div>
    
    <script type="text/javascript">
        function onTelegramAuth(user) {
            document.getElementById('user-data').innerHTML = JSON.stringify(user, null, 2);
            
            // Отправляем данные на сервер
            fetch('/test-callback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(user)
            }).then(response => response.text())
              .then(data => {
                  console.log('Server response:', data);
                  alert('Logged in as: ' + user.first_name + ' (ID: ' + user.id + ')');
              });
        }
    </script>
</body>
</html>
"""

@app.route('/test-telegram-login')
def test_login():
    domain = Config.APP_DOMAIN or request.host_url.rstrip('/')
    return render_template_string(TEST_PAGE, domain=domain)

@app.route('/test-callback', methods=['POST'])
def test_callback():
    data = request.json
    print(f"\n✅ Telegram callback received!")
    print(f"User ID: {data.get('id')}")
    print(f"Name: {data.get('first_name')} {data.get('last_name')}")
    print(f"Username: @{data.get('username')}")
    print(f"Data: {data}\n")
    return f"OK: User {data.get('id')} authenticated"

if __name__ == '__main__':
    print("\n🔧 Test server starting...")
    print("📍 Open: http://localhost:5001/test-telegram-login")
    print(f"⚠️  Make sure @{BOT_USERNAME} domain is set to your ngrok URL\n")
    app.run(port=5001, debug=True)
