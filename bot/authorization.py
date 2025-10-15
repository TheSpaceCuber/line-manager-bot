from functools import wraps
import logging
from bot.config import Config
from telegram import Update
from telegram.ext import ContextTypes

def authorized_only(func):
    """Decorator to restrict command access to authorized users."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user or not user.username:
            logging.warning("Command triggered by user with no username.")
            return  # Do nothing

        username = user.username.lower()
        if username not in Config.AUTHORIZED_USERS:
            logging.warning(f"Unauthorized access denied for {username}.")
            return  # Do nothing as requested

        return await func(update, context, *args, **kwargs)
    return wrapped
