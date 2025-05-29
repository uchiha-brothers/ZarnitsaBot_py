import json
import random
import string
import os
from flask import Flask, request
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Constants
BOT_USERNAME = "tbcfilestoringbot"
STORAGE_FILE = "storage.json"
CHANNEL_ID = -1002646820169
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")

# Flask server to keep alive
app_flask = Flask(__name__)

@app_flask.route("/")
def index():
    return "Bot is alive!", 200

# Load storage
def load_storage():
    try:
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_storage(data):
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_random_id(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

storage = load_storage()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    chat_id = update.effective_chat.id

    if args:
        random_id = args[0]
        if random_id in storage:
            data = storage[random_id]
            file_id = data["file_id"]
            caption = f"📎 File Name: {data['file_name']}\n📦 File Size: {data['file_size']}"
            if "caption" in data:
                caption += f"\n📝 Caption: {data['caption']}"

            media_type = data["type"]

            if media_type == "photo":
                await context.bot.send_photo(chat_id=chat_id, photo=file_id, caption=caption)
            elif media_type == "video":
                await context.bot.send_video(chat_id=chat_id, video=file_id, caption=caption)
            elif media_type == "audio":
                await context.bot.send_audio(chat_id=chat_id, audio=file_id, caption=caption)
            elif media_type == "document":
                await context.bot.send_document(chat_id=chat_id, document=file_id, caption=caption)
            elif media_type == "sticker":
                await context.bot.send_sticker(chat_id=chat_id, sticker=file_id)
            else:
                await update.message.reply_text("❌ Unsupported media type.")
        else:
            await update.message.reply_text("❌ Invalid file link or the file does not exist.")
    else:
        welcome = (
            "👋 Welcome to the Secure File Storage Bot!\n\n"
            "📥 *Instructions:*\n"
            "1. Send me any file, photo, video, audio, or sticker.\n"
            "2. I will securely store it and generate a unique link for access.\n"
            "3. Use the link to retrieve the file anytime.\n"
            "🔒 Your files are stored securely and privately."
        )
        await update.message.reply_markdown(welcome)

async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    allowed_types = ["document", "photo", "video", "audio", "sticker"]

    for media_type in allowed_types:
        media = getattr(message, media_type, None)
        if media:
            if media_type == "photo":
                file_id = media[-1].file_id
                file_name = "Photo"
                file_size = media[-1].file_size
            elif media_type == "sticker":
                file_id = media.file_id
                file_name = "Sticker"
                file_size = 0
            else:
                file_id = media.file_id
                file_name = getattr(media, "file_name", media_type.capitalize())
                file_size = getattr(media, "file_size", 0)

            caption = message.caption if media_type in ["photo", "video"] else ""
            random_id = generate_random_id()
            file_size_str = f"{round(file_size / 1024, 2)} KB" if file_size else "Unknown"

            storage[random_id] = {
                "file_id": file_id,
                "file_name": file_name,
                "file_size": file_size_str,
                "type": media_type,
            }
            if caption:
                storage[random_id]["caption"] = caption

            save_storage(storage)

            file_link = f"https://t.me/{BOT_USERNAME}?start={random_id}"

            msg = (
                f"✅ *Your file has been securely saved!*\n\n"
                f"📎 *File Name:* {file_name}\n"
                f"📦 *Size:* {file_size_str}\n"
            )
            if caption:
                msg += f"📝 *Caption:* {caption}\n"
            msg += (
                f"🔗 *Access Link:* [Click Here]({file_link})\n\n"
                f"⭕ *Permanent Link:* {file_link}"
            )

            await update.message.reply_markdown(msg)

            # Forward to private channel with user info
            user_info = (
                f"👤 Name: {user.full_name}\n"
                f"🆔 ID: `{user.id}`\n"
                f"🔗 Username: @{user.username if user.username else 'N/A'}"
            )

            await context.bot.send_message(chat_id=CHANNEL_ID, text=user_info)

            if media_type == "photo":
                await context.bot.send_photo(chat_id=CHANNEL_ID, photo=file_id, caption=caption)
            elif media_type == "video":
                await context.bot.send_video(chat_id=CHANNEL_ID, video=file_id, caption=caption)
            elif media_type == "audio":
                await context.bot.send_audio(chat_id=CHANNEL_ID, audio=file_id, caption=caption)
            elif media_type == "document":
                await context.bot.send_document(chat_id=CHANNEL_ID, document=file_id, caption=caption)
            elif media_type == "sticker":
                await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=file_id)

            return

    await update.message.reply_text("⚠️ Please send a valid file, photo, video, audio, or sticker.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ Invalid command. Use /start to begin.")

async def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    bot_app = ApplicationBuilder().token(TOKEN).build()

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_files))
    bot_app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Set webhook (full URL)
    await bot_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

    # Run webhook server (remove webhook_path)
    await bot_app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        path="/webhook",  # ✅ Use 'path' instead of 'webhook_path'
        web_app=app_flask,
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
