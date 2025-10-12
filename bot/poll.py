from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database import get_db, TrainingSession, Attendance
from sqlalchemy.orm import Session
import logging
# Define poll options (could be moved to DB if dynamic)
POLL_OPTIONS = [
    "Thu 730pm @ YCK",
    "Sat 945am",
    "Cmi",
]

def format_poll_message(session_ids: dict, db: Session) -> str:
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
            cmi_attendance = db.query(Attendance).filter(
                Attendance.session_id.in_([session_ids["Thu"], session_ids["Sat"]]),
                Attendance.present == False,
                Attendance.source == "Cmi"
            ).all()
            # Count unique telegram_handle
            unique_handles = set(a.telegram_handle for a in cmi_attendance)
            count = len(unique_handles)
            bar = "█" * count if count > 0 else "░"
            msg += f"• *{option}*: {bar} `{count}`\n"
            if count > 0:
                formatted_voters = ", ".join(sorted(unique_handles))
                msg += f"  👥 {formatted_voters}\n"
            msg += "\n"
            continue
        else:
            voters = []

        count = len(voters)
        bar = "█" * count if count > 0 else "░"
        msg += f"• *{option}*: {bar} `{count}`\n"
        if count > 0:
            names = sorted(v.telegram_handle for v in voters)
            formatted_voters = ", ".join(names)
            msg += f"  👥 {formatted_voters}\n"
        msg += "\n"
    return msg

def build_poll_keyboard(session_ids: dict, db: Session) -> InlineKeyboardMarkup:
    keyboard = []
    for option in POLL_OPTIONS:
        if option == "Thu 730pm @ YCK":
            session_id = session_ids["Thu"]
            count = db.query(Attendance).filter_by(session_id=session_id, present=True, source=option).count()
        elif option == "Sat 945am":
            session_id = session_ids["Sat"]
            count = db.query(Attendance).filter_by(session_id=session_id, present=True, source=option).count()
        elif option == "Cmi":
            cmi_attendance = db.query(Attendance).filter(
                Attendance.session_id.in_([session_ids["Thu"], session_ids["Sat"]]),
                Attendance.present == False,
                Attendance.source == "Cmi"
            ).all()
            unique_handles = set(a.telegram_handle for a in cmi_attendance)
            count = len(unique_handles)
        else:
            count = 0

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



def toggle_vote(user_info: dict, selected_option: str, session_ids: dict, db: Session):
    user_handle = user_info["name"]

    if selected_option == "Cmi":
        # Remove any previous Cmi attendance for both sessions
        for sid in session_ids.values():
            existing = db.query(Attendance).filter_by(
                session_id=sid,
                telegram_handle=user_handle,
                present=False,
                source="Cmi"
            ).first()
            if existing:
                db.delete(existing)
                db.commit()
                return ("You removed your Cmi vote.", None)
        # Add Cmi attendance for both sessions
        for sid in session_ids.values():
            attendance = Attendance(
                session_id=sid,
                telegram_handle=user_handle,
                present=False,
                source="Cmi",
            )
            db.add(attendance)
        db.commit()
        log_current_attendance(session_ids, db)
        return ("You marked yourself as unable to attend.", None)

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
        log_current_attendance(session_ids, db)
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
        log_current_attendance(session_ids, db)
        return (f"You voted for {selected_option}!", None)


def log_current_attendance(session_ids: dict, db: Session):
    logging.info("Current attendance status:")
    for label, session_id in session_ids.items():
        present = db.query(Attendance).filter_by(session_id=session_id, present=True).all()
        absent = db.query(Attendance).filter_by(session_id=session_id, present=False, source="Cmi").all()
        present_names = [a.telegram_handle for a in present]
        absent_names = [a.telegram_handle for a in absent]
        logging.info(f"{label}: Present: {present_names if present_names else 'None'} | Cmi: {absent_names if absent_names else 'None'}")