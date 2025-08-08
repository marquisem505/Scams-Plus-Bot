# utils/helpers.py

from typing import List, Optional
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
    """
    Track a message ID so delete_old_messages can remove it later.
    IMPORTANT: pass CONTEXT here, not chat_id.
    """
    lst: List[int] = context.user_data.get("old_messages", [])
    lst.append(msg_id)
    context.user_data["old_messages"] = lst


async def delete_old_messages(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    keep_last: int = 0
) -> None:
    """
    Delete previously tracked bot messages for this user/chat.
    - keep_last: preserve the most recent N tracked messages (default 0 = delete all)
    """
    old_ids: List[int] = context.user_data.get("old_messages", [])
    if not old_ids:
        return

    # If we should preserve the newest N messages, slice accordingly
    to_delete = old_ids[:-keep_last] if keep_last > 0 else old_ids[:]

    for msg_id in to_delete:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            # message may already be deleted or too old; ignore
            pass

    # If keeping some, retain them in the list; else clear all
    if keep_last > 0:
        context.user_data["old_messages"] = old_ids[-keep_last:]
    else:
        context.user_data["old_messages"] = []