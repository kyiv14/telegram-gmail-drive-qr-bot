
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import re

TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Используй команды:
"
        "/gmail — генерация точек
"
        "/gdrive — прямая ссылка
"
        "/qr — декодировать QR"
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
