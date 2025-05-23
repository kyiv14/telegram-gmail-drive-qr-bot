import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Используй команды:\n"
        "- /gmail — генерация Gmail-вариантов\n"
        "- /drive — преобразование ссылки Google Диска\n"
        "- /qr — распознавание QR-кода с картинки"
    )

def main():
    app = ApplicationBuilder().token("7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k").build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
