from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from datetime import datetime
from typing import Any

import sys
from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Config
from menu_tree import SECTIONS  # тут твоё дерево с "root", "sec_...", "lesson_..."

#python -m bots.bot_dev

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.auth import get_user_by_telegram_id

DEFAULT_VIEW_MODE = "mobile"
# prod BOT_TOKEN = "8570792426:AAHlF4WaDjh-0NyqBsmngFCVM9QQazkVudY"

# dev 
BOT_TOKEN = Config.TELEGRAM_BOT_VIDEO_TOKEN


#WEBAPP_URL2 = "https://play.boomstream.com/TsQAJHvj?id_recovery=sdt20252"
WEBAPP_URL_STEPIK="https://stepik.org/lesson/"
WEBAPP_URL_TEMPLATE = "https://play.boomstream.com/{boom_media}?id_recovery={boom_password}"
WEBAPP_URL_TEMPLATE_WITHOUT_PASS = "https://play.boomstream.com/{boom_media}"

def get_view_mode(context):
    return context.user_data.get("view_mode", DEFAULT_VIEW_MODE)

def toggle_view_mode(context):
    current = get_view_mode(context)
    new_mode = "web" if current == "mobile" else "mobile"
    context.user_data["view_mode"] = new_mode
    return new_mode

def adapt_title(title: str, context):

    padding = "\u2800" * 30 if get_view_mode(context) == "mobile" else "\u2800" * 2
    new_title = f"\u2800\u2800{title}{padding}"
    
    return new_title

def build_video_url(current_node: Any, context) -> str:
    boom_media = current_node.get("boom_media", "")
    
    boom_password = context.user_data.get("boom_password", "")
    
    list_media_no_pass = ["RPBloIDb", "nkLQR8Fv0", "MbFb5tN1", "ShjjOBN0", "7VdpkZ48", "1RUjKEKI", "NNh807eh", "jlJpTeI9", "5o7twHCd", "Bb1aCbln"]

    if boom_media in list_media_no_pass:
        webapp_url = WEBAPP_URL_TEMPLATE_WITHOUT_PASS.format(boom_media=boom_media)
    else:
        webapp_url = WEBAPP_URL_TEMPLATE.format(boom_media=boom_media, 
                                                boom_password=boom_password)
    return webapp_url



def get_bottom_row(node: any, context) -> list[InlineKeyboardButton]:
    
    bottom_row: list[InlineKeyboardButton] = []
    parent_id = node.get("parent")
    
    if parent_id is not None:
        bottom_row.append(
            InlineKeyboardButton(
                text="⬅ Назад",
                callback_data=f"menu:{parent_id}",
            )
        )

    bottom_row.append(
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=f"refresh:root",   # важно передать текущий узел
        )
    )

    if parent_id is None:
        view_mode = get_view_mode(context)
        mode_label = "💻 Web" if view_mode == "web" else "📱 Mobile"
        bottom_row.append(
            InlineKeyboardButton(mode_label, callback_data="toggle:mode")
        )

    return bottom_row

def build_menu_keyboard(node_id: str, context) -> InlineKeyboardMarkup:
    
    """
    Строим клавиатуру для любого узла дерева SECTIONS.
    - Если у узла есть children -> рисуем пункты меню (подразделы/уроки).
    - Добавляем кнопку "Назад", если есть parent.
    """
    node = SECTIONS[node_id]
    keyboard: list[list[InlineKeyboardButton]] = []

    # Кнопки для детей (подменю / уроки)
    for child_id in node.get("children", []):
        child = SECTIONS[child_id]
#        if "lesson_id" in child:
#            url = WEBAPP_URL2
#            keyboard_button = InlineKeyboardButton(
#                text=child["title"],
#                web_app=WebAppInfo(url=url),  # в callback передаем id узла
#            )        
#        else:
        keyboard_button = InlineKeyboardButton(
                text=adapt_title(child['title'], context),
                callback_data=f"menu:{child_id}",  # в callback передаем id узла
            )
        
        keyboard.append([keyboard_button])


    bottom_row = get_bottom_row(node, context)
    keyboard.append(bottom_row)

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    tg_user = update.effective_user
    tg_id = tg_user.id

    # 1. Проверяем, есть ли такой пользователь в таблице users
    user = get_user_by_telegram_id(tg_id)  
    error_text = None
    if not user:
        # НЕТ пользователя с таким telegram_id → считаем неавторизованным
        error_text = f"У вас нет доступа к боту. \n Telegram ID: {tg_user.id}"
    elif not user.video_access or user.video_access < 1:
        error_text = f"Здравствуйте {tg_user.full_name}!\n" \
                      "Извините, у Вас пока нет доступа к видео.\n" \
                      "Если вы считаете, что это ошибка, пожалуйста, свяжитесь с администратором.\n"\
                      f"И сообщите ваш Telegram ID: {tg_user.id}" 
    else:
        context.user_data["user_id"] = user.id  # сохраняем ID пользователя в контекст                   
        context.user_data["boom_password"] = user.boom_password  # сохраняем boom_password пользователя в контекст                   
    
    if error_text:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "✉️ Написать администратору",
                url=f"https://t.me/ekaruk",
                )
            ]])
        if update.message:
            await update.message.reply_text(error_text,reply_markup=keyboard)
        else:
            await update.callback_query.edit_message_text(error_text,reply_markup=keyboard)
        return
    
    """Команда /start — показываем корень дерева"""
    await update.message.reply_text(
        SECTIONS["root"]["title"],
        reply_markup=build_menu_keyboard("root", context),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Универсальный хендлер для всех уровней меню"""
    query = update.callback_query
    data = query.data              # ожидаем "menu:<node_id>"
    await query.answer()

    
    # 1) Обновить текущий узел
    if data.startswith("refresh:"):

        text = SECTIONS["root"]["title"] + f"\n\n(обновлено {datetime.now().strftime('%H:%M:%S')})"
     
        await query.edit_message_text(
                text=text,
                reply_markup=build_menu_keyboard("root", context),
            )
        return
    # 2) Переход по меню: menu:<node_id>
    if data.startswith("menu:"):
        # вытаскиваем id узла
        _, node_id = data.split(":", maxsplit=1)
        node = SECTIONS[node_id]

        # если у узла НЕТ детей и есть lesson_id — это "лист" (конечный урок)
        if not node.get("children") and "lesson_id" in node:
            lesson_id = node["lesson_id"]

            title = node["title"]
            title_parent = SECTIONS[node["parent"]]["title"]
            keyboard: list[list[InlineKeyboardButton]] = []
 
            # здесь делаешь то, что нужно с уроком:
            # можно отправить ссылку, WebApp, текст и т.п.
            # я для примера просто отправлю текст с ID урока и общей ссылкой
            webapp_url = build_video_url(node, context)
            webapp_button = InlineKeyboardButton(
                text=adapt_title("📺 Просмотреть видеоурок", context),
                web_app=WebAppInfo(url=webapp_url)
                )
            keyboard.append([webapp_button])
            
            webapp_stepik_button = InlineKeyboardButton(
                text=adapt_title("📚 Выполнить тест к уроку на Stepik", context),
                web_app=WebAppInfo(url=WEBAPP_URL_STEPIK + str(lesson_id))
                )
            keyboard.append([webapp_stepik_button])

            bottom_row = get_bottom_row(node, context)
            keyboard.append(bottom_row)

            await query.edit_message_text(
                f"📙 {title_parent}\n📘{title}\n\nНажмите кнопку ниже, чтобы открыть урок:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    
    if data == "toggle:mode":
        new_mode = toggle_view_mode(context)

        # После переключения — возвращаем пользователя в текущее меню
        # но лучше в корень, так более логично
        text = SECTIONS["root"]["title"] + f"\n\nРежим интерфейса переключен на: {new_mode}\nДля возвращения к прошлому режиму отображения нажмите кнопку еще раз."
        await query.edit_message_text(
            text=text,
            reply_markup=build_menu_keyboard("root", context),
        )
        return
    # если у узла есть children — это раздел/подраздел, рисуем подменю
    text = node["title"]
    await query.edit_message_text(
        text=text,
        reply_markup=build_menu_keyboard(node_id, context),
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    # ловим только callback_data, начинающиеся с "menu:"
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^(menu|refresh|toggle):"))
    app.run_polling()


if __name__ == "__main__":
    main()
