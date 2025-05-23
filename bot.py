import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import re
import cv2
import numpy as np
import io
from PIL import Image

TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Используй команды:
"
        "/gmail — генерация Gmail-вариантов
"
        "/drive — преобразование ссылки Google Диска
"
        "/qr — распознавание QR-кода с картинки"
    )

async def gmail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите адрес Gmail:")

async def drive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте ссылку на файл Google Диска.")

async def qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте изображение с QR-кодом.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "@gmail.com" in text:
        prefix = text.replace("@gmail.com", "")
        variants = [f"{prefix}@gmail.com", f"{prefix}@googlemail.com"]
        for i in range(1, len(prefix)):
            variants.append(f"{prefix[:i]}.{prefix[i:]}@gmail.com")
        reply_text = "\n".join(variants)
        buttons = [
            [InlineKeyboardButton("Скопировать все", callback_data="copy_gmail")],
            [InlineKeyboardButton("Скачать .txt", callback_data="txt_gmail")],
            [InlineKeyboardButton("Экспорт в CSV", callback_data="csv_gmail")]
        ]
        await update.message.reply_text(reply_text, reply_markup=InlineKeyboardMarkup(buttons))
    elif "drive.google.com" in text:
        file_id = None
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", text)
        if match:
            file_id = match.group(1)
        else:
            alt_match = re.search(r"id=([a-zA-Z0-9_-]+)", text)
            if alt_match:
                file_id = alt_match.group(1)
        if file_id:
            link = f"https://drive.google.com/uc?export=download&id={file_id}"
            buttons = [
                [InlineKeyboardButton("Скопировать", callback_data="copy_link")],
                [InlineKeyboardButton("Перейти", url=link)]
            ]
            await update.message.reply_text(link, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await update.message.reply_text("Не удалось извлечь ID файла из ссылки.")
    else:
        await update.message.reply_text("Введите корректный адрес Gmail или ссылку на Google Диск.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    file_bytes = await photo.download_as_bytearray()
    np_arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    if data:
        buttons = [
            [InlineKeyboardButton("Скопировать", callback_data="copy_qr")],
            [InlineKeyboardButton("Перейти", url=data)]
        ]
        await update.message.reply_text(f"QR-код: {data}", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.message.reply_text("Не удалось распознать QR-код.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "copy_gmail":
        await query.edit_message_text("Скопируй текст вручную.")
    elif query.data == "txt_gmail":
        content = query.message.text.replace("\n", "\r\n")
        await query.message.reply_document(document=io.BytesIO(content.encode()), filename="gmail_variants.txt")
    elif query.data == "csv_gmail":
        content = query.message.text.replace("\n", "\n")
        csv_data = content.replace("\n", ",\n")
        await query.message.reply_document(document=io.BytesIO(csv_data.encode()), filename="gmail_variants.csv")
    elif query.data == "copy_link":
        await query.edit_message_text("Скопируй ссылку вручную.")
    elif query.data == "copy_qr":
        await query.edit_message_text("Скопируй QR-содержимое вручную.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gmail", gmail_command))
    app.add_handler(CommandHandler("drive", drive_command))
    app.add_handler(CommandHandler("qr", qr_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__":
    main()