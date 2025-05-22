
import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import random
import string
import os
import cv2
import numpy as np
from PIL import Image
import io
import httpx

logging.basicConfig(level=logging.INFO)
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

def generate_gmail():
    user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{user}@gmail.com"

def get_direct_link(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я могу:\n1️⃣ Сгенерировать Gmail\n2️⃣ Получить прямую ссылку с Google Диска\n3️⃣ Прочитать QR по фото\n\nПришли мне ID файла, изображение или используй /gmail")

async def gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = generate_gmail()
    await update.message.reply_text(f"📧 Gmail: `{email}`", parse_mode="Markdown")

async def drive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Пришли ID файла Google Drive, например:\n`/drive 1x2x3x4x5`", parse_mode="Markdown")
        return
    file_id = context.args[0]
    direct_link = get_direct_link(file_id)
    await update.message.reply_text(f"🔗 Прямая ссылка:\n{direct_link}")

async def scan_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("📷 Пожалуйста, отправь изображение с QR-кодом.")
        return

    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    np_arr = np.frombuffer(photo_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(image)

    if data:
        await update.message.reply_text(f"✅ QR-код распознан:\n{data}")
    else:
        await update.message.reply_text("❌ QR-код не распознан.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gmail", gmail))
    app.add_handler(CommandHandler("drive", drive))
    app.add_handler(MessageHandler(filters.PHOTO, scan_qr))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
