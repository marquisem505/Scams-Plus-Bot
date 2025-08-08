# utils/helpers.py

from typing import List
from telegram.ext import ContextTypes

# --- Memory ---
onboarding_memory = {}   # user_id -> dict
user_ranks = {}          # user_id -> rank
violation_counts = {}    # user_id -> int

# In-memory admin login tracker
logged_in_admins = set()

# Store per-user/chat tracked bot message IDs for cleanup
# We’ll stash IDs in context.user_data["old_messages"] (a list of ints)
# so this stays scoped to that user+chat in PTB.
user_messages = {}


def increment_violation(user_id: int) -> int:
    violation_counts[user_id] = violation_counts.get(user_id, 0) + 1
    return violation_counts[user_id]


def store_message_id(context: ContextTypes.DEFAULT_TYPE, msg_id: int) -> None:
    
    chat_bucket = context.application.chat_data.setdefault(chat_id, {})
    lst: List[int] = chat_bucket.setdefault("old_messages", [])
    lst.append(message_id)


async def delete_old_messages(context, chat_id: int) -> None:
    """
    Delete previously stored messages for this chat and clear the list.
    """
    chat_bucket = context.application.chat_data.get(chat_id, {})
    ids: List[int] = chat_bucket.get("old_messages", [])
    if not ids:
        return

    for mid in ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=mid)
        except Exception:
            # message may already be gone, too old, or insufficient rights—ignore
            pass

    chat_bucket["old_messages"] = []