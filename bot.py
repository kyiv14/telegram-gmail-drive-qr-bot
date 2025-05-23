
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import numpy as np
import cv2
import io

TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Привет! Используй команды:
"
        "/gmail <email> – сгенерировать варианты Gmail
"
        "/drive <file_id> – получить прямую ссылку на файл
"
        "/qr – отправь изображение с QR кодом"
    )
    await update.message.reply_text(text)

def generate_gmail_variants(email: str):
    local, domain = email.split('@')
    variants = set()

    if domain not in ("gmail.com", "googlemail.com"):
        return []

    def insert_dots(name):
        return [name[:i] + '.' + name[i:] for i in range(1, len(name))]

    queue = [local]
    for _ in range(len(local) - 1):
        queue += [v for x in queue for v in insert_dots(x) if '.' not in x]

    for variant in set(queue):
        variants.add(f"{variant}@gmail.com")
        variants.add(f"{variant}@googlemail.com")

    return sorted(variants)

async def gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи адрес Gmail, например: /gmail example@gmail.com")
        return

    email = context.args[0]
    variants = generate_gmail_variants(email)
    if not variants:
        await update.message.reply_text("Некорректный Gmail адрес.")
        return

    text = "
".join(variants)
    keyboard = [
        [InlineKeyboardButton("Скопировать все", callback_data="copy_gmail")],
        [InlineKeyboardButton("Скачать txt", callback_data="download_txt")],
        [InlineKeyboardButton("Экспорт в CSV", callback_data="download_csv")]
    ]
    context.user_data["gmail_variants"] = text
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    data = context.user_data.get("gmail_variants", "")

    if action == "copy_gmail":
        await query.message.reply_text(data)
    elif action == "download_txt":
        await query.message.reply_document(document=InputFile(io.BytesIO(data.encode()), filename="gmail_variants.txt"))
    elif action == "download_csv":
        csv_data = data.replace("
", ",")
        await query.message.reply_document(document=InputFile(io.BytesIO(csv_data.encode()), filename="gmail_variants.csv"))

async def drive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи ID файла Google Диска, например: /drive 1aBcD...")
        return

    file_id = context.args[0]
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    keyboard = [
        [InlineKeyboardButton("Скопировать ссылку", callback_data="copy_drive")],
        [InlineKeyboardButton("Перейти", url=url)]
    ]
    context.user_data["drive_link"] = url
    await update.message.reply_text(f"🔗 Прямая ссылка:
{url}", reply_markup=InlineKeyboardMarkup(keyboard))

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    image_bytes = await photo.download_as_bytearray()

    image_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)

    if data:
        keyboard = [
            [InlineKeyboardButton("Скопировать", callback_data="copy_qr")],
            [InlineKeyboardButton("Перейти", url=data)]
        ]
        context.user_data["qr_data"] = data
        await update.message.reply_text(f"QR код: {data}", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("QR код не найден.")

async def handle_qr_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = context.user_data.get("qr_data", "")
    if query.data == "copy_qr":
        await query.message.reply_text(data)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gmail", gmail))
    app.add_handler(CommandHandler("drive", drive))
    app.add_handler(MessageHandler(filters.PHOTO, photo))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CallbackQueryHandler(handle_qr_button, pattern="copy_qr"))
    app.run_polling()

if __name__ == "__main__":
    main()
