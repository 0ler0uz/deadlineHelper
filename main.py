import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
import schedule
import smtplib
from email.mime.text import MIMEText
import sqlite3
from telegram import Update

TOKEN = '6323519459:AAEB3ETBACHr5vnGWPsx9BB_ofoIdJr6H9Y'
EMAIL_USER = '0ler0uz@gmail.com'
EMAIL_PASSWORD = 'HenryFordsma11er'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
DATABASE_FILE = "reminders.db"

updater = Updater(TOKEN)
dp = updater.dispatcher


def start(update: Update):
    update.message.reply_text(
        "What’s up! Я самый ахрененный бот, который будет бить тебя по голове, если ты что-то забудешь или не успеешь. Чтобы тебя начали бить по голове, тыкни на эту штучку /setreminder")


dp.add_handler(CommandHandler("start", start))


def set_reminder(update, context):
    chat_id = update.message.chat_id
    context.user_data['chat_id'] = chat_id

    update.message.reply_text("Я бы сказал, что ты молодец, но это явно не так! Пиши уже что у тебя там.")
    update.message.reply_text("Мне еще твой имейлик нужен, там тоже по голове тебе стучать буду:")
    return 'email'


def get_email(update, context):
    email = update.message.text
    context.user_data['email'] = email

    update.message.reply_text("Номерок скинь(и желательно паспортные данные):")
    return 'phone'


def get_phone(update, context):
    phone = update.message.text
    context.user_data['phone'] = phone

    update.message.reply_text("скажи мне до какого времени мне тебя мутузить:")
    return 'deadline'


def get_deadline(update, context):
    deadline = update.message.text
    context.user_data['deadline'] = deadline

    update.message.reply_text("И ради чего я тебя мутузить буду:")
    return 'goal'


def get_goal(update, context, deadline=None):
    goal = update.message.text
    context.user_data['goal'] = goal

    # Сохраняем данные в базе данных или файле
    save_reminder_data(context.user_data)

    update.message.reply_text("Все готово солнышко, готовься страдать от головной боли")

    # Запускаем планировщик для отправки напоминания
    schedule.every().day.at(f"{context.user_data['deadline']} 00:00").do(send_reminder, context=context)

    return 'done'


def send_reminder(context):
    chat_id = context.job.context['chat_id']
    email = context.job.context['email']
    goal = context.job.context['goal']

    bot = telegram.Bot(token=TOKEN)
    bot.send_message(chat_id=chat_id,
                     text=f"Напоминание: Я тебя последний раз предупреждаю '{goal}' НЕ сделаешь все седня, тебя мертвым в канаве найдут!")

    send_email(email,
               f"Напоминание: Я тебя последний раз предупреждаю '{goal}' НЕ сделаешь все седня, тебя мертвым в канаве найдут!")


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

    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("setreminder", set_reminder))

    dp.add_handler(MessageHandler(filters.text & ~filters.command, get_email), group=1)
    dp.add_handler(MessageHandler(filters.text & ~filters.command, get_phone), group=2)
    dp.add_handler(MessageHandler(filters.text & ~filters.command, get_deadline), group=3)
    dp.add_handler(MessageHandler(filters.text & ~filters.command, get_goal), group=4)

    updater.start_polling()

    updater.idle()
