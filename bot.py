import json
import random
import string
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# In-memory storage file or use JSON file
STORAGE_FILE = "storage.json"

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

# Telegram bot token and bot username (used for generating links)
BOT_USERNAME = "tbcfilestoringbot"

# Load storage on startup
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
                # Stickers can't have captions
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
    chat_id = message.chat.id

    allowed_types = ["document", "photo", "video", "audio", "sticker"]

    # We'll check the types in priority order
    for media_type in allowed_types:
        media = getattr(message, media_type, None)
        if media:
            # For photo, it's a list of PhotoSize; take the highest resolution (last)
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

            # Save caption only for photo and video
            caption = message.caption if media_type in ["photo", "video"] else ""

            # Generate random ID
            random_id = generate_random_id()

            # Format file size
            if file_size:
                file_size_str = f"{round(file_size / 1024, 2)} KB"
            else:
                file_size_str = "Unknown"

            # Save to storage
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
            return

    # If no media found
    await update.message.reply_text("⚠️ Please send a valid file, photo, video, audio, or sticker.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ Invalid command. Use /start to begin.")

if __name__ == "__main__":
    import os

    TOKEN = os.getenv("TELEGRAM_TOKEN")  # Set your bot token in environment variable

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_files))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))  # catch unknown commands

    print("Bot is running...")
    app.run_polling()
