import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import re
import os
import csv
import io
import cv2
import numpy as np
from PIL import Image
import tempfile

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Привет! Используй команды:
"
        "/gmail - Генерация Gmail вариантов
"
        "/drive - Преобразование ссылки Google Drive
"
        "/qr - Сканирование QR-кода с изображения"
    )
    await update.message.reply_text(text)

def generate_gmail_variants(email):
    local, domain = email.lower().split('@')
    if domain not in ["gmail.com", "googlemail.com"]:
        return []
    variants = set()
    for i in range(1 << (len(local)-1)):
        with_dots = local[0]
        for j in range(1, len(local)):
            with_dots += ('.' if (i >> (j-1)) & 1 else '') + local[j]
        variants.add(with_dots + '@gmail.com')
        variants.add(with_dots + '@googlemail.com')
    return sorted(variants)

async def gmail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введи адрес Gmail (например, testuser@gmail.com):")

async def drive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вставь ссылку на файл в Google Drive:")

async def qr_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь изображение с QR-кодом.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if '@gmail.com' in text or '@googlemail.com' in text:
        variants = generate_gmail_variants(text)
        if variants:
            variants_text = "\n".join(variants)
            keyboard = [[
                InlineKeyboardButton("Скопировать все", callback_data="copy_gmail"),
                InlineKeyboardButton("Скачать .txt", callback_data="download_txt"),
                InlineKeyboardButton("Экспорт CSV", callback_data="download_csv")
            ]]
            context.user_data["gmail_variants"] = variants
            await update.message.reply_text(variants_text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text("Неверный Gmail адрес.")

    elif "drive.google.com" in text:
        file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)|id=([a-zA-Z0-9_-]+)', text)
        file_id = file_id_match.group(1) if file_id_match else file_id_match.group(2) if file_id_match else None
        if file_id:
            link = f"https://drive.google.com/uc?export=download&id={file_id}"
            context.user_data["drive_link"] = link
            keyboard = [[
                InlineKeyboardButton("Скопировать ссылку", callback_data="copy_drive"),
                InlineKeyboardButton("Перейти по ссылке", url=link)
            ]]
            await update.message.reply_text(link, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text("Не удалось извлечь ID из ссылки.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        await photo_file.download_to_drive(tmp.name)
        img = cv2.imread(tmp.name)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        if data:
            context.user_data["qr_data"] = data
            keyboard = [[
                InlineKeyboardButton("Скопировать", callback_data="copy_qr"),
                InlineKeyboardButton("Перейти", url=data if data.startswith("http") else f"http://{data}")
            ]]
            await update.message.reply_text(f"QR-код: {data}", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text("QR-код не найден.")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "copy_gmail":
        await query.edit_message_text("\n".join(context.user_data.get("gmail_variants", [])))
    elif query.data == "download_txt":
        text_data = "\n".join(context.user_data.get("gmail_variants", []))
        await query.message.reply_document(document=InputFile(io.BytesIO(text_data.encode()), filename="emails.txt"))
    elif query.data == "download_csv":
        output = io.StringIO()
        writer = csv.writer(output)
        for email in context.user_data.get("gmail_variants", []):
            writer.writerow([email])
        await query.message.reply_document(document=InputFile(io.BytesIO(output.getvalue().encode()), filename="emails.csv"))
    elif query.data == "copy_drive":
        await query.edit_message_text(context.user_data.get("drive_link", ""))
    elif query.data == "copy_qr":
        await query.edit_message_text(context.user_data.get("qr_data", ""))

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gmail", gmail_handler))
    app.add_handler(CommandHandler("drive", drive_handler))
    app.add_handler(CommandHandler("qr", qr_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_buttons))

    app.run_polling()

if __name__ == "__main__":
    main()
