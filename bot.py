
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import re, io
import numpy as np
import cv2
from PIL import Image

TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

logging.basicConfig(level=logging.INFO)

def extract_file_id(drive_url: str) -> str | None:
    patterns = [
        r'drive.google.com\/file\/d\/([a-zA-Z0-9_-]+)',
        r'drive.google.com\/open\?id=([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, drive_url)
        if match:
            return match.group(1)
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь:
- Ссылку на Google Диск
- Фото с QR-кодом")

async def handle_drive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    file_id = extract_file_id(message)
    if not file_id:
        await update.message.reply_text("❗ Не удалось извлечь ID файла из ссылки Google Диска.")
        return
    direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
    keyboard = [
        [InlineKeyboardButton("📋 Скопировать ссылку", callback_data=f"copy_drive|{direct_link}")],
        [InlineKeyboardButton("🔗 Перейти по ссылке", url=direct_link)]
    ]
    await update.message.reply_text(f"✅ Прямая ссылка:\n{direct_link}", reply_markup=InlineKeyboardMarkup(keyboard))

def decode_qr_from_photo(file_bytes) -> str | None:
    image = Image.open(file_bytes).convert("RGB")
    img_np = np.array(image)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img_np)
    return data if data else None

async def handle_qr_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()
    qr_data = decode_qr_from_photo(io.BytesIO(photo_bytes))
    if not qr_data:
        await update.message.reply_text("❌ QR-код не распознан.")
        return
    keyboard = [[InlineKeyboardButton("📋 Скопировать", callback_data=f"copy_qr|{qr_data}")]]
    if qr_data.startswith("http"):
        keyboard.append([InlineKeyboardButton("🔗 Перейти по ссылке", url=qr_data)])
    await update.message.reply_text(f"✅ QR-содержимое:\n{qr_data}", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("copy_drive|") or data.startswith("copy_qr|"):
        _, payload = data.split("|", 1)
        await query.message.reply_text(f"📋 Скопировано:\n{payload}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("drive.google.com"), handle_drive_link))
    app.add_handler(MessageHandler(filters.PHOTO, handle_qr_photo))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
