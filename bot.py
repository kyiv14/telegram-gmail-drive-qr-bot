import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

import re
import csv
import io
import base64
from PIL import Image
import cv2
import numpy as np

TOKEN = os.getenv("TELEGRAM_TOKEN") or "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_gmail_variants(email: str):
    name, domain = email.lower().split("@")
    if domain not in ["gmail.com", "googlemail.com"]:
        return []

    name = name.replace(".", "")
    variants = set()
    for i in range(1 << (len(name) - 1)):
        variant = name[0]
        for j in range(1, len(name)):
            if i & (1 << (j - 1)):
                variant += "."
            variant += name[j]
        variants.add(f"{variant}@gmail.com")
        variants.add(f"{variant}@googlemail.com")
    return sorted(variants)

def get_drive_direct_link(file_id: str):
    return f"https://drive.google.com/uc?export=download&id={file_id}"

def extract_file_id(url: str):
    patterns = [
        r"drive.google.com\/file\/d\/([a-zA-Z0-9_-]+)",
        r"drive.google.com\/open\?id=([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def extract_qr_code_from_image(image_bytes):
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(image)
        return data
    except Exception as e:
        logger.error(f"QR Decode error: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Используй команды:
"
        "/gmail — генерация вариантов Gmail
"
        "/drive — преобразование ссылки Google Диска
"
        "/qr — считать QR-код с картинки"
    )

async def gmail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["action"] = "gmail"
    await update.message.reply_text("📧 Введите адрес Gmail:")

async def drive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["action"] = "drive"
    await update.message.reply_text("🔗 Введите ссылку на Google Диск:")

async def qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["action"] = "qr"
    await update.message.reply_text("🖼 Пришлите изображение с QR-кодом:")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get("action")
    text = update.message.text.strip()

    if action == "gmail":
        variants = generate_gmail_variants(text)
        if not variants:
            await update.message.reply_text("❌ Неверный формат Gmail.")
            return

        joined = "\n".join(variants[:40])
        keyboard = [
            [InlineKeyboardButton("📋 Копировать всё", callback_data="copy_gmail")],
            [InlineKeyboardButton("⬇️ Скачать TXT", callback_data="download_txt")],
            [InlineKeyboardButton("📄 Экспорт в CSV", callback_data="download_csv")]
        ]
        context.user_data["gmail_variants"] = variants
        await update.message.reply_text(f"🔢 Варианты:
{joined}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == "drive":
        file_id = extract_file_id(text)
        if not file_id:
            await update.message.reply_text("❌ Не удалось извлечь ID файла.")
            return

        direct_link = get_drive_direct_link(file_id)
        keyboard = [
            [InlineKeyboardButton("📋 Скопировать ссылку", callback_data="copy_drive")],
            [InlineKeyboardButton("🌐 Перейти по ссылке", url=direct_link)]
        ]
        context.user_data["drive_link"] = direct_link
        await update.message.reply_text(f"✅ Прямая ссылка:
{direct_link}", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get("action")
    if action != "qr":
        return

    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    result = extract_qr_code_from_image(photo_bytes)
    if result:
        keyboard = [
            [InlineKeyboardButton("📋 Скопировать", callback_data="copy_qr")],
            [InlineKeyboardButton("🌐 Перейти", url=result)]
        ]
        context.user_data["qr_result"] = result
        await update.message.reply_text(f"📎 QR-код:
{result}", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("❌ Не удалось распознать QR-код.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "copy_gmail":
        text = "\n".join(context.user_data.get("gmail_variants", []))
        await query.message.reply_text(text)
    elif data == "download_txt":
        txt = "\n".join(context.user_data.get("gmail_variants", []))
        await query.message.reply_document(document=io.BytesIO(txt.encode()), filename="emails.txt")
    elif data == "download_csv":
        output = io.StringIO()
        writer = csv.writer(output)
        for email in context.user_data.get("gmail_variants", []):
            writer.writerow([email])
        await query.message.reply_document(document=io.BytesIO(output.getvalue().encode()), filename="emails.csv")
    elif data == "copy_drive":
        link = context.user_data.get("drive_link", "")
        await query.message.reply_text(link)
    elif data == "copy_qr":
        result = context.user_data.get("qr_result", "")
        await query.message.reply_text(result)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gmail", gmail_command))
    app.add_handler(CommandHandler("drive", drive_command))
    app.add_handler(CommandHandler("qr", qr_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()