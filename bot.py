import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import re
import csv
import io
import numpy as np
import cv2
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Используй команды:
"
        "/gmail <email> - генерировать Gmail-варианты
"
        "/drive <ссылка> - получить прямую ссылку
"
        "или отправь фото с QR-кодом"
    )

def generate_gmail_variants(email: str):
    if '@' not in email:
        return []
    name, domain = email.split('@')
    variants = set()
    for i in range(1, 1 << (len(name)-1)):
        chars = list(name)
        for j in range(len(name)-1):
            if i & (1 << j):
                chars[j] += '.'
        variant = ''.join(chars).replace('..', '.')
        variants.add(variant + '@gmail.com')
        variants.add(variant + '@googlemail.com')
    return sorted(variants)

async def gmail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: /gmail example@gmail.com")
        return
    email = context.args[0]
    variants = generate_gmail_variants(email)
    if not variants:
        await update.message.reply_text("Неверный формат Gmail.")
        return
    text = '\n'.join(variants)
    context.user_data['gmail_variants'] = variants
    buttons = [
        [InlineKeyboardButton("Скопировать всё", switch_inline_query=text)],
        [InlineKeyboardButton("Скачать .txt", callback_data='download_txt')],
        [InlineKeyboardButton("Экспорт в CSV", callback_data='download_csv')]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

async def drive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: /drive https://drive.google.com/file/d/ID/view")
        return
    url = context.args[0]
    match = re.search(r'/d/([\w-]+)', url)
    if not match:
        await update.message.reply_text("Не удалось извлечь ID.")
        return
    file_id = match.group(1)
    direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
    buttons = [
        [InlineKeyboardButton("Скопировать", switch_inline_query=direct_link)],
        [InlineKeyboardButton("Перейти", url=direct_link)]
    ]
    await update.message.reply_text(direct_link, reply_markup=InlineKeyboardMarkup(buttons))

def decode_qr(image: Image.Image):
    np_img = np.array(image.convert('RGB'))
    np_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(np_img)
    return data

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    path = await file.download_to_drive()
    image = Image.open(path)
    result = decode_qr(image)
    if result:
        buttons = [
            [InlineKeyboardButton("Скопировать", switch_inline_query=result)],
            [InlineKeyboardButton("Перейти", url=result)]
        ]
        await update.message.reply_text(result, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.message.reply_text("QR-код не найден.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    variants = context.user_data.get('gmail_variants', [])
    if query.data == 'download_txt':
        file = io.BytesIO('\n'.join(variants).encode())
        file.name = "gmail_variants.txt"
        await query.message.reply_document(document=InputFile(file))
    elif query.data == 'download_csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Email"])
        for v in variants:
            writer.writerow([v])
        file = io.BytesIO(output.getvalue().encode())
        file.name = "gmail_variants.csv"
        await query.message.reply_document(document=InputFile(file))

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gmail", gmail_command))
    app.add_handler(CommandHandler("drive", drive_command))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
