# utils/helpers.py

from telegram import Update
from telegram.ext import ContextTypes
from utils.constants import ADMIN_ID

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def extract_username(text: str) -> str:
    """Strip @ and return just the username."""
    return text.lstrip("@").strip()

def format_markdown(text: str) -> str:
    """Escape text for Markdown V2 formatting."""
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text

async def send_dm(context: ContextTypes.DEFAULT_TYPE, user_id: int, message: str):
    try:
        await context.bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        print(f"⚠️ Failed to send DM to {user_id}: {e}")