import os
import telebot
from telebot import types
import json
from flask import Flask, request

TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# تحميل بيانات العتاد
with open('hardware_data.json', 'r', encoding='utf-8') as f:
    hardware_data = json.load(f)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
    👋 Привет! Я бот для сравнения процессоров и видеокарт.
    
    🔍 Вы можете сравнить:
    - Процессоры (CPU)
    - Видеокарты (GPU)
    
    Используйте кнопки ниже для навигации.
    """
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_cpu = types.KeyboardButton('🔍 Сравнить процессоры')
    btn_gpu = types.KeyboardButton('🎮 Сравнить видеокарты')
    markup.add(btn_cpu, btn_gpu)
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🔍 Сравнить процессоры')
def compare_cpus(message):
    markup = types.InlineKeyboardMarkup()
    for cpu in hardware_data['cpus']:
        markup.add(types.InlineKeyboardButton(
            cpu['name'], 
            callback_data=f"cpu_{cpu['id']}"
        ))
    bot.send_message(
        message.chat.id, 
        "📊 Выберите процессор для сравнения:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == '🎮 Сравнить видеокарты')
def compare_gpus(message):
    markup = types.InlineKeyboardMarkup()
    for gpu in hardware_data['gpus']:
        markup.add(types.InlineKeyboardButton(
            gpu['name'], 
            callback_data=f"gpu_{gpu['id']}"
        ))
    bot.send_message(
        message.chat.id, 
        "🎮 Выберите видеокарту для сравнения:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('cpu_'))
def show_cpu_details(call):
    cpu_id = call.data.split('_')[1]
    cpu = next((item for item in hardware_data['cpus'] if item['id'] == cpu_id), None)
    
    if cpu:
        response = f"""
        🚀 Процессор: {cpu['name']}
        ⚙️ Ядра: {cpu['cores']}
        🚀 Тактовая частота: {cpu['clock']} GHz
        💰 Цена: ${cpu['price']}
        🔥 TDP: {cpu['tdp']}W
        """
        bot.send_message(call.message.chat.id, response)
    else:
        bot.send_message(call.message.chat.id, "Процессор не найден")

@bot.callback_query_handler(func=lambda call: call.data.startswith('gpu_'))
def show_gpu_details(call):
    gpu_id = call.data.split('_')[1]
    gpu = next((item for item in hardware_data['gpus'] if item['id'] == gpu_id), None)
    
    if gpu:
        response = f"""
        🎮 Видеокарта: {gpu['name']}
        🎮 Память: {gpu['memory']} GB
        🚀 Тактовая частота: {gpu['clock']} MHz
        💰 Цена: ${gpu['price']}
        """
        bot.send_message(call.message.chat.id, response)
    else:
        bot.send_message(call.message.chat.id, "Видеокарта не найдена")

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return '<h1>CPU/GPU Comparison Bot is Running!</h1>'

if __name__ == '__main__':
    if os.getenv('WEBHOOK_MODE', 'false').lower() == 'true':
        bot.remove_webhook()
        bot.set_webhook(url=os.getenv('WEBHOOK_URL') + '/' + TOKEN)
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
    else:
        bot.polling(none_stop=True)
