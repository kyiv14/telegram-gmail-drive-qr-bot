import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import os
import io
import csv
import base64
import numpy as np
import cv2
from PIL import Image
import tempfile

logging.basicConfig(level=logging.INFO)
TOKEN = "7490249052:AAEaldElMOFFJwn9WIvuSR0bx6tFaebeR0k"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Используй команды:\n"
        "/gmail — сгенерировать варианты email\n"
        "/drive — сделать прямую ссылку\n"
        "/qr — распознать QR из картинки"
    )

async def gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📧 Введи свой адрес Gmail (без вариантов):")

async def drive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔗 Вставь ссылку на файл с Google Диска:")

async def qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📷 Отправь изображение с QR-кодом.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gmail", gmail))
    app.add_handler(CommandHandler("drive", drive))
    app.add_handler(CommandHandler("qr", qr))
    app.run_polling()

if __name__ == '__main__':
    main()