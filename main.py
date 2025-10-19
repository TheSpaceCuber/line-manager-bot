import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.config import Config
from bot.handlers import echo

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    if not Config.LOCAL_DEVELOPMENT_TELEGRAM_BOT_TOKEN:
        raise ValueError("❌ LOCAL_DEVELOPMENT_TELEGRAM_BOT_TOKEN environment variable is missing")
   
    # Create the Application
    application = Application.builder().token(Config.LOCAL_DEVELOPMENT_TELEGRAM_BOT_TOKEN).build()
   
    # Register handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

   
    # Start the bot
    logger.info('Bot started')
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()