
import logging
import re
import csv
from io import BytesIO
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import cv2
import numpy as np
from PIL import Image
import os

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📧 Генерация Gmail", callback_data="gmail")],
        [InlineKeyboardButton("🔗 Прямая ссылка Google Диска", callback_data="drive")],
        [InlineKeyboardButton("📷 Распознать QR-код", callback_data="qr")]
    ]
    await update.message.reply_text("Выберите функцию:", reply_markup=InlineKeyboardMarkup(keyboard))

def generate_gmail_variations(email):
    local, domain = email.split("@")
    pos = [i for i in range(1, len(local))]
    variations = set()
    for i in range(1 << len(pos)):
        parts, last = [], 0
        for j in range(len(pos)):
            if i & (1 << j):
                parts.append(local[last:pos[j]])
                last = pos[j]
        parts.append(local[last:])
        dotted = ".".join(parts)
        if not dotted.startswith(".") and not dotted.endswith(".") and ".." not in dotted:
            variations.add(dotted + "@gmail.com")
        if len(variations) >= 100:
            break
    return sorted(variations)

def extract_drive_link(link):
    match = re.search(r"(?:/d/|id=|/file/d/)([\w-]{10,})", link)
    if match:
        return "https://drive.google.com/uc?export=download&id=" + match[1]
    return None

def decode_qr_cv2(image: Image.Image):
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(cv_image)
    return data.strip() if data else None

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = query.data
    context.user_data["mode"] = mode
    if mode == "gmail":
        await query.message.reply_text("Введите Gmail адрес:")
    elif mode == "drive":
        await query.message.reply_text("Вставьте ссылку на Google Диск:")
    elif mode == "qr":
        await query.message.reply_text("Отправьте изображение с QR-кодом.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode", "")
    text = update.message.text.strip()
    if mode == "gmail":
        if not text.endswith("@gmail.com"):
            await update.message.reply_text("Некорректный Gmail адрес.")
            return
        emails = generate_gmail_variations(text)
        context.user_data["gmail_output"] = "\n".join(emails)
        csv_bytes = BytesIO()
        writer = csv.writer(csv_bytes)
        writer.writerow(["Email"])
        for email in emails:
            writer.writerow([email])
        csv_bytes.seek(0)
        context.user_data["gmail_csv"] = csv_bytes
        txt_bytes = BytesIO(context.user_data["gmail_output"].encode("utf-8"))
        txt_bytes.seek(0)
        context.user_data["gmail_txt"] = txt_bytes
        await update.message.reply_text(
            context.user_data["gmail_output"][:4000],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Скопировать всё", callback_data="copy_gmail")],
                [InlineKeyboardButton("📄 Скачать .txt", callback_data="txt_gmail")],
                [InlineKeyboardButton("📊 Экспорт в CSV", callback_data="csv_gmail")]
            ])
        )
    elif mode == "drive":
        link = extract_drive_link(text)
        if link:
            context.user_data["drive_link"] = link
            await update.message.reply_text(
                link,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Скопировать ссылку", callback_data="copy_drive")],
                    [InlineKeyboardButton("🌐 Перейти по ссылке", url=link)]
                ])
            )
        else:
            await update.message.reply_text("Не удалось извлечь ссылку.")
    else:
        await update.message.reply_text("Выберите режим с помощью /start.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode", "")
    if mode != "qr":
        return
    photo_file = await update.message.photo[-1].get_file()
    img_bytes = BytesIO()
    await photo_file.download_to_memory(out=img_bytes)
    img_bytes.seek(0)
    img = Image.open(img_bytes).convert("RGB")
    result = decode_qr_cv2(img)
    if result:
        context.user_data["qr_result"] = result
        buttons = [[InlineKeyboardButton("📋 Скопировать", callback_data="copy_qr")]]
        if result.startswith("http"):
            buttons.append([InlineKeyboardButton("🌐 Перейти", url=result)])
        await update.message.reply_text(result, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.message.reply_text("QR-код не распознан.")

async def result_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "copy_gmail":
        await query.message.reply_text(context.user_data.get("gmail_output", "Нет данных."))
    elif data == "txt_gmail":
        file = InputFile(context.user_data["gmail_txt"], filename="gmail_variations.txt")
        await query.message.reply_document(file)
    elif data == "csv_gmail":
        file = InputFile(context.user_data["gmail_csv"], filename="gmail_variations.csv")
        await query.message.reply_document(file)
    elif data == "copy_drive":
        await query.message.reply_text(context.user_data.get("drive_link", "Нет ссылки."))
    elif data == "copy_qr":
        await query.message.reply_text(context.user_data.get("qr_result", "Нет результата."))

if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN_HERE")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(gmail|drive|qr)$"))
    app.add_handler(CallbackQueryHandler(result_button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    async def set_webhook():
        await app.bot.set_webhook(url="{}/webhook/{}".format("https://myallapps.onrender.com", TOKEN))

    import asyncio
    asyncio.run(set_webhook())

    print("Webhook установлен")
    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_path="/webhook/{}".format(TOKEN),
        webhook_url="{}/webhook/{}".format("https://myallapps.onrender.com", TOKEN)
    )
