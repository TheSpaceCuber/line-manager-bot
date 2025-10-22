import re
from telegram import Update
from telegram.ext import ContextTypes
from bot.spreadsheet import SpreadsheetLoader
from bot.splitter import Splitter

async def handle_lines_split_via_poll_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poll_text = update.message.text  # type: ignore

    # Split into sections by double newlines — each poll option is separated that way
    sections = poll_text.strip().split("\n\n")

    thu_names = []
    for section in sections:
        lines = section.strip().split("\n")
        if not lines:
            continue
        header = lines[0].lower()
        if "thu" in header:  # Check if the section title mentions "Thu"
            # Everything after the first line (the header) is assumed to be names
            thu_names = [name.strip() for name in lines[1:] if name.strip()]
            break  # Stop after finding the first "Thu" section

    print("Names under Thu option:", thu_names)
    
    splitter = Splitter()
    line_x, line_y, stats = splitter.split_lines(thu_names) # returns (line1, line2)
    
    msg = (
        "🏃 **Thursday Lines Split** 🏃\n\n"
        f"*Darks* ({len(line_x)} players):\n" +
        "\n".join(f"- {name}" for name in line_x) +
        "\n\n" +
        f"*Lights* ({len(line_y)} players):\n" +
        "\n".join(f"- {name}" for name in line_y) + "\n\n" + "\n".join(stats)
    )

    await update.message.reply_text(msg, parse_mode="Markdown")
