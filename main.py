import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
import schedule
import time
import smtplib
from email.mime.text import MIMEText
import sqlite3

# Замените на свои значения
TOKEN = '6909822287:AAEhmXuNfRmK_4djIlJoFPXfIe98aKZR91M'
EMAIL_USER = '0ler0uz@gmail.com'
EMAIL_PASSWORD = 'HenryFordsma11er'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
DATABASE_FILE = "reminders.db"


def start(update, context):
    update.message.reply_text("Привет! Я бот-напоминалка. Чтобы установить напоминание, используйте /setreminder")


def set_reminder(update, context):
    chat_id = update.message.chat_id
    context.user_data['chat_id'] = chat_id

    update.message.reply_text("Отлично! Давайте установим напоминание.")
    update.message.reply_text("Введите свой адрес электронной почты:")
    return 'email'


def get_email(update, context):
    email = update.message.text
    context.user_data['email'] = email

    update.message.reply_text("Теперь введите свой телефон:")
    return 'phone'


def get_phone(update, context):
    phone = update.message.text
    context.user_data['phone'] = phone

    update.message.reply_text("Введите срок дедлайна (например, 2023-12-31):")
    return 'deadline'


def get_deadline(update, context):
    deadline = update.message.text
    context.user_data['deadline'] = deadline

    update.message.reply_text("Введите цель/задачу, которую необходимо выполнить:")
    return 'goal'


def get_goal(update, context, deadline=None):
    goal = update.message.text
    context.user_data['goal'] = goal

    # Сохраняем данные в базе данных или файле
    save_reminder_data(context.user_data)

    update.message.reply_text("Напоминание установлено! Я вас оповещу за час до дедлайна.")

    # Запускаем планировщик для отправки напоминания
    schedule.every().day.at(f"{deadline} 00:00").do(send_reminder, context=context)

    return 'done'


def send_reminder(context):
    chat_id = context.job.context['chat_id']
    email = context.job.context['email']
    goal = context.job.context['goal']

    # Отправка напоминания в Telegram
    bot = telegram.Bot(token=TOKEN)
    bot.send_message(chat_id=chat_id, text=f"Напоминание: Срок выполнения задачи '{goal}' истекает сегодня!")

    # Отправка напоминания на электронную почту
    send_email(email, f"Напоминание: Срок выполнения задачи '{goal}' истекает сегодня!")


def save_reminder_data(data):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO reminders (chat_id, email, phone, deadline, goal)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['chat_id'], data['email'], data['phone'], data['deadline'], data['goal']))

    conn.commit()
    conn.close()


def create_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            chat_id INTEGER,
            email TEXT,
            phone TEXT,
            deadline TEXT,
            goal TEXT
        )
    ''')

    conn.commit()
    conn.close()


def send_email(to_email, message):
    msg = MIMEText(message)
    msg['Subject'] = 'Напоминание о задаче'
    msg['From'] = EMAIL_USER
    msg['To'] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())


def main():
    create_table()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("setreminder", set_reminder))

    dp.add_handler(MessageHandler(filters.text & ~filters.command, get_email), group=1)
    dp.add_handler(MessageHandler(filters.text & ~filters.command, get_phone), group=2)
    dp.add_handler(MessageHandler(filters.text & ~filters.command, get_deadline), group=3)
    dp.add_handler(MessageHandler(filters.text & ~filters.command, get_goal), group=4)

    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
