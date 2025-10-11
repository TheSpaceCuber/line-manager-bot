import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers import start, echo
from bot.config import Config
import asyncio

if not Config.TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is missing")

telegram_app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

asyncio.get_event_loop().run_until_complete(telegram_app.initialize())

app = FastAPI()

logging.basicConfig(level=logging.INFO)

@app.post("/api/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print("Received webhook data:", data)  # Logs to Vercel console
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"ok": True}
    except Exception as e:
        # Log the full exception
        import traceback
        tb = traceback.format_exc()
        print("Webhook error:", tb)
        return {"ok": False, "error": str(e)}

@app.get("/")
async def healthcheck():
    """Health check endpoint."""
    return {"status": "ok"}
