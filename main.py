from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from bot.handlers import start, echo, poll, handle_poll_response
from bot.config import Config

def main():
    if not Config.LOCAL_DEVELOPMENT_TELEGRAM_BOT_TOKEN:
        raise ValueError("❌ LOCAL_DEVELOPMENT_TELEGRAM_BOT_TOKEN environment variable is missing")

    app = Application.builder().token(Config.LOCAL_DEVELOPMENT_TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.add_handler(CommandHandler("poll", poll))
    app.add_handler(CallbackQueryHandler(handle_poll_response))

    print("🤖 Running locally with polling...")
    app.run_polling()

if __name__ == "__main__":
    main()