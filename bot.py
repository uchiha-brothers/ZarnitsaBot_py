import json
import random
import string
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from os import getenv

# Config
BOT_USERNAME = "tbc_file_store_bot"
STORAGE_FILE = "storage.json"
API_ID = int(getenv("API_ID"))
API_HASH = getenv("API_HASH")
BOT_TOKEN = getenv("BOT_TOKEN")

# Load and save functions
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

# Load data
storage = load_storage()

# Create bot
app = Client("FileStoringBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    args = message.text.split()
    chat_id = message.chat.id

    if len(args) > 1:
        random_id = args[1]
        if random_id in storage:
            data = storage[random_id]
            file_id = data["file_id"]
            caption = f"📎 File Name: {data['file_name']}\n📦 File Size: {data['file_size']}"
            if "caption" in data:
                caption += f"\n📝 Caption: {data['caption']}"

            media_type = data["type"]

            try:
                if media_type == "photo":
                    await client.send_photo(chat_id, photo=file_id, caption=caption)
                elif media_type == "video":
                    await client.send_video(chat_id, video=file_id, caption=caption)
                elif media_type == "audio":
                    await client.send_audio(chat_id, audio=file_id, caption=caption)
                elif media_type == "document":
                    await client.send_document(chat_id, document=file_id, caption=caption)
                elif media_type == "sticker":
                    await client.send_sticker(chat_id, sticker=file_id)
                else:
                    await message.reply("❌ Unsupported media type.")
            except Exception as e:
                await message.reply("❌ Failed to send media.")
        else:
            await message.reply("❌ Invalid or expired file link.")
    else:
        await message.reply_text(
            "👋 Welcome to the Secure File Storage Bot!\n\n"
            "📥 *Instructions:*\n"
            "1. Send me any file, photo, video, audio, or sticker.\n"
            "2. I will securely store it and generate a unique link for access.\n"
            "3. Use the link to retrieve the file anytime.\n"
            "🔒 Your files are stored securely and privately.",
            quote=True,
            parse_mode="markdown"
        )

@app.on_message(filters.private & filters.media)
async def save_file(client, message: Message):
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

            await message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
            return

    await message.reply("⚠️ Please send a valid file, photo, video, audio, or sticker.")

if __name__ == "__main__":
    app.run()
