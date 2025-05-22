
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import numpy as np
import cv2
from PIL import Image
import io
import httpx

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "https://your-app-name.onrender.com").rstrip("/")

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь Gmail, ссылку Google Drive или QR-фото.")

# Обработка текста
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "@gmail.com" in text:
        await update.message.reply_text(f"✉️ Gmail: {text}")
    elif "drive.google.com" in text:
        file_id = extract_drive_id(text)
        if file_id:
            link = f"https://drive.google.com/uc?export=download&id={file_id}"
            await update.message.reply_text(f"🔗 Прямая ссылка:
{link}")
        else:
            await update.message.reply_text("⚠️ Не удалось распознать ссылку.")
    else:
        await update.message.reply_text("🤔 Отправь Gmail или ссылку Google Drive.")

# QR через фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    f = await file.download_as_bytearray()
    img = Image.open(io.BytesIO(f)).convert("RGB")
    img_np = np.array(img)
    img_gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(img_gray)
    if data:
        await update.message.reply_text(f"📷 Распознанный QR:
{data}")
    else:
        await update.message.reply_text("🚫 Не удалось распознать QR-код.")

def extract_drive_id(url: str) -> str:
    import re
    match = re.search(r"(?:/d/|id=|/file/d/)([a-zA-Z0-9_-]{10,})", url)
    return match.group(1) if match else None

# Запуск
if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    async def set_webhook():
        async with httpx.AsyncClient() as client:
            url = f"{BASE_URL}/{BOT_TOKEN}"
            r = await client.post(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", data={"url": url})
            if r.status_code == 200:
                print("Webhook установлен")
            else:
                print("Ошибка установки webhook:", r.text)

    import asyncio
    asyncio.run(set_webhook())

    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        url_path=BOT_TOKEN,
        webhook_url=f"{BASE_URL}/{BOT_TOKEN}"
    )
