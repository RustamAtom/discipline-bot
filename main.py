import telebot
from telebot import types
import schedule
import time
from database import cursor, conn, add_user, update_streak
from datetime import date
from database import get_top_users
import database
import os

TOKEN = os.environ["TOKEN"]
bot = telebot.TeleBot(TOKEN)

# Словарь, чтобы хранить выбор цели временно
user_goals = {}

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Учёба", "Тренировка", "Привычки")
    bot.send_message(chat_id, "Привет! Я твой Анти-Слив бот 👊\nВыбери свою цель на сегодня:", reply_markup=markup)

# Обработка выбора цели
@bot.message_handler(func=lambda message: message.text in ["Учёба", "Тренировка", "Привычки"])
def set_goal(message):
    chat_id = message.chat.id
    goal = message.text
    user_goals[chat_id] = goal  # временно сохраняем
    add_user(chat_id, goal)     # сохраняем в базе
    bot.send_message(chat_id, f"Отлично! Твоя цель на сегодня: {goal}\nЯ буду напоминать тебе утром и вечером.")

# Утреннее сообщение
def morning_message():
    cursor.execute("SELECT user_id FROM users")
    for row in cursor.fetchall():
        user_id = row[0]
        bot.send_message(user_id, "Доброе утро! Готов к своей цели на сегодня?")

# Вечернее сообщение с кнопками отчета
def evening_message():
    cursor.execute("SELECT user_id FROM users")
    for row in cursor.fetchall():
        user_id = row[0]
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("✅ Сделал", "❌ Не сделал")
        bot.send_message(user_id, "Как прошел твой день?", reply_markup=markup)

# Обработка отчета
@bot.message_handler(func=lambda message: message.text in ["✅ Сделал", "❌ Не сделал"])
def handle_report(message):
    chat_id = message.chat.id
    done_today = message.text == "✅ Сделал"
    update_streak(chat_id, done_today)
    cursor.execute("SELECT streak FROM users WHERE user_id=?", (chat_id,))
    streak = cursor.fetchone()[0]
    bot.send_message(chat_id, f"Текущий streak: {streak} дней! 💪")

# Планировщик для утренних и вечерних сообщений
schedule.every().day.at("09:00").do(morning_message)
schedule.every().day.at("21:00").do(evening_message)

# Функция для постоянного выполнения планировщика
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)
        
@bot.message_handler(commands=['top'])
def show_top(message):

    top_users = get_top_users()

    text = "🏆 Рейтинг дисциплины:\n\n"

    place = 1
    for user_id, streak in top_users:
        text += f"{place}. ID {user_id} — 🔥 {streak} дней\n"
        place += 1

    bot.send_message(message.chat.id, text)
    
from datetime import timedelta

@bot.message_handler(commands=['stats'])
def stats(message):

    done = database.get_week_stats(message.chat.id)

    bot.send_message(
        message.chat.id,
        f"📊 За последние 7 дней выполнено: {done}/7 дней"
    )
    
def reminder():

    database.cursor.execute("SELECT user_id FROM users")
    users = database.cursor.fetchall()

    for user in users:
        bot.send_message(
            user[0],
            "⏳ Ты сегодня уже выполнил свою цель?"
        )
        
schedule.every().day.at("12:00").do(reminder)
schedule.every().day.at("16:00").do(reminder)
schedule.every().day.at("20:00").do(reminder)

@bot.message_handler(commands=['me'])
def my_stats(message):
    user = database.get_user_info(message.chat.id)
    
    if user:
        goal, streak = user
        
        bot.send_message(message.chat.id, f"Твоя цель: {goal}\n" f"Серия: {streak} дней")
    else:
        bot.send_message(message.chat.id, 'Ты ещё не выбрал цель')
        
    rank = database.get_user_rank(message.chat.id)

    bot.send_message(
    message.chat.id,
    f"🏆 Место в рейтинге: {rank}"
    )
    
@bot.message_handler(commands=['week'])
def week_history(message):

    days = database.get_last_days(message.chat.id)

    text = "📆 Последние дни:\n"

    for day, done in days:
        mark = "✅" if done else "❌"
        text += f"{day} {mark}\n"

    bot.send_message(message.chat.id, text)

# Запускаем бота и планировщик
import threading
threading.Thread(target=run_schedule).start()
bot.infinity_polling(skip_pending=True)