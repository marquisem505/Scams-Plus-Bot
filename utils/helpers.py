# utils/helpers.py

from typing import List
from telegram.ext import ContextTypes

# --- In-memory state ---
onboarding_memory = {}    # user_id -> dict (if you ever use it)
user_ranks = {}           # user_id -> rank (legacy, db is source of truth)
violation_counts = {}     # user_id -> int
logged_in_admins = set()  # admin login tracker (DM auth)

def increment_violation(user_id: int) -> int:
    """Increment and return a user's violation count."""
    violation_counts[user_id] = violation_counts.get(user_id, 0) + 1
    return violation_counts[user_id]

def store_message_id(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int) -> None:
    """
    Track a bot-sent message ID for a given chat so we can clean it up later.
    Uses application.chat_data[chat_id]["old_messages"] as the bucket.
    """
    if not hasattr(context, "application") or context.application is None:
        return  # safety

    chat_bucket = context.application.chat_data.setdefault(chat_id, {})
    lst: List[int] = chat_bucket.setdefault("old_messages", [])
    lst.append(message_id)

async def delete_old_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int, keep_last: int = 0) -> None:
    """
    Delete previously tracked messages in this chat.
    If keep_last > 0, keep the most recent N tracked messages (do not delete them),
    and only delete older ones.
    """
    if not hasattr(context, "application") or context.application is None:
        return  # safety

    chat_bucket = context.application.chat_data.get(chat_id, {})
    ids: List[int] = chat_bucket.get("old_messages", [])
    if not ids:
        return

    # Determine which IDs to delete
    if keep_last > 0 and len(ids) > keep_last:
        to_delete = ids[:-keep_last]
        to_keep = ids[-keep_last:]
    else:
        to_delete = ids
        to_keep = []

    # Try to delete each message; ignore errors (already deleted, too old, no rights, etc.)
    for mid in to_delete:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=mid)
        except Exception:
            pass

    # Save back the kept IDs
    chat_bucket["old_messages"] = to_keep