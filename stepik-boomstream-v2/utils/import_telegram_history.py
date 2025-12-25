import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from telethon import TelegramClient

from app.db import SessionLocal
from app.models import TelegramTopic, TelegramDiscussionMessage


def get_env_int(name: str):
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


async def main():
    api_id = get_env_int("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()

    if not api_id:
        api_id = int(input("Enter TELEGRAM_API_ID: ").strip())
    if not api_hash:
        api_hash = input("Enter TELEGRAM_API_HASH: ").strip()

    phone = os.getenv("TELEGRAM_PHONE", "").strip()
    if not phone:
        phone = input("Enter phone (international format): ").strip()

    session_path = str(ROOT / "telethon.session")
    client = TelegramClient(session_path, api_id, api_hash)

    await client.start(phone=phone)

    db = SessionLocal()
    try:
        topics = db.query(TelegramTopic).order_by(TelegramTopic.opened_at.asc()).all()
        inserted = 0
        skipped = 0

        for topic in topics:
            chat_id = int(topic.chat_id)
            thread_id = int(topic.message_thread_id)

            async for message in client.iter_messages(chat_id, reply_to=thread_id, reverse=True):
                text = (message.text or "").strip()
                if not text:
                    skipped += 1
                    continue

                if message.sender and getattr(message.sender, "bot", False):
                    skipped += 1
                    continue

                exists = (
                    db.query(TelegramDiscussionMessage)
                    .filter_by(chat_id=chat_id, message_id=message.id)
                    .first()
                )
                if exists:
                    skipped += 1
                    continue

                reaction_count = 0
                if message.reactions and message.reactions.results:
                    reaction_count = sum(r.count for r in message.reactions.results)

                record = TelegramDiscussionMessage(
                    chat_id=chat_id,
                    message_id=message.id,
                    thread_id=thread_id,
                    user_id=message.sender_id or 0,
                    text=text,
                    created_at=message.date,
                    edited_at=message.edit_date,
                    reply_to_message_id=message.reply_to_msg_id,
                    reaction_count=reaction_count,
                )
                db.add(record)
                inserted += 1

            db.commit()
            print(f"[Import] thread {thread_id}: inserted {inserted}, skipped {skipped}")

        print(f"[Import] Done. inserted {inserted}, skipped {skipped}")
    finally:
        db.close()
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
