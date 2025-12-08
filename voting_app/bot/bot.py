import os
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")  # токен бота от BotFather
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://vapid-agnus-unconversational.ngrok-free.dev/voting")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # опционально, если хочешь слать посты в канал
BOT_USERNAME = os.getenv("BOT_USERNAME")  # нужно, чтобы формировать ссылку t.me/...

# /start и /start voting
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args

    if args and args[0] == "voting":
        # пользователь пришёл по ссылке вида t.me/Bot?start=voting
        await send_voting_webapp_button(update, context)
    else:
        await update.message.reply_text(
            "Привет! Чтобы пройти голосование, нажми кнопку ниже."
        )
        await send_voting_webapp_button(update, context)


async def send_voting_webapp_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🕒 Пройти голосование",
            web_app=WebAppInfo(url=WEBAPP_URL),
        )
    ]])

    await context.bot.send_message(
        chat_id=chat_id,
        text="Открой форму голосования и отметь удобные часы:",
        reply_markup=keyboard,
    )


# Дополнительно: команда для отправки приглашения в канал (по желанию)
async def send_invite_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет в канал сообщение с кнопкой, ведущей в личку бота."""
    if not CHANNEL_ID or not BOT_USERNAME:
        await update.message.reply_text("CHANNEL_ID или BOT_USERNAME не заданы.")
        return

    invite_url = f"https://t.me/{BOT_USERNAME}?start=voting"

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="Пройти голосование",
            web_app=WebAppInfo(url=invite_url),
        )
    ]])

    await context.bot.send_message(
        chat_id=int(CHANNEL_ID),
        text="Друзья, пройдите, пожалуйста, голосование по времени:",
        reply_markup=keyboard,
    )


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send_invite", send_invite_to_channel))

    app.run_polling()


if __name__ == "__main__":
    main()
