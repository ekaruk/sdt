import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Config
from app.telegram_service import post_forum_topic_with_message


TOPIC_NAME = "Видео урок"
MESSAGE_HTML = (
    "<b>Новое видео</b>\n\n"
    "Смотрите запись по кнопке ниже."
)
BOOM_MEDIA_CODE = "HOP3CJoH"
WEBAPP_SHORT_NAME = "boom"


def main() -> int:
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        print("Telegram не настроен: проверь TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID.")
        return 1
    bot_username = (Config.TELEGRAM_BOT_USERNAME or "").lstrip("@")
    if not bot_username:
        print("BOT_USERNAME не задан.")
        return 1

    start_param = f"boom_{BOOM_MEDIA_CODE}"
    webapp_url = f"https://t.me/{bot_username}/{WEBAPP_SHORT_NAME}?startapp={start_param}"
    reply_markup = {
        "inline_keyboard": [
            [{"text": "📺 Смотреть видео", "url": webapp_url}],
        ]
    }

    post_result = post_forum_topic_with_message(
        chat_id=Config.TELEGRAM_CHAT_ID,
        topic_name=TOPIC_NAME,
        message_text=MESSAGE_HTML,
        parse_mode="HTML",
        reply_markup=reply_markup,
    )

    if not post_result.get("ok"):
        print(f"Ошибка публикации: {post_result.get('body')}")
        return 2

    print("OK")
    print(f"thread_id={post_result.get('message_thread_id')}")
    print(f"topic_link={post_result.get('topic_link')}")
    print(f"message_id={post_result.get('message_id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
