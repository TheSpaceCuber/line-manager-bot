from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database import get_db, TrainingSession, Attendance, Absentee
from sqlalchemy.orm import Session
import logging
# Define poll options (could be moved to DB if dynamic)
POLL_OPTIONS = [
    "Thu 730pm @ YCK",
    "Sat 945am",
    "Cmi",
]

def format_poll_message(session_ids: dict, db: Session, poll_message_id: int) -> str:
    msg = "🏋️‍♂️ *Training Roll Call*\n\n"
    for option in POLL_OPTIONS:
        if option == "Thu 730pm @ YCK":
            session_id = session_ids["Thu"]
            voters = db.query(Attendance).filter_by(session_id=session_id, present=True, source=option).all()
        elif option == "Sat 945am":
            session_id = session_ids["Sat"]
            voters = db.query(Attendance).filter_by(session_id=session_id, present=True, source=option).all()
        elif option == "Cmi":
            # Get all Attendance records for Cmi for both sessions
            voters = db.query(Absentee).filter(Absentee.poll_message_id == poll_message_id).all()
        else:
            voters = []

        logging.info(f"Option '{option}' has voters: {voters}")
        count = len(voters)
        bar = "█" * count if count > 0 else "░"
        msg += f"• *{option}*: {bar} `{count}`\n"
        if count > 0:
            names = sorted(v.telegram_handle for v in voters)
            formatted_voters = ", ".join(names)
            msg += f"  👥 {formatted_voters}\n"
        msg += "\n"
    return msg

def build_poll_keyboard(session_ids: dict, db: Session, poll_message_id: int) -> InlineKeyboardMarkup:
    keyboard = []
    for option in POLL_OPTIONS:
        if option == "Thu 730pm @ YCK":
            session_id = session_ids["Thu"]
            count = db.query(Attendance).filter_by(session_id=session_id, present=True, source=option).count()
        elif option == "Sat 945am":
            session_id = session_ids["Sat"]
            count = db.query(Attendance).filter_by(session_id=session_id, present=True, source=option).count()
        elif option == "Cmi":
            count = db.query(Absentee).filter(Absentee.poll_message_id == poll_message_id).count()

        emoji = ""
        if "Thu" in option:
            emoji = "🕢"
        elif "Sat" in option:
            emoji = "☀️"
        elif "Cmi" in option:
            emoji = "❌"

        button_text = f"{emoji} {option} ({count})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=option)])

    return InlineKeyboardMarkup(keyboard)

def toggle_vote(user_info: dict, 
                selected_option: str, 
                session_ids: dict, 
                db: Session,
                poll_message_id: int):
    user_handle = user_info["name"]

    if selected_option == "Cmi":
        # Check if user is already marked as Cmi in the Absentees table
        try:
            existing = db.query(Absentee).filter(
                Absentee.telegram_handle == user_handle, 
                Absentee.poll_message_id == poll_message_id).one()
        except:
            # if no record found, .one() raises an exception
            # Add to Absentees table (marked as Cmi)
            db.add(Absentee(
                telegram_handle=user_handle,
                poll_message_id=poll_message_id
            ))
            db.commit()
            logging.info(f"Added {user_handle} to Absentees for poll {poll_message_id}")
            return ("You marked yourself as Cmi.", None)
        else:
            # record found, remove from Absentees table
            db.delete(existing)
            db.commit()
            log_current_attendance(session_ids, db, poll_message_id)
            logging.info(f"Removed {user_handle} from Absentees for poll {poll_message_id}")
            return ("You removed your Cmi mark.", None)

    # For Thu/Sat options
    if selected_option == "Thu 730pm @ YCK":
        session_id = session_ids["Thu"]
    elif selected_option == "Sat 945am":
        session_id = session_ids["Sat"]
    else:
        return ("Unknown option.", None)

    # Check if user is already present for this session and option
    existing = db.query(Attendance).filter_by(
        session_id=session_id,
        telegram_handle=user_handle,
        present=True,
        source=selected_option
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        log_current_attendance(session_ids, db, poll_message_id)
        return ("You removed your vote.", None)
    else:
        attendance = Attendance(
            session_id=session_id,
            telegram_handle=user_handle,
            present=True,
            source=selected_option,
        )
        db.add(attendance)
        db.commit()
        log_current_attendance(session_ids, db, poll_message_id)
        return (f"You voted for {selected_option}!", None)


def log_current_attendance(session_ids: dict, db: Session, poll_message_id: int):
    logging.info("Current attendance status:")
    for label, session_id in session_ids.items():
        present = db.query(Attendance).filter_by(session_id=session_id, present=True).all()
        present_names = [a.telegram_handle for a in present]
        cmi = db.query(Absentee).filter_by(poll_message_id=poll_message_id).all()
        logging.info(f"{label}: Present: {present_names if present_names else 'None'} | Cmi: {cmi if cmi else 'None'}")