


from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    ReplyKeyboardMarkup, 
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler, 
    filters,
)

#TOKEN = "YOUR_BOT_TOKEN_HERE"
BOT_TOKEN = "8570792426:AAHlF4WaDjh-0NyqBsmngFCVM9QQazkVudY"
#WEBAPP_URL = "https://sdt2025-web.onrender.com/telegram-widget"
#WEBAPP_URL = "https://vapid-agnus-unconversational.ngrok-free.dev/telegram-widget"
WEBAPP_URL2 = "https://play.boomstream.com/TsQAJHvj?id_recovery=sdt20252"


# ----- ДАННЫЕ -----
SECTIONS = {
    "561993": {
        "title": "Раздел 1. Основные энергии",
        "subs": [
            "Урок 1. Основные желания человека",
            "Урок 2. Психическое тело",
            "Урок 3. Основные энергии",
            "Урок 4. Хронические состояния нехватки энергии",
            "Урок 5. Виды перенапряжения",
            "Урок 6. Иллюзии",
            "Урок 7. О красоте, влиянии, бесплодии",
            "Урок 8. Психическое напряжение. Как и где оно скапливается?",
            "Урок 9. Взаимодействие физического и психического тела",
            "Урок 10. Психические каналы: Шротосы и Нади",
        ],
    },
    "579296": {
        "title": "Раздел 2. Блоки",
        "subs": [
            "Урок 11. Психические слои. Их структура.",
            "Урок 12. Психические слои. Их функции в психическом теле.",
            "Урок 13. Блоки. Как они возникают и как влияют на человека.",
            "Урок 14. Прана. Её движение в организме.",
            "Урок 15. Блоки на глубоких слоях",
            "Урок 16. Блоки и их комбинации на разных слоях",
            "Урок 17. Влияние нехватки энергии на физическое тело.",
            "Урок 18. Формирование болезней и блоков",
            "Урок 19. Виды и правила очищения организма",
            "Урок 20. Проблемы при нарушении правил очищения организма.",
        ],
    },
    "564649": {
        "title": "Раздел 3. Оценка здоровья",
        "subs": [
            "Урок 21. Оценка состояния организма",
            "Урок 22. Категории здоровья человека",
            "Урок 23. Первая категория здоровья",
            "Урок 24. Вторая категория здоровья",
            "Урок 25.1 Третья группа здоровья",
            "Урок 25.2 Четвёртая категория здоровья",
        ],
    },
    "579297": {
        "title": "Раздел 4. Вода",
        "subs": [
            "Урок 26. Наполнение энергией воды",
            "Урок 27. Безопасное наполнение энергией воды (часть 1)",
            "Урок 27. Безопасное наполнение энергией воды (часть 2)",
            "Урок 28. Статика",
            "Урок 29. Статика",
            "Урок 30. Деревья",
        ],
    },
    "611382": {
        "title": "Раздел 5. Воздух",
        "subs": [
            "Урок 31. Динамика",
            "Урок 32. Динамика",
            "Урок 33 Динамика",
            "Урок 34. Пассивное очищение Воздухом. Пост.",
        ],
    },
    "611383": {
        "title": "Раздел 6. Солнце",
        "subs": [
            "Урок 35. Посты",
            "Урок 35. Посты (часть 2)",
            "Урок 36. Наполнение Солнцем на открытом солнце",
            "Урок 37. Практика Бани/Сауны/Хамам",
            "Урок 37. Практика Бани/Сауны/Хамам (часть2)",
            "Урок 38. Влияние климата",
            "Урок 39. Внутренние особенности человека",
        ],
    },
}

WIDE_PREFIX_1 = "\u2800" * 2
WIDE_PREFIX_2 = "\u2800" * 40

refresh_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("🔄 Обновить")]
    ],
    resize_keyboard=True,     # растягивает на ширину экрана
    one_time_keyboard=False   # кнопка всегда видна
)

# ----- КЛАВИАТУРЫ -----
def build_sections_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура 1-го уровня: выбор раздела"""
    keyboard = []

    for sec_id, data in SECTIONS.items():
#        title = "\u2003" + data["title"] 
        title = f"{WIDE_PREFIX_1}{data['title']}{WIDE_PREFIX_2}"
        keyboard.append([
            InlineKeyboardButton(
                text=title,
                callback_data=f"sec:{sec_id}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_subsections_keyboard(section_id: str) -> InlineKeyboardMarkup:
    """Клавиатура 2-го уровня: выбор подраздела (открывает WebApp) + Назад"""
    keyboard = []
    subs = SECTIONS[section_id]["subs"]
    

    for idx, sub_title in enumerate(subs, start=1):
        # Формируем ссылку на WebApp с параметрами раздела и подраздела
 #       url = f"{BASE_WEBAPP_URL}?section={section_id}&sub={idx}"
        url = WEBAPP_URL2
        title = f"{sub_title}{WIDE_PREFIX_2}"
        keyboard.append([
            InlineKeyboardButton(
                text=title,
 
                web_app=WebAppInfo(url=url),  # <-- открываем WebApp
            )
        ])

    # Кнопка назад к разделам (по-прежнему callback_data)
    keyboard.append([
        InlineKeyboardButton(
            text="⬅ Назад к разделам",
            callback_data="back:sections",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# ----- ХЕНДЛЕРЫ -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 1) Сообщение, которое включает постоянную кнопку "Обновить"
    await update.message.reply_text(
        "Кнопка 🔄 Обновить всегда внизу экрана.",
        reply_markup=refresh_keyboard,
    )

    # 2) Сообщение с меню разделов (inline-кнопки)
    """Команда /start — показываем разделы"""
    await update.message.reply_text(
        "Выберите раздел:",
        reply_markup=build_sections_keyboard(),
    )

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Просто заново показываем меню разделов
    await update.message.reply_text(
        "Обновлено. Выберите раздел:",
        reply_markup=build_sections_keyboard(),
    )



async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback'ов (только секции и кнопка Назад)"""
    query = update.callback_query
    data = query.data

    await query.answer()

    # Выбор раздела: sec:<id>
    if data.startswith("sec:"):
        _, sec_id = data.split(":", maxsplit=1)

        text = (
            f"Вы выбрали: {SECTIONS[sec_id]['title']}\n"
            f"Теперь выберите подраздел :"
        )
        await query.edit_message_text(
            text=text,
            reply_markup=build_subsections_keyboard(sec_id),
        )

    # Назад к разделам
    elif data == "back:sections":
        await query.edit_message_text(
            text="Выберите раздел:",
            reply_markup=build_sections_keyboard(),
        )

async def restore_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Меню:",
        reply_markup=refresh_keyboard
    )

# ----- ЗАПУСК БОТА -----
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.Regex("^🔄 Обновить$"), refresh))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, restore_keyboard))

    app.run_polling()


if __name__ == "__main__":
    main()