import os
import random
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect("pomoshnik.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            streak INTEGER DEFAULT 0,
            lang TEXT DEFAULT 'ru'
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("pomoshnik.db")
    cursor = conn.cursor()
    cursor.execute("SELECT streak FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if not result:
        cursor.execute("INSERT INTO users (user_id, streak) VALUES (?, 0)", (user_id,))
        conn.commit()
        result = (0,)
    conn.close()
    return result

def update_streak(user_id):
    conn = sqlite3.connect("pomoshnik.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET streak = streak + 1 WHERE user_id = ?", (user_id,))
    cursor.execute("SELECT streak FROM users WHERE user_id = ?", (user_id,))
    streak = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return streak

# ========== МОТИВИРУЮЩИЕ ФРАЗЫ ==========
MOTIVATION_PHRASES = [
    "Отлично! Помни: даже маленький шаг — это движение вперёд. Я в тебя верю! 💪",
    "Молодец! Сегодня ты сделал больше, чем вчера. А завтра сделаешь больше, чем сегодня.",
    "Так держать! Каждая победа, даже крошечная, строит твой путь к норме. 🏆",
    "Горжусь тобой! Дисциплина — это мышца, и ты её тренируешь каждый день.",
    "Супер! Не забывай: путь к норме — это марафон, а не спринт. Ты на правильном пути. ",
]

# ========== НАВИГАТОР ПО СТАТЬЯМ ==========
NAVIGATOR_CATEGORIES = {
    "🔐 Сид-фраза": [
        "📌 Что такое сид-фраза и почему её нельзя никому показывать: [ссылка]",
        "📌 Как безопасно хранить сид-фразу: [ссылка]",
        "📌 Что делать, если сид-фраза скомпрометирована: [ссылка]",
    ],
    " Фишинг": [
        " Как распознать фишингового бота: [ссылка]",
        "📌 Примеры фишинговых сообщений: [ссылка]",
        "📌 Как проверить подлинность ссылки: [ссылка]",
    ],
    " TON Proof": [
        " Что такое TON Proof и зачем он нужен: [ссылка]",
        "📌 Как безопасно проходить верификацию: [ссылка]",
        "📌 Типичные ошибки при TON Proof: [ссылка]",
    ],
}

# ========== КЛАВИАТУРЫ ==========
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📚 Уроки", callback_data="nav_main"),
            InlineKeyboardButton("🎮 Викторина", callback_data="quiz"),
        ],
        [
            InlineKeyboardButton("📊 Прогресс", callback_data="progress"),
            InlineKeyboardButton("❓ Помощь", callback_data="help"),
        ],
    ])

def navigator_keyboard():
    buttons = [[InlineKeyboardButton(cat, callback_data=f"nav_{i}")] for i, cat in enumerate(NAVIGATOR_CATEGORIES.keys())]
    buttons.append([InlineKeyboardButton("⬅️ Главное меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(buttons)

def quiz_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Лёгкий", callback_data="quiz_easy")],
        [InlineKeyboardButton("🟡 Средний", callback_data="quiz_medium")],
        [InlineKeyboardButton("🔴 Сложный", callback_data="quiz_hard")],
        [InlineKeyboardButton("️ Главное меню", callback_data="back_to_main")],
    ])

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Я — *Notcoin Shield Bot*, твой помощник в мире криптобезопасности.\n\n"
        "Здесь ты научишься:\n"
        " Защищать свою сид-фразу\n"
        "🎣 Распознавать фишинговых ботов\n"
        "🔑 Безопасно проходить TON Proof\n\n"
        "Выбери, что тебе интересно:"
    )
    await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ *Помощь*\n\n"
        " *Уроки* — изучи основы криптобезопасности\n"
        "🎮 *Викторина* — проверь свои знания\n"
        "📊 *Прогресс* — посмотри, сколько уроков пройдено\n"
        "❓ *Помощь* — это меню\n\n"
        "⚠️ Важно: этот бот никогда не запросит твою сид-фразу, приватный ключ или пароль!"
    )
    await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

# ========== ОБРАБОТЧИКИ КНОПОК ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_to_main":
        await query.edit_message_text("Главное меню 👇", reply_markup=main_menu_keyboard())

    elif data == "nav_main":
        await query.edit_message_text("📚 *Выбери тему урока:*\n\nКаждый урок займёт 2-3 минуты.", reply_markup=navigator_keyboard(), parse_mode="Markdown")

    elif data.startswith("nav_") and data[4:].isdigit():
        idx = int(data[4:])
        category = list(NAVIGATOR_CATEGORIES.keys())[idx]
        articles = "\n".join(NAVIGATOR_CATEGORIES[category])
        text = f"📂 *{category}*\n\n{articles}\n\n_Ссылки-заглушки — замени на свои!_"
        keyboard = [[InlineKeyboardButton("⬅️ К темам", callback_data="nav_main")],
                    [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_to_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "quiz":
        await query.edit_message_text("🎮 *Выбери уровень сложности:*\n\n🟢 Лёгкий — базовые вопросы\n🟡 Средний — практические ситуации\n🔴 Сложный — продвинутые сценарии", reply_markup=quiz_keyboard(), parse_mode="Markdown")

    elif data.startswith("quiz_"):
        level = data.split("_")[1]
        level_names = {"easy": "Лёгкий", "medium": "Средний", "hard": "Сложный"}
        await query.edit_message_text(f"🎮 Викторина: {level_names[level]}\n\nЗдесь будут вопросы по теме. (Функция в разработке)", reply_markup=main_menu_keyboard(), parse_mode="Markdown")

    elif data == "progress":
        user_id = update.effective_user.id
        streak = get_user(user_id)[0]
        text = (
            f"📊 *Твой прогресс*\n\n"
            f"✅ Уроки пройдено: 0 из 3\n"
            f"🎯 Викторины пройдено: 0\n"
            f"⭐ Верных ответов: 0\n\n"
            f"Продолжай учиться — каждый урок делает тебя безопаснее!"
        )
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

    elif data == "help":
        await help_cmd(update, context)

# ========== ЗАПУСК ==========
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Notcoin Shield Bot запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
