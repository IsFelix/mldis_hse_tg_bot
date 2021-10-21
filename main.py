import telebot
from telebot import types

import sqlite3

import datetime

conn = sqlite3.connect('events.db')
cursor = conn.cursor()

try:
    query = "CREATE TABLE \"events\" (\"ID\" INTEGER UNIQUE, \"user_id\" INTEGER, \"event_dt\" TEXT, " \
            "\"meal_nm\" TEXT, \"meal_kcal\" INTEGER,  PRIMARY KEY (\"ID\"))"
    cursor.execute(query)
except:
    pass

with open("token_file.txt", "r") as f:
    token = f.read()

bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def send_keyboard(message, text="Привет, я бот, который поможет тебе собрать собирать информацию "
                                "о еде и ее калорийности"):
    keyboard = types.ReplyKeyboardMarkup(row_width=3)
    item_btn_1 = types.KeyboardButton('Добавить блюдо')
    item_btn_2 = types.KeyboardButton('Блюда за сегодня')
    item_btn_3 = types.KeyboardButton('Блюда за 3 дня')
    item_btn_4 = types.KeyboardButton('Удалить блюдо')
    item_btn_5 = types.KeyboardButton('Пока все')
    keyboard.add(item_btn_1, item_btn_2, item_btn_3)
    keyboard.add(item_btn_4, item_btn_5)

    msg = bot.send_message(message.from_user.id,
                           text=text, reply_markup=keyboard)

    bot.register_next_step_handler(msg, callback_worker)


def add_meal_data(msg):
    with sqlite3.connect('events.db') as con:
        cursor = con.cursor()
        cursor.execute('INSERT INTO events (user_id, event_dt, meal_nm, meal_kcal) VALUES (?, ?, ?, ?)',
                       (msg.from_user.id,
                        datetime.datetime.now(),
                        msg.text.split(",")[0],
                        msg.text.split(",")[1].replace(" ", "")))
        con.commit()
    bot.send_message(msg.chat.id, 'Запомню :-)')
    send_keyboard(msg, "Готово! Что-то еще?")


def get_today_meal_kcal_data(meal):
    meal_str = []
    kcal_sum = 0
    for val in list(enumerate(meal)):
        if val[1][0].split(" ")[0] == str(datetime.datetime.now().date()):
            meal_str.append(val[1][0].split(".")[0] + " - " +
                            val[1][1] + " - " +
                            str(val[1][2]) + '\n')
            kcal_sum += val[1][2]
    return ''.join(meal_str) + "\nСумма килокалорий за день: " + str(kcal_sum)


def show_today_meal_kcal(msg):
    with sqlite3.connect('events.db') as con:
        cursor = con.cursor()
        cursor.execute('SELECT event_dt, meal_nm, meal_kcal FROM events WHERE user_id=={}'.format(msg.from_user.id))
        meal = get_today_meal_kcal_data(cursor.fetchall())
        bot.send_message(msg.chat.id, meal)
        send_keyboard(msg, "Готово! Что-то еще?")


def get_last_3days_meal_kcal_data(meal):
    meal_str = []
    for val in list(enumerate(meal)):
        if val[1][0].split(" ")[0] >= str(datetime.datetime.now().date() - datetime.timedelta(days=2)):
            meal_str.append(val[1][0].split(".")[0] + " - " +
                            val[1][1] + " - " +
                            str(val[1][2]) + '\n')
    return ''.join(meal_str)


def show_last_3days_meal_kcal(msg):
    with sqlite3.connect('events.db') as con:
        cursor = con.cursor()
        cursor.execute('SELECT event_dt, meal_nm, meal_kcal FROM events WHERE user_id=={}'.format(msg.from_user.id))
        meal = get_last_3days_meal_kcal_data(cursor.fetchall())
        bot.send_message(msg.chat.id, meal)
        send_keyboard(msg, "Готово! Что-то еще?")


def delete_one_meal(msg):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with sqlite3.connect('events.db') as con:
        cursor = con.cursor()
        cursor.execute('SELECT event_dt, meal_nm, meal_kcal FROM events WHERE user_id=={}'.format(msg.from_user.id))
        meal = cursor.fetchall()
        for value in meal:
            markup.add(types.KeyboardButton(value[0] + " - " + value[1]))
        msg = bot.send_message(msg.from_user.id,
                               text="Выбери одно блюдо из списка",
                               reply_markup=markup)
        bot.register_next_step_handler(msg, delete_one_meal_)


def delete_one_meal_(msg):
    with sqlite3.connect('events.db') as con:
        cursor = con.cursor()
        cursor.execute('DELETE FROM events WHERE user_id==? AND meal_nm==?', (msg.from_user.id, (msg.text).split(" - ")[1]))
        bot.send_message(msg.chat.id, 'Отлично, все блюдо удалено!')
        send_keyboard(msg, "Готово! Что-то еще?")


def callback_worker(call):
    if call.text == "Добавить блюдо":
        msg = bot.send_message(call.chat.id, 'Давайте добавим блюдо и количество калорий! Напишите его в чат')
        bot.register_next_step_handler(msg, add_meal_data)

    elif call.text == "Блюда за сегодня":
        try:
            show_today_meal_kcal(call)
        except:
            bot.send_message(call.chat.id, 'Похоже, что Вы сегодня еще не ели или забыли добавить '
                                           'информацию о съеднном блюде')
            send_keyboard(call, "Чем еще могу помочь?")

    elif call.text == "Блюда за 3 дня":
        try:
            show_last_3days_meal_kcal(call)
        except:
            bot.send_message(call.chat.id, 'Вы ничего не ели 3 дня? Или просто не вностили записи :)')
            send_keyboard(call, "Чем еще могу помочь?")

    elif call.text == "Удалить блюдо":
        try:
            delete_one_meal(call)
        except:
            bot.send_message(call.chat.id, 'Готово! Блюдо удалено.')
            send_keyboard(call, "Чем еще могу помочь?")

    elif call.text == "Пока все":
        bot.send_message(call.chat.id, 'Хорошего дня! Когда захотите продолжнить нажмите на команду /start')

bot.polling(none_stop=True)
f.close()
