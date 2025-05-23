import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import httpx
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
import re

TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Используй команды:
"
        "/gmail — генерация Gmail-вариантов
"
        "/link — преобразование ссылки Google Диска
"
        "/qr — распознавание QR-кода с картинки"
    )

async def gmail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите Gmail адрес:")
    return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if re.match(r"^[\w.-]+@gmail\.com$", text, re.IGNORECASE):
        name = text.split("@")[0]
        variants = [f"{name.replace('.', '')[:i]}.{name.replace('.', '')[i:]}@gmail.com" for i in range(1, len(name))]
        await update.message.reply_text("\n".join(variants))
    else:
        await update.message.reply_text("Некорректный Gmail адрес.")

async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте ссылку Google Диска.")

async def qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте изображение с QR-кодом.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    byte_data = await file.download_as_bytearray()
    nparr = np.frombuffer(byte_data, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img_np)
    if data:
        await update.message.reply_text(f"QR-код содержит:
{data}")
    else:
        await update.message.reply_text("QR-код не распознан.")

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gmail", gmail_command))
app.add_handler(CommandHandler("link", link_command))
app.add_handler(CommandHandler("qr", qr_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

if __name__ == "__main__":
    app.run_polling()
