import os
import telebot
from telebot import types
import random
from flask import Flask, request  # للوضع السحابي

# تهيئة البوت
TOKEN = os.getenv('BOT_TOKEN') or "7935884095:AAHl3H4IjzPg2Yq0svNwJ42kslwgfzr-NIc"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)  # للوضع السحابي

# ============ الألعاب ============
class NumberGame:
    """لعبة تخمين الرقم"""
    def __init__(self):
        self.number = random.randint(1, 100)
        self.attempts = 0

class WordGame:
    """لعبة تخمين الكلمة"""
    def __init__(self, language='ar'):
        self.language = language
        self.words = {
            'ar': ["تفاح", "برتقال", "موز", "كمثرى"],
            'ru': ["яблоко", "апельсин", "банан", "груша"]
        }[language]
        self.secret_word = random.choice(self.words)
        self.guessed = ["_"] * len(self.secret_word)
        self.attempts_left = 6

# تخزين بيانات اللاعبين
users_data = {}

# ============ أوامر البوت ============
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_ar = types.KeyboardButton('🇸🇦 العربية')
    btn_ru = types.KeyboardButton('🇷🇺 Русский')
    markup.add(btn_ar, btn_ru)
    
    bot.send_message(
        message.chat.id,
        "اختر اللغة / Выберите язык",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text in ['🇸🇦 العربية', '🇷🇺 Русский'])
def set_language(message):
    chat_id = message.chat.id
    if message.text == '🇷🇺 Русский':
        users_data[chat_id] = {'language': 'ru'}
        bot.send_message(chat_id, "Язык установлен: Русский")
    else:
        users_data[chat_id] = {'language': 'ar'}
        bot.send_message(chat_id, "تم تعيين اللغة: العربية")

@bot.message_handler(commands=['game'])
def game_menu(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('🔢 تخمين الرقم')
    btn2 = types.KeyboardButton('📝 تخمين الكلمة')
    markup.add(btn1, btn2)
    
    bot.send_message(
        chat_id,
        "اختر نوع اللعبة:",
        reply_markup=markup
    )

# ============ معالجة الألعاب ============
@bot.message_handler(func=lambda m: m.text == '🔢 تخمين الرقم')
def start_number_game(message):
    chat_id = message.chat.id
    users_data[chat_id] = {'game': NumberGame(), 'type': 'number'}
    bot.send_message(chat_id, "أنا أفكر في رقم بين 1 و100، حاول تخمينه!")

@bot.message_handler(func=lambda m: m.text == '📝 تخمين الكلمة')
def start_word_game(message):
    chat_id = message.chat.id
    lang = users_data.get(chat_id, {}).get('language', 'ar')
    users_data[chat_id] = {'game': WordGame(lang), 'type': 'word'}
    game = users_data[chat_id]['game']
    bot.send_message(
        chat_id,
        f"الكلمة: {' '.join(game.guessed)}\n\nالمحاولات المتبقية: {game.attempts_left}"
    )

@bot.message_handler(func=lambda m: True)
def handle_guesses(message):
    chat_id = message.chat.id
    if chat_id not in users_data or 'game' not in users_data[chat_id]:
        return
    
    game_data = users_data[chat_id]
    
    if game_data['type'] == 'number':
        handle_number_guess(message)
    elif game_data['type'] == 'word':
        handle_word_guess(message)

def handle_number_guess(message):
    chat_id = message.chat.id
    try:
        guess = int(message.text)
        game = users_data[chat_id]['game']
        game.attempts += 1
        
        if guess < game.number:
            bot.reply_to(message, "أعلى! ⬆️")
        elif guess > game.number:
            bot.reply_to(message, "أقل! ⬇️")
        else:
            bot.reply_to(message, f"🎉 صحيح! الرقم كان {game.number}، استغرقت {game.attempts} محاولات")
            del users_data[chat_id]['game']
    except ValueError:
        bot.reply_to(message, "الرجاء إدخال رقم صحيح")

def handle_word_guess(message):
    chat_id = message.chat.id
    guess = message.text.strip().lower()
    game = users_data[chat_id]['game']
    
    if len(guess) != 1 or not guess.isalpha():
        bot.reply_to(message, "الرجاء إدخال حرف واحد فقط")
        return
    
    if game.guess_letter(guess):
        hint = game.get_hint()
        if "_" not in hint:
            bot.reply_to(message, f"🎉 فزت! الكلمة كانت: {game.secret_word}")
            del users_data[chat_id]['game']
        else:
            bot.reply_to(message, f"صح! {hint}\n\nالمحاولات المتبقية: {game.attempts_left}")
    else:
        if game.attempts_left <= 0:
            bot.reply_to(message, f"💔 انتهت المحاولات! الكلمة كانت: {game.secret_word}")
            del users_data[chat_id]['game']
        else:
            bot.reply_to(message, f"خطأ! {game.get_hint()}\n\nالمحاولات المتبقية: {game.attempts_left}")

# ============ تشغيل البوت ============
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return "OK", 200

if __name__ == '__main__':
    # التشغيل المحلي
    if os.getenv('RENDER'):  # إذا كان على Render
        bot.remove_webhook()
        bot.set_webhook(url=os.getenv('WEBHOOK_URL') + TOKEN)
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
    else:  # التشغيل المحلي
        bot.infinity_polling()
