import telebot
import random
from telebot import types

TOKEN = "7935884095:AAHl3H4IjzPg2Yq0svNwJ42kslwgfzr-NIc"
bot = telebot.TeleBot(TOKEN)

# تخزين بيانات اللاعبين واللغة المختارة
users_data = {}

class WordGame:
    def __init__(self, language='ru'):
        self.language = language
        if language == 'ru':
            self.words = ["яблоко", "апельсин", "банан", "груша", "клубника"]
            self.hint_text = {
                'start': "Угадай слово!",
                'correct': "✅ Верно!",
                'wrong': "❌ Неверно!",
                'win': "🎉 Поздравляю! Вы угадали слово:",
                'lose': "💔 Игра окончена! Слово было:"
            }
        else:  # العربية
            self.words = ["تفاح", "برتقال", "موز", "كمثرى", "فراولة"]
            self.hint_text = {
                'start': "!إخمن الكلمة",
                'correct': "!✅ صحيح",
                'wrong': "!❌ خطأ",
                'win': "🎉 !لقد ربحت، الكلمة كانت",
                'lose': "💔 !انتهت اللعبة، الكلمة كانت"
            }
        
        self.secret_word = random.choice(self.words)
        self.guessed = ["_"] * len(self.secret_word)
        self.attempts_left = 6
    
    def get_hint(self):
        return " ".join(self.guessed)

    def guess_letter(self, letter):
        letter = letter.lower()
        if letter in self.secret_word:
            for i, char in enumerate(self.secret_word):
                if char == letter:
                    self.guessed[i] = letter
            return True
        else:
            self.attempts_left -= 1
            return False

# أوامر البوت الأساسية
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_ru = types.KeyboardButton('🇷🇺 Русский')
    btn_ar = types.KeyboardButton('🇸🇦 العربية')
    markup.add(btn_ru, btn_ar)
    
    bot.send_message(
        message.chat.id,
        "Выберите язык / اختر اللغة",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text in ['🇷🇺 Русский', '🇸🇦 العربية'])
def set_language(message):
    chat_id = message.chat.id
    if message.text == '🇷🇺 Русский':
        users_data[chat_id] = {'language': 'ru'}
        bot.send_message(chat_id, "Язык установлен: Русский")
    else:
        users_data[chat_id] = {'language': 'ar'}
        bot.send_message(chat_id, "تم تعيين اللغة: العربية")

# بدء لعبة الكلمات
@bot.message_handler(commands=['game'])
def start_game(message):
    chat_id = message.chat.id
    if chat_id not in users_data:
        bot.send_message(chat_id, "Сначала выберите язык / اختر اللغة أولا")
        return
    
    language = users_data[chat_id].get('language', 'ru')
    users_data[chat_id]['game'] = WordGame(language)
    
    game = users_data[chat_id]['game']
    bot.send_message(
        chat_id,
        f"{game.hint_text['start']}\n{game.get_hint()}\n\nПопыток осталось: {game.attempts_left}"
        if language == 'ru' else
        f"{game.hint_text['start']}\n{game.get_hint()}\n\nمحاولات باقية: {game.attempts_left}"
    )

# معالجة التخمينات
@bot.message_handler(func=lambda m: True)
def handle_guess(message):
    chat_id = message.chat.id
    if chat_id not in users_data or 'game' not in users_data[chat_id]:
        return
    
    game = users_data[chat_id]['game']
    guess = message.text.strip().lower()
    
    if len(guess) != 1 or not guess.isalpha():
        return
    
    if game.guess_letter(guess):
        hint = game.get_hint()
        if "_" not in hint:
            bot.send_message(
                chat_id,
                f"{game.hint_text['win']} {game.secret_word}"
            )
            del users_data[chat_id]['game']
        else:
            bot.send_message(
                chat_id,
                f"{game.hint_text['correct']} {hint}\n\nПопыток осталось: {game.attempts_left}"
                if game.language == 'ru' else
                f"{game.hint_text['correct']} {hint}\n\nمحاولات باقية: {game.attempts_left}"
            )
    else:
        if game.attempts_left <= 0:
            bot.send_message(
                chat_id,
                f"{game.hint_text['lose']} {game.secret_word}"
            )
            del users_data[chat_id]['game']
        else:
            bot.send_message(
                chat_id,
                f"{game.hint_text['wrong']} {game.get_hint()}\n\nПопыток осталось: {game.attempts_left}"
                if game.language == 'ru' else
                f"{game.hint_text['wrong']} {game.get_hint()}\n\nمحاولات باقية: {game.attempts_left}"
            )

bot.polling()
