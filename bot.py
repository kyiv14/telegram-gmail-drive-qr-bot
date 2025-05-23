
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import re
import io
import csv
from PIL import Image
import numpy as np
import cv2

TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_gmail_variants(base_email: str):
    username, domain = base_email.split("@")
    if domain != "gmail.com":
        return []
    variants = set()
    for i in range(1 << (len(username) - 1)):
        s = username[0]
        for j in range(1, len(username)):
            s += ("." if (i >> (j - 1)) & 1 else "") + username[j]
        variants.add(s + "@gmail.com")
        variants.add(s + "@googlemail.com")
    return sorted(variants)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Используй команды:
"
        "/gmail <ваша_почта>
"
        "/drive <google_drive_url>
"
        "или отправьте изображение с QR-кодом"
    )

async def handle_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите email, например: /gmail test@gmail.com")
        return
    base_email = context.args[0]
    variants = generate_gmail_variants(base_email)
    if not variants:
        await update.message.reply_text("Почта должна быть в домене gmail.com")
        return
    txt_output = "
".join(variants)
    keyboard = [
        [InlineKeyboardButton("Скопировать все", switch_inline_query=txt_output)],
        [InlineKeyboardButton("Скачать .txt", callback_data="download_txt")],
        [InlineKeyboardButton("Экспорт CSV", callback_data="download_csv")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(txt_output, reply_markup=reply_markup)
    context.user_data["variants"] = variants

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    variants = context.user_data.get("variants", [])
    if query.data == "download_txt":
        txt = "
".join(variants)
        bio = io.BytesIO(txt.encode("utf-8"))
        bio.name = "emails.txt"
        await query.message.reply_document(bio)
    elif query.data == "download_csv":
        bio = io.BytesIO()
        writer = csv.writer(io.TextIOWrapper(bio, "utf-8", newline=""))
        for v in variants:
            writer.writerow([v])
        bio.seek(0)
        bio.name = "emails.csv"
        await query.message.reply_document(bio)

async def handle_drive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите ссылку, например: /drive https://drive.google.com/file/d/ID/view")
        return
    url = context.args[0]
    match = re.search(r"/d/([\w-]+)", url)
    if not match:
        await update.message.reply_text("Неверная ссылка")
        return
    file_id = match.group(1)
    direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
    keyboard = [
        [InlineKeyboardButton("Преобразовать и скопировать", switch_inline_query=direct_link)],
        [InlineKeyboardButton("Перейти", url=direct_link)]
    ]
    await update.message.reply_text(direct_link, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    bio = io.BytesIO()
    await photo_file.download_to_memory(out=bio)
    bio.seek(0)
    image = Image.open(bio)
    image_np = np.array(image.convert("RGB"))
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(image_np)
    if data:
        keyboard = [
            [InlineKeyboardButton("Скопировать", switch_inline_query=data)],
            [InlineKeyboardButton("Перейти", url=data)]
        ]
        await update.message.reply_text(f"QR-содержимое: {data}", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("QR-код не найден")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gmail", handle_gmail))
    app.add_handler(CommandHandler("drive", handle_drive))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
