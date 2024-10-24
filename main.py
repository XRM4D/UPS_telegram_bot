import telebot
import requests
from telebot import types
import time
import threading

bot = telebot.TeleBot('')
RAPIDAPI_KEY = '9f968fd171mshcaab8da16945f5cp177372jsn6e7b06507896'
user_data = {}

def stop_previous_prognos(chat_id):
    if chat_id in user_data and user_data[chat_id]['prognos'] is not None:
        user_data[chat_id]['prognos_working'].clear()
        user_data[chat_id]['prognos'].join()
        user_data[chat_id]['prognos'] = None

@bot.message_handler(commands=['start'])
def privet(message):
    bot.send_message(message.chat.id, "Бот для просмотра погоды. Для указания города введите /weather")

@bot.message_handler(commands=['weather'])
def thapros_goroda(message):
    stop_previous_prognos(message.chat.id)
    user_data[message.chat.id] = {
        'weath': 1,
        'city': '',
        'period': 0,
        'prognos': None,
        'prognos_working': threading.Event()
    }
    bot.send_message(message.chat.id, 'Введите город, погоду которого вы хотите узнать')

@bot.message_handler(commands=['stop'])
def stop(message):
    stop_previous_prognos(message.chat.id)

@bot.message_handler(content_types=['text'])
def get_pogoda_period(message):
    if message.chat.id not in user_data or user_data[message.chat.id]['weath'] != 1:
        return

    user_data[message.chat.id]['city'] = message.text.strip()
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("1 минута", callback_data="1_минута")
    button2 = types.InlineKeyboardButton("12 часов", callback_data="12_часов")
    button3 = types.InlineKeyboardButton("24 часа", callback_data="24_часа")
    markup.add(button1, button2, button3)
    bot.send_message(message.chat.id, "Выберите период отправки прогноза:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def obrabotka_perioda(call):
    user_data[call.message.chat.id]['period'] = {
        "1_минута": 60,
        "12_часов": 43200,
        "24_часа": 86400
    }[call.data]
    bot.send_message(call.message.chat.id, f"Период: {call.data.replace('_', ' ')}")

    stop_previous_prognos(call.message.chat.id)
    start_prognos(call.message)

def send_weather_prognos(chat_id):
    while user_data[chat_id]['prognos_working'].is_set():
        url = "https://weatherapi-com.p.rapidapi.com/current.json"
        querystring = {"q": user_data[chat_id]['city'], "lang": "ru"}

        headers = {
            'x-rapidapi-host': "weatherapi-com.p.rapidapi.com",
            'x-rapidapi-key': RAPIDAPI_KEY
        }

        try:
            response = requests.get(url, headers=headers, params=querystring)
            data = response.json()

            location = data['location']['name']
            temperature = data['current']['temp_c']
            weather = data['current']['condition']['text']

            weather_info = (f"Город {location}\n"
                            f"Температура: {temperature}°C\n"
                            f"Погода: {weather}\n\n"
                            f"Остановить прогноз /stop")

            bot.send_message(chat_id, weather_info)


        except Exception as e:
            print("error ", e)
            bot.send_message(chat_id, "Ошибка при получении данных о погоде")

        time.sleep(user_data[chat_id]['period'])

def start_prognos(message):
    chat_id = message.chat.id
    user_data[chat_id]['prognos_working'].set()
    user_data[chat_id]['prognos'] = threading.Thread(target=send_weather_prognos, args=(chat_id,))
    user_data[chat_id]['prognos'].start()

print('Бот успешно запущен')
bot.polling()
