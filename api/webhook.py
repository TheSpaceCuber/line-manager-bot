import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers import start, echo
from bot.config import Config

if not Config.TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is missing")

telegram_app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

app = FastAPI()

logging.basicConfig(level=logging.INFO)

@app.post("/api/webhook")
async def webhook(request: Request):
    """Receives Telegram updates via webhook."""
    data = await request.json()
    logging.info(f"Received webhook data: {data}")
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    logging.info("Processed update successfully.")
    return {"ok": True}

@app.get("/")
async def healthcheck():
    """Health check endpoint."""
    return {"status": "ok"}
