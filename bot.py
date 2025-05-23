
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👋 Привет! Используй команды:
/email - генератор Gmail
/link - Google Drive
/qr - QR из картинки")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
