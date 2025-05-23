import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "👋 Привет! Используй команды:\n"
            "/start — начать\n"
            "/help — помощь"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Справка: этот бот помогает с ...")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Ошибка в обновлении:", exc_info=context.error)

def main():
    if not TOKEN or "YOUR_TELEGRAM_BOT_TOKEN" in TOKEN:
        raise ValueError("❌ Установите действительный Telegram TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_error_handler(error_handler)

    logging.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("Ошибка при запуске бота:")