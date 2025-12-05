from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8570792426:AAHlF4WaDjh-0NyqBsmngFCVM9QQazkVudY"
WEBAPP_URL = "https://sdt2025-web.onrender.com/telegram-widget"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                text="Открыть лекции",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]]
    )

    await update.message.reply_text(
        "Нажмите кнопку для входа:",
        reply_markup=keyboard
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
