import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers import start, echo
from bot.config import Config

def main():
    if not Config.TELEGRAM_BOT_TOKEN:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN environment variable is missing")

    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("🤖 Running locally with polling...")
    app.run_polling()

if __name__ == "__main__":
    main()