
import logging
import re
import csv
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import numpy as np
import cv2

logging.basicConfig(level=logging.INFO)
TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Используй команды:

/gmail - генерация вариантов Gmail
/drive - преобразование ссылки Google Диска
/qr - распознавание QR-кода")

async def gmail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите ваш Gmail адрес (пример: example@gmail.com):")

async def drive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите ссылку на файл Google Диска:")

async def qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пришлите изображение с QR-кодом.")

def generate_gmail_variants(email: str):
    if not email.endswith("@gmail.com"):
        return []
    username = email.split("@")[0]
    parts = [username[:i] + "." + username[i:] for i in range(1, len(username))]
    variants = sorted(set([username] + parts))
    gmail_variants = [v + "@gmail.com" for v in variants]
    googlemail_variants = [v + "@googlemail.com" for v in variants]
    return gmail_variants + googlemail_variants

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.endswith("@gmail.com"):
        variants = generate_gmail_variants(text)
        if variants:
            context.user_data["gmail_variants"] = variants
            keyboard = [
                [InlineKeyboardButton("📋 Скопировать всё", callback_data="copy_gmail")],
                [InlineKeyboardButton("📄 Скачать .txt", callback_data="download_txt"),
                 InlineKeyboardButton("📊 Скачать .csv", callback_data="download_csv")]
            ]
            await update.message.reply_text(
                "
".join(variants[:20]) + ("
..." if len(variants) > 20 else ""),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    elif "drive.google.com" in text:
        file_id_match = re.search(r"/d/([a-zA-Z0-9_-]+)|id=([a-zA-Z0-9_-]+)", text)
        file_id = file_id_match.group(1) if file_id_match and file_id_match.group(1) else (file_id_match.group(2) if file_id_match else None)
        if file_id:
            direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
            keyboard = [
                [InlineKeyboardButton("📋 Скопировать", callback_data="copy_drive")],
                [InlineKeyboardButton("➡ Перейти", url=direct_link)]
            ]
            context.user_data["drive_link"] = direct_link
            await update.message.reply_text(direct_link, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text("Не удалось извлечь ID файла.")
    else:
        await update.message.reply_text("Команда не распознана. Используй /gmail, /drive или /qr.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    file_path = await photo.download_to_drive()
    image = cv2.imread(file_path)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(image)
    if data:
        context.user_data["qr_data"] = data
        keyboard = [
            [InlineKeyboardButton("📋 Скопировать", callback_data="copy_qr")],
            [InlineKeyboardButton("➡ Перейти", url=data if data.startswith("http") else f"https://{data}")]
        ]
        await update.message.reply_text(data, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("QR-код не найден.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "copy_gmail":
        variants = context.user_data.get("gmail_variants", [])
        await query.message.reply_text("
".join(variants))
    elif data == "download_txt":
        variants = context.user_data.get("gmail_variants", [])
        file = io.StringIO("
".join(variants))
        await query.message.reply_document(document=InputFile(file, filename="emails.txt"))
    elif data == "download_csv":
        variants = context.user_data.get("gmail_variants", [])
        file = io.StringIO()
        writer = csv.writer(file)
        for v in variants:
            writer.writerow([v])
        file.seek(0)
        await query.message.reply_document(document=InputFile(file, filename="emails.csv"))
    elif data == "copy_drive":
        await query.message.reply_text(context.user_data.get("drive_link", "Нет ссылки"))
    elif data == "copy_qr":
        await query.message.reply_text(context.user_data.get("qr_data", "Нет данных"))

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gmail", gmail_command))
    app.add_handler(CommandHandler("drive", drive_command))
    app.add_handler(CommandHandler("qr", qr_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
