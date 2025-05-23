
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import re
import numpy as np
import cv2
from PIL import Image
import io

TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👋 Привет! Используй команды:\n/gmail, /link, /qr, /start, /help")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Справка: этот бот помогает с генерацией Gmail, обработкой ссылок и QR.")

async def gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Введите ваш Gmail адрес.")

async def handle_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        email = update.message.text.strip()
        if "@gmail.com" in email:
            prefix = email.split("@")[0]
            variants = [f"{prefix.replace('.', '')[:i]}.{prefix.replace('.', '')[i:]}@gmail.com"
                        for i in range(1, len(prefix.replace('.', '')))]
            reply = "\n".join(set(variants[:20])) or "Варианты не найдены."
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text("Это не Gmail адрес.")

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Отправьте ссылку Google Диска.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    match = re.search(r"https://drive.google.com/file/d/([\w-]+)", url)
    if match:
        file_id = match.group(1)
        direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
        await update.message.reply_text(direct_link)
    else:
        await update.message.reply_text("Ссылка не распознана.")

async def qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Отправьте изображение с QR-кодом.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    image = Image.open(io.BytesIO(photo_bytes)).convert('RGB')
    open_cv_image = np.array(image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(open_cv_image)
    if data:
        await update.message.reply_text(f"QR-код содержит: {data}")
    else:
        await update.message.reply_text("QR-код не найден.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("gmail", gmail))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("@gmail.com"), handle_gmail))
    app.add_handler(CommandHandler("link", link))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("drive.google.com"), handle_link))
    app.add_handler(CommandHandler("qr", qr))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
