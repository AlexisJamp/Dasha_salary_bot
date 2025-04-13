from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from datetime import datetime
from collections import defaultdict
import json
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f)

# Хранилище данных пользователей в памяти
raw_data = load_data()
user_data = defaultdict(lambda: {
    "today":[],
    "history":[]},
        {int(k): v for k, v in raw_data.items()
})

# Главное меню с кнопками
def get_main_menue():
    keyboard  = [
        [InlineKeyboardButton("Внести стоимость процедуры", callback_data="add")],
        [InlineKeyboardButton("Всё", callback_data="done")],
        [InlineKeyboardButton("Итог", callback_data="summary")],
        [InlineKeyboardButton("Закрыть месяц", callback_data="close_month")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Команда start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет я бт для расчета зарплаты.", reply_markup=get_main_menue())

# Обработка кнопок
async def handle_button(update: Update, conext: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id # Ответ принимаемый от пользователя по ID пользователя

    if query.data == "add":
        await query.message.reply_text("Введите стоимость процедуры числом:")
        conext.user_data["expecting_input"] = True

    elif query.data == 'done':
        today_sum = sum(user_data[user_id]['today'])
        percent = round(today_sum * 0.4, 2)
        user_data[user_id]['history'].append(today_sum)
        user_data[user_id]['today'].clear()
        save_data()
        await query.message.reply_text(f"Итог сегодняшнего дня: {today_sum} Лев \n40%: {percent} Лев")

    elif query.data == "summary":
        today_sum = sum(user_data[user_id]["today"])
        today_percent = round(today_sum * 0.4, 2)
        total_sum = sum(user_data[user_id]["history"])
        total_percent = round(total_sum * 0.4, 2)
        await query.message.reply_text(
            f"Сегодня: {today_sum} Лев (40% = {today_percent} Лев)\n"f"За всё время: {total_sum} Лев (40% = {total_percent} Лев)"
        )
    elif query.data == "close_month":
        total_sum = sum(user_data[user_id]["history"])
        if total_sum == 0:
            await query.message.reply_text("Нет данных для закрытия месяца.")
        else:
            percent = round(total_sum * 0.4, 2)
            await query.message.reply_text(
                f"Месяц закрыт!\nОбщий доход: {total_sum} Лев\n40%: {percent} Лев"
            )
            user_data[user_id]["history"].clear()
            save_data()

# Ввод суммы вручную
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if context.user_data.get("expecting_input"):
        try:
            value = float(update.message.text)
            user_data[user_id]['today'].append(value)
            save_data()
            await update.message.reply_text(f"Сумма {value} Лев добавлена.", reply_markup=get_main_menue())
        except ValueError:
            await update.message.reply_text("Пожалуйста введите число.")
        context.user_data["expecting_input"] = False

app = Application.builder().token(os.environ[TOKEN]).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_button))
app.add_handler((MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)))

app.run_polling()
