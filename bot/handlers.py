from telegram import Update
from telegram.ext import ContextTypes

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text) # type: ignore