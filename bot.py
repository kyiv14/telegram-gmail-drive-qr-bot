
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет! Используй команды:
"
        "/gmail your_email@gmail.com - для генерации вариантов gmail"
    )

async def handle_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        email = update.message.text.strip()
        if email.endswith("@gmail.com") or email.endswith("@googlemail.com"):
            prefix = email.split("@")[0].replace(".", "")
            variants = [
                f"{prefix[:i]}.{prefix[i:]}@gmail.com" for i in range(1, len(prefix))
            ] + [
                f"{prefix[:i]}.{prefix[i:]}@googlemail.com" for i in range(1, len(prefix))
            ]
            reply = "
".join(set(variants[:20])) or "Варианты не найдены."
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text("Это не Gmail или Googlemail адрес.")

def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gmail))
    app.run_polling()

if __name__ == "__main__":
    main()
