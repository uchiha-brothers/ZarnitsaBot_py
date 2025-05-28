from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

MESSAGES = {
    "start": {
        "ru": "Привет! Используйте команду:\n/compare cpu intel i7-12700 vs amd ryzen 7 5800x\nили\n/compare gpu nvidia rtx 3080 vs amd rx 6800",
        "ar": "مرحبًا! استخدم الأمر:\n/compare cpu intel i7-12700 vs amd ryzen 7 5800x\nأو\n/compare gpu nvidia rtx 3080 vs amd rx 6800",
        "en": "Hello! Use the command:\n/compare cpu intel i7-12700 vs amd ryzen 7 5800x\nor\n/compare gpu nvidia rtx 3080 vs amd rx 6800"
    },
    "error_format": {
        "ru": "Пожалуйста, используйте формат:\n/compare cpu|gpu название1 vs название2",
        "ar": "الرجاء استخدام الصيغة:\n/compare cpu|gpu اسم_المعالج_1 vs اسم_المعالج_2",
        "en": "Please use the format:\n/compare cpu|gpu name1 vs name2"
    },
    "not_found": {
        "ru": "Один или оба устройства не найдены в базе данных.",
        "ar": "واحد أو كلا المعالجين غير موجودين في قاعدة البيانات.",
        "en": "One or both devices not found in the database."
    },
    "lang_set": {
        "ru": "Язык установлен на русский.",
        "ar": "تم تعيين اللغة إلى العربية.",
        "en": "Language set to English."
    },
    "lang_invalid": {
        "ru": "Доступные языки: ru, ar, en",
        "ar": "اللغات المتاحة: ru, ar, en",
        "en": "Available languages: ru, ar, en"
    },
}

DATABASE = {
    "cpu": {
        "intel i7-12700": {"cores": 12, "threads": 20, "base_clock": 2.1, "boost_clock": 4.9, "tdp": 65},
        "amd ryzen 7 5800x": {"cores": 8, "threads": 16, "base_clock": 3.8, "boost_clock": 4.7, "tdp": 105},
    },
    "gpu": {
        "nvidia rtx 3080": {"vram": "10GB", "boost_clock": 1.7, "tdp": 320},
        "amd rx 6800": {"vram": "16GB", "boost_clock": 2.1, "tdp": 250},
    }
}

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    lang = context.user_data.get('lang', 'ru')  # هنا اللغة الافتراضية روسية
    text = MESSAGES.get(key, {}).get(lang, "")
    await update.message.reply_text(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_message(update, context, "start")

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        lang = context.args[0].lower()
        if lang in ['ru', 'ar', 'en']:
            context.user_data['lang'] = lang
            await update.message.reply_text(MESSAGES["lang_set"][lang])
        else:
            await update.message.reply_text(MESSAGES["lang_invalid"]["ru"])
    else:
        await update.message.reply_text("Usage: /lang ru|ar|en")

async def compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    text = update.message.text
    parts = text.split()
    try:
        vs_index = parts.index('vs')
    except ValueError:
        await send_message(update, context, "error_format")
        return

    category = parts[1].lower()
    item1 = " ".join(parts[2:vs_index]).lower()
    item2 = " ".join(parts[vs_index+1:]).lower()

    if category not in DATABASE:
        await send_message(update, context, "error_format")
        return

    data = DATABASE[category]

    if item1 not in data or item2 not in data:
        await send_message(update, context, "not_found")
        return

    spec1 = data[item1]
    spec2 = data[item2]

    if lang == 'ar':
        response = f"مقارنة بين:\n1. {item1}\n{spec1}\n\n2. {item2}\n{spec2}"
    elif lang == 'ru':
        response = f"Сравнение между:\n1. {item1}\n{spec1}\n\n2. {item2}\n{spec2}"
    else:
        response = f"Comparison between:\n1. {item1}\n{spec1}\n\n2. {item2}\n{spec2}"

    await update.message.reply_text(response)

if __name__ == '__main__':
    import os
    TOKEN = os.getenv("TELEGRAM_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", set_language))
    app.add_handler(CommandHandler("compare", compare))

    print("Бот запущен...")
    app.run_polling()
