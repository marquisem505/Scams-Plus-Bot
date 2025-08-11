# utils/helpers.py
from typing import List
from telegram.ext import ContextTypes

# --- Memory (in‑process) ---
onboarding_memory = {}      # user_id -> dict
user_ranks = {}             # user_id -> rank (if you still use it)
violation_counts = {}       # user_id -> int
logged_in_admins = set()    # track admin DM sessions

def increment_violation(user_id: int) -> int:
    violation_counts[user_id] = violation_counts.get(user_id, 0) + 1
    return violation_counts[user_id]

def store_message_id(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int) -> None:
    """
    Track a bot-sent message id in chat_data[chat_id]["old_messages"] so we can
    delete it later. chat_data is per-application and keyed by chat id.
    """
    chat_bucket = context.application.chat_data.setdefault(chat_id, {})
    lst: List[int] = chat_bucket.setdefault("old_messages", [])
    lst.append(message_id)

async def delete_old_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int, keep_last: int = 0) -> None:
    """
    Delete previously stored bot messages for this chat (except the last N if keep_last>0),
    then clear the list.
    """
    chat_bucket = context.application.chat_data.get(chat_id, {})
    lst: List[int] = chat_bucket.get("old_messages", [])
    if not lst:
        return

    to_delete = lst if keep_last <= 0 else lst[:-keep_last]
    for mid in to_delete:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=mid)
        except Exception:
            # message might be too old/already deleted/lacking rights — ignore
            pass

    if keep_last <= 0:
        chat_bucket["old_messages"] = []
    else:
        chat_bucket["old_messages"] = lst[-keep_last:]