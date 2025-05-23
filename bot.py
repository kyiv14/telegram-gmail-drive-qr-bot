import os
import csv
import io
import re
import logging
import numpy as np
import httpx
from PIL import Image
import cv2
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"
logging.basicConfig(level=logging.INFO)

def generate_gmail_variants(base):
    parts = base.split("@")[0]
    domain = base.split("@")[1] if "@" in base else "gmail.com"
    dots = [i for i in range(1, len(parts))]
    combinations = set()
    for i in range(1, 1 << len(dots)):
        s = list(parts)
        for j in range(len(dots)):
            if i & (1 << j):
                s.insert(dots[j] + j, ".")
        combinations.add("".join(s))
    combinations.add(parts)
    emails = sorted({f"{x}@gmail.com" for x in combinations} | {f"{x}@googlemail.com" for x in combinations})
    return emails

def generate_drive_link(file_id):
    return f"https://drive.google.com/uc?id={file_id}"

def extract_drive_id(text):
    patterns = [
        r"https?://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)",
        r"^([a-zA-Z0-9_-]{25,})$"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Используй команды:
"
        "/gmail - генерация вариантов gmail
"
        "/drive - прямая ссылка по ID
"
        "/qr - отправь изображение с QR-кодом"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "@" in text:
        emails = generate_gmail_variants(text)
        csv_buf = io.StringIO()
        csv_writer = csv.writer(csv_buf)
        csv_writer.writerow(["Email"])
        for e in emails:
            csv_writer.writerow([e])
        csv_buf.seek(0)
        keyboard = [[
            InlineKeyboardButton("Скачать .txt", callback_data="download_txt"),
            InlineKeyboardButton("Экспорт в .csv", callback_data="download_csv")
        ]]
        context.user_data["emails"] = emails
        await update.message.reply_text(
            f"Сгенерировано {len(emails)} адресов.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif extract_drive_id(text):
        file_id = extract_drive_id(text)
        link = generate_drive_link(file_id)
        keyboard = [[
            InlineKeyboardButton("Перейти", url=link),
            InlineKeyboardButton("Скопировать", callback_data="copy_link")
        ]]
        context.user_data["link"] = link
        await update.message.reply_text("Вот прямая ссылка:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("Не понял сообщение. Используй команды.")

async def qr_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    image_bytes = await photo.download_as_bytearray()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    opencv_img = np.array(img)
    opencv_img = cv2.cvtColor(opencv_img, cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(opencv_img)
    if data:
        keyboard = [[
            InlineKeyboardButton("Скопировать", callback_data="copy_qr"),
            InlineKeyboardButton("Перейти", url=data)
        ]]
        context.user_data["qr"] = data
        await update.message.reply_text(f"QR-содержимое: {data}", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("QR-код не распознан.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "download_txt":
        txt = "
".join(context.user_data.get("emails", []))
        await query.message.reply_document(InputFile(io.BytesIO(txt.encode()), filename="emails.txt"))
    elif query.data == "download_csv":
        csv_buf = io.StringIO()
        csv_writer = csv.writer(csv_buf)
        csv_writer.writerow(["Email"])
        for e in context.user_data.get("emails", []):
            csv_writer.writerow([e])
        csv_buf.seek(0)
        await query.message.reply_document(InputFile(io.BytesIO(csv_buf.getvalue().encode()), filename="emails.csv"))

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gmail", start))
app.add_handler(CommandHandler("drive", start))
app.add_handler(CommandHandler("qr", start))
app.add_handler(MessageHandler(filters.PHOTO, qr_image))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.COMMAND, start))
app.add_handler(MessageHandler(filters.StatusUpdate.ALL, start))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.add_handler(MessageHandler(filters.ALL, handle_text))
app.run_polling()