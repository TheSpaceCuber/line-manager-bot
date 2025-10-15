#handlers.py
from telegram import Update, Poll as TelegramPoll
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from datetime import datetime
from collections import defaultdict
import logging

from bot.database import (
    save_poll,
    get_current_week_poll,
    save_votes,
    remove_user_votes,
    get_poll_votes,
    get_poll_by_id,
    get_week_bounds,
    SGT
)

logger = logging.getLogger(__name__)

# Poll options
POLL_OPTIONS = ["Thu", "Sat", "Cmi"]
POLL_QUESTION = "Weekly training"


async def poll_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /poll command. Creates a new poll for the week or provides
    a link to the existing poll if one already exists for the current week.
    """
    try:
        chat_id = update.effective_chat.id
        
        # Check if a poll already exists for this week
        existing_poll = await get_current_week_poll(chat_id)
        
        if existing_poll:
            # Poll already exists for this week, send a link to it
            week_start, week_end = await get_week_bounds()
            week_range = f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"
            
            # Create a link to the existing poll message
            # Format: https://t.me/c/<chat_id_without_-100>/<message_id>
            chat_id_str = str(chat_id)
            if chat_id_str.startswith('-100'):
                chat_id_short = chat_id_str[4:]  # Remove -100 prefix
                message_link = f"https://t.me/c/{chat_id_short}/{existing_poll.message_id}"
            else:
                # For non-supergroup chats, just mention the message
                message_link = f"message #{existing_poll.message_id}"
            
            await update.message.reply_text(
                f"📊 Poll already created for this week ({week_range}).\n\n"
                f"Jump to poll: {message_link}",
                disable_web_page_preview=True
            )
            return
        
        # No poll exists, create a new one
        message = await update.message.reply_poll(
            question=POLL_QUESTION,
            options=POLL_OPTIONS,
            is_anonymous=False,
            allows_multiple_answers=True
        )
        
        # Save the poll to database
        poll_id = message.poll.id
        message_id = message.message_id
        await save_poll(poll_id, chat_id, message_id)
        
        logger.info(f"Created new poll {poll_id} in chat {chat_id}")
        
    except TelegramError as e:
        logger.error(f"Telegram error in poll_command: {e}")
        await update.message.reply_text(
            "❌ Sorry, there was an error creating the poll. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error in poll_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An unexpected error occurred. Please try again later."
        )


async def lines_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /lines command. Shows all votes for the current week's poll
    grouped by option.
    """
    try:
        chat_id = update.effective_chat.id
        
        # Get the current week's poll
        current_poll = await get_current_week_poll(chat_id)
        
        if not current_poll:
            await update.message.reply_text(
                "ℹ️ No poll has been created for this week yet.\n"
                "Use /poll to create one!"
            )
            return
        
        # Get all votes for this poll
        votes = await get_poll_votes(current_poll.id)
        
        if not votes:
            week_start, week_end = await get_week_bounds()
            week_range = f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"
            await update.message.reply_text(
                f"📊 This Week's Lines ({week_range})\n\n"
                "No votes yet! Be the first to vote! 🎯"
            )
            return
        
        # Group votes by option
        votes_by_option = defaultdict(list)
        for vote in votes:
            votes_by_option[vote.option_text].append(vote)
        
        # Format the output
        week_start, week_end = await get_week_bounds()
        week_range = f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"
        
        output_lines = [f"📊 This Week's Lines ({week_range})\n"]
        
        # Iterate through options in the order they appear in POLL_OPTIONS
        for option in POLL_OPTIONS:
            if option in votes_by_option:
                output_lines.append(f"\n{option}:")
                for vote in votes_by_option[option]:
                    # Format: @username (First Name) or just First Name if no username
                    if vote.user_username:
                        user_display = f"@{vote.user_username} ({vote.user_first_name})"
                    else:
                        user_display = vote.user_first_name
                    output_lines.append(f"• {user_display}")
        
        output_text = "\n".join(output_lines)
        await update.message.reply_text(output_text)
        
        logger.info(f"Displayed lines for poll {current_poll.id} in chat {chat_id}")
        
    except TelegramError as e:
        logger.error(f"Telegram error in lines_command: {e}")
        await update.message.reply_text(
            "❌ Sorry, there was an error fetching the poll results. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error in lines_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An unexpected error occurred. Please try again later."
        )


async def poll_answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle poll answers. Saves or removes votes based on user's selection.
    """
    try:
        poll_answer = update.poll_answer
        poll_id = poll_answer.poll_id
        user = poll_answer.user
        option_ids = poll_answer.option_ids
        
        # Check if this poll exists in our database
        poll = await get_poll_by_id(poll_id)
        if not poll:
            logger.warning(f"Received answer for unknown poll {poll_id}")
            return
        
        # If option_ids is empty, user retracted their vote
        if not option_ids:
            deleted_count = await remove_user_votes(poll_id, user.id)
            logger.info(f"User {user.id} retracted {deleted_count} votes from poll {poll_id}")
            return
        
        # Convert option IDs to option texts
        option_texts = [POLL_OPTIONS[option_id] for option_id in option_ids]
        
        # Save the votes (this automatically removes old votes first)
        await save_votes(
            poll_id=poll_id,
            user_id=user.id,
            user_first_name=user.first_name,
            user_username=user.username,
            option_texts=option_texts
        )
        
        logger.info(
            f"User {user.id} ({user.first_name}) voted {option_texts} on poll {poll_id}"
        )
        
    except Exception as e:
        logger.error(f"Error in poll_answer_handler: {e}", exc_info=True)
        # We can't easily send error messages here since poll answers don't have
        # a direct message to reply to. Just log the error.