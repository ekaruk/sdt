from typing import Any, Dict, Optional

import json
import requests

from .config import Config
from .db import SessionLocal
from .models import TelegramMessage


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/{method}"


def _thread_id_from_config() -> Optional[int]:
    if Config.TELEGRAM_THREAD_ID is None:
        return None
    try:
        return int(Config.TELEGRAM_THREAD_ID)
    except (TypeError, ValueError):
        return None


def get_topic_link(chat_id: Any, message_thread_id: int) -> str:
    chat_id_str = str(chat_id)
    if chat_id_str.startswith("-100"):
        return f"https://t.me/c/{chat_id_str[4:]}/{message_thread_id}"
    return ""


def create_forum_topic(
    *,
    chat_id: Any,
    name: str,
    icon_custom_emoji_id: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"chat_id": chat_id, "name": name}
    if icon_custom_emoji_id:
        payload["icon_custom_emoji_id"] = icon_custom_emoji_id
    resp = requests.post(_api_url("createForumTopic"), json=payload)
    data = {}
    try:
        data = resp.json()
    except Exception:
        data = {"ok": False, "error": resp.text}
    return {
        "ok": resp.ok,
        "status_code": resp.status_code,
        "body": data,
        "message_thread_id": data.get("result", {}).get("message_thread_id"),
    }


def send_message(
    *,
    chat_id: Any,
    text: str,
    message_thread_id: Optional[int] = None,
    parse_mode: Optional[str] = None,
    reply_markup: Optional[Dict[str, Any]] = None,
    ref_type: Optional[str] = None,
    ref_id: Optional[int] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"chat_id": chat_id, "text": text}
    if message_thread_id is not None:
        payload["message_thread_id"] = message_thread_id
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    resp = requests.post(_api_url("sendMessage"), json=payload)
    data = {}
    try:
        data = resp.json()
    except Exception:
        data = {"ok": False, "error": resp.text}
    result = {
        "ok": resp.ok,
        "status_code": resp.status_code,
        "body": data,
        "message_id": data.get("result", {}).get("message_id"),
    }
    if resp.ok and result["message_id"] is not None:
        try:
            session = SessionLocal()
            session.add(
                TelegramMessage(
                    chat_id=chat_id,
                    message_thread_id=message_thread_id,
                    message_id=result["message_id"],
                    ref_type=ref_type,
                    ref_id=ref_id,
                    text=text,
                    reply_markup=json.dumps(reply_markup) if reply_markup else None,
                    parse_mode=parse_mode,
                )
            )
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
    return result


def close_forum_topic(
    *,
    chat_id: Any,
    message_thread_id: int,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "message_thread_id": message_thread_id,
    }
    resp = requests.post(_api_url("closeForumTopic"), json=payload)
    data = {}
    try:
        data = resp.json()
    except Exception:
        data = {"ok": False, "error": resp.text}
    return {
        "ok": resp.ok,
        "status_code": resp.status_code,
        "body": data,
    }


def pin_notice_message(notification_message_id: int) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "message_id": notification_message_id,
    }
    thread_id = _thread_id_from_config()
    if thread_id is not None:
        payload["message_thread_id"] = thread_id
    resp = requests.post(_api_url("pinChatMessage"), json=payload)
    data = {}
    try:
        data = resp.json()
    except Exception:
        data = {"ok": False, "error": resp.text}
    return {
        "ok": resp.ok,
        "status_code": resp.status_code,
        "body": data,
    }


def unpin_notice_message(notification_message_id: int) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "message_id": notification_message_id,
    }
    thread_id = _thread_id_from_config()
    if thread_id is not None:
        payload["message_thread_id"] = thread_id
    resp = requests.post(_api_url("unpinChatMessage"), json=payload)
    data = {}
    try:
        data = resp.json()
    except Exception:
        data = {"ok": False, "error": resp.text}
    return {
        "ok": resp.ok,
        "status_code": resp.status_code,
        "body": data,
    }


def edit_notice_reply_markup(
    notification_message_id: int,
    reply_markup: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "message_id": notification_message_id,
        "reply_markup": reply_markup or {"inline_keyboard": []},
    }
    thread_id = _thread_id_from_config()
    if thread_id is not None:
        payload["message_thread_id"] = thread_id
    resp = requests.post(_api_url("editMessageReplyMarkup"), json=payload)
    data = {}
    try:
        data = resp.json()
    except Exception:
        data = {"ok": False, "error": resp.text}
    return {
        "ok": resp.ok,
        "status_code": resp.status_code,
        "body": data,
    }


def edit_message_text(
    message_id: int,
    text: str,
    chat_id: Optional[Any] = None,
    parse_mode: Optional[str] = None,
    message_thread_id: Optional[int] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chat_id": chat_id if chat_id is not None else Config.TELEGRAM_CHAT_ID,
        "message_id": message_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    thread_id = message_thread_id if message_thread_id is not None else _thread_id_from_config()
    if thread_id is not None:
        payload["message_thread_id"] = thread_id
    resp = requests.post(_api_url("editMessageText"), json=payload)
    data = {}
    try:
        data = resp.json()
    except Exception:
        data = {"ok": False, "error": resp.text}
    return {
        "ok": resp.ok,
        "status_code": resp.status_code,
        "body": data,
    }


def edit_message_reply_markup(
    message_id: int,
    reply_markup: Optional[Dict[str, Any]],
    chat_id: Optional[Any] = None,
    message_thread_id: Optional[int] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chat_id": chat_id if chat_id is not None else Config.TELEGRAM_CHAT_ID,
        "message_id": message_id,
        "reply_markup": reply_markup or {"inline_keyboard": []},
    }
    thread_id = message_thread_id if message_thread_id is not None else _thread_id_from_config()
    if thread_id is not None:
        payload["message_thread_id"] = thread_id
    resp = requests.post(_api_url("editMessageReplyMarkup"), json=payload)
    data = {}
    try:
        data = resp.json()
    except Exception:
        data = {"ok": False, "error": resp.text}
    return {
        "ok": resp.ok,
        "status_code": resp.status_code,
        "body": data,
    }


def post_forum_topic_with_message(
    *,
    chat_id: Any,
    topic_name: str,
    message_text: str,
    icon_custom_emoji_id: Optional[str] = None,
    parse_mode: Optional[str] = "HTML",
    reply_markup: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    topic_result = create_forum_topic(
        chat_id=chat_id,
        name=topic_name,
        icon_custom_emoji_id=icon_custom_emoji_id,
    )
    if not topic_result["ok"] or not topic_result["message_thread_id"]:
        return {
            "ok": False,
            "status_code": topic_result.get("status_code"),
            "body": topic_result.get("body"),
        }

    message_thread_id = int(topic_result["message_thread_id"])
    message_result = send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=f"❓<b>{topic_name}</b>❓\n{message_text}",
        parse_mode= "HTML",
        reply_markup=reply_markup,
    )
    if not message_result["ok"]:
        return {
            "ok": False,
            "status_code": message_result.get("status_code"),
            "body": message_result.get("body"),
            "message_thread_id": message_thread_id,
        }

    return {
        "ok": True,
        "status_code": message_result.get("status_code"),
        "body": message_result.get("body"),
        "message_thread_id": message_thread_id,
        "message_id": message_result.get("message_id"),
        "topic_link": get_topic_link(chat_id, message_thread_id),
    }
