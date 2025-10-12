from telegram import Update
from telegram.ext import ContextTypes
from bot.poll import format_poll_message, build_poll_keyboard, toggle_vote
from bot.database import get_db, get_or_create_sessions

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text( # type: ignore
        "Hey! 🥏 I'm your Ultimate Frisbee Bot.\nSend me a message and I’ll echo it back."
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text) # type: ignore

async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with next(get_db()) as db:
        session_ids = get_or_create_sessions(db)
        await update.message.reply_text(
            format_poll_message(session_ids, db),
            parse_mode="Markdown",
            reply_markup=build_poll_keyboard(session_ids, db),
        )
    
async def handle_poll_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_info = {
        "id": user.id,
        "username": user.username,
        "name": f"{user.first_name} {user.last_name or ''}".strip(),
    }
    selected_option = query.data
    with next(get_db()) as db:
        session_ids = get_or_create_sessions(db)
        action_msg, _ = toggle_vote(user_info, selected_option, session_ids, db)
        if selected_option != "Cmi":
            new_text = format_poll_message(session_ids, db)
            new_markup = build_poll_keyboard(session_ids, db)
            try:
                await query.edit_message_text(
                    text=new_text,
                    parse_mode="Markdown",
                    reply_markup=new_markup,
                )
            except Exception as e:
                if "Message is not modified" in str(e):
                    pass  # Ignore this error
                else:
                    raise
        await query.answer(action_msg, show_alert=True)
