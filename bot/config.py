import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    LOCAL_DEVELOPMENT_TELEGRAM_BOT_TOKEN = os.getenv("LOCAL_DEVELOPMENT_TELEGRAM_BOT_TOKEN")
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///local.db")

    # Google Sheets
    GOOGLE_SHEETS_URL = os.getenv("GOOGLE_SHEETS_URL")
    GOOGLE_SHEETS_PLAYERS_GID = os.getenv("GOOGLE_SHEETS_PLAYERS_GID")
    GOOGLE_SHEETS_GROUPS_GID = os.getenv("GOOGLE_SHEETS_GROUPS_GID")
    GOOGLE_SHEETS_CONFIG_GID = os.getenv("GOOGLE_SHEETS_CONFIG_GID")

    # Authorization
    AUTHORIZED_USERS = [
        u.strip().lower()
        for u in os.getenv("AUTHORIZED_USERS", "").split(",")
        if u.strip()
    ]

    # Chat IDs
    EXCO_CHAT_ID = os.getenv("EXCO_CHAT_ID")
    PLAYERS_CHAT_ID = os.getenv("PLAYERS_CHAT_ID")

