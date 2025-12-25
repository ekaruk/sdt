import json
import sys
from .db import SessionLocal
from .models import Question, TelegramTopic, TelegramDiscussionMessage


def build_discussion_snapshot(question_id: int) -> dict:
    db = SessionLocal()
    try:
        question = db.query(Question).filter_by(id=question_id).first()
        if not question:
            return {
                "question": {"id": question_id, "text": ""},
                "meta": {"message_count": 0, "closed_at": None},
                "messages": [],
            }

        topic = db.query(TelegramTopic).filter_by(question_id=question_id).first()
        if not topic:
            return {
                "question": {"id": question.id, "text": question.body or ""},
                "meta": {"message_count": 0, "closed_at": None},
                "messages": [],
            }

        rows = (
            db.query(TelegramDiscussionMessage)
            .filter(
                TelegramDiscussionMessage.chat_id == topic.chat_id,
                TelegramDiscussionMessage.thread_id == topic.message_thread_id,
            )
            .order_by(
                TelegramDiscussionMessage.created_at.asc(),
                TelegramDiscussionMessage.message_id.asc(),
            )
            .all()
        )

        messages = []
        id_to_order = {}
        for idx, msg in enumerate(rows, start=1):
            text = (msg.text or "").strip()
            if not text:
                continue
            id_to_order[msg.message_id] = idx
            messages.append({
                "order": idx,
                "text": text,
                "reply_to": None,
                "reaction_count": max(0, msg.reaction_count or 0),
                "_message_id": msg.message_id,
                "_reply_to_id": msg.reply_to_message_id,
            })

        for msg in messages:
            reply_id = msg.pop("_reply_to_id")
            msg_id = msg.pop("_message_id")
            if reply_id and reply_id in id_to_order:
                msg["reply_to"] = id_to_order[reply_id]
            else:
                msg["reply_to"] = None

        closed_at = topic.closed_at.isoformat() if topic.closed_at else None
        snapshot = {
            "question": {
                "id": question.id,
                "text": question.body or "",
            },
            "meta": {
                "message_count": len(messages),
                "closed_at": closed_at,
            },
            "messages": messages,
        }
        return snapshot
    finally:
        db.close()


def _cli():
    if len(sys.argv) < 2:
        print("Usage: python -m app.discussion_snapshot <question_id>")
        return 1
    try:
        question_id = int(sys.argv[1])
    except ValueError:
        print("question_id must be an integer")
        return 1
    snapshot = build_discussion_snapshot(question_id)
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
