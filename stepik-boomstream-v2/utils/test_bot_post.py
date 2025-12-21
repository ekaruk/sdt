import os
import requests

TELEGRAM_BOT_TOKEN = '8570792426:AAHlF4WaDjh-0NyqBsmngFCVM9QQazkVudY'
TELEGRAM_CHAT_ID = -1003542588723

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Проверьте, что в .env заданы TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID")
    exit(1)

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": "Тестовое сообщение от бота"
}

response = requests.post(url, json=payload)

print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")
    
# 1. Создание темы (forum topic)
create_topic_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/createForumTopic"
topic_payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "name": "Тестовая тема от скрипта"
}

resp = requests.post(create_topic_url, json=topic_payload)
print(f"Create topic status: {resp.status_code}")
print(f"Create topic response: {resp.text}")

data = resp.json()
if not data.get("ok"):
    print("Не удалось создать тему!")
    exit(1)

thread_id = data["result"]["message_thread_id"]

# 2. Отправка сообщения в созданную тему
send_message_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
message_payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "message_thread_id": thread_id,
    "text": "Тестовое сообщение в новую тему"
}

resp2 = requests.post(send_message_url, json=message_payload)
print(f"Send message status: {resp2.status_code}")
print(f"Send message response: {resp2.text}")
