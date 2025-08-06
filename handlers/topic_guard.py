# --- handlers/topic_guard.py ---
# This module handles topic access control based on user ranks in a Telegram group.
# It restricts users from posting in topics they are not allowed to access based on their rank.
import logging
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.constants import GROUP_ID, rank_access_topics
from db import get_user_rank

# --- Memory for Violation Counts (temp: use SQLite for persistent tracking later) ---
violation_counts = {}

# --- Increment Violation Count ---
def increment_violation(user_id: int):
    if user_id not in violation_counts:
        violation_counts[user_id] = 1
    else:
        violation_counts[user_id] += 1

# --- Topic Guard Handler ---
async def topic_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # Defensive check
    if not message or message.chat_id != GROUP_ID or message.message_thread_id is None:
        return

    uid = update.effective_user
    username = update.effective_user or "Unknown"
    topic_id = message.message_thread_id 
    user_rank = get_user_rank(uid) or "Lookout"

    allowed_topics = rank_access_topics.get(user_rank, [])

    if topic_id not in allowed_topics:
        increment_violation(uid)

        # Try deleting the unauthorized message
        try:
            await message.delete()
        except Exception as e:
            logging.warning(f"❌ Couldn't delete message from @{username}: {e}")

        # Public warning
        try:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                message_thread_id=topic_id,
                text=f"⚠️ @{username}, you're not allowed to post in this topic at your current rank (*{user_rank}*).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Request Promotion", callback_data="promoteme")]
                ]),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.warning(f"⚠️ Failed to warn user in group thread: {e}")

        # Private DM
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=(
                    f"🚫 You tried posting in a restricted topic (ID: `{topic_id}`).\n"
                    f"Your current rank is: *{user_rank}*\n\n"
                    f"Use /promoteme in the group to request a rank promotion."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.warning(f"❌ Failed to DM user @{username}: {e}")

        # Auto-mute if 3+ violations
        if violation_counts.get(uid, 0) >= 3:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=GROUP_ID,
                    user_id=uid,
                    permissions=ChatPermissions(can_send_messages=False)
                )
                await context.bot.send_message(
                    chat_id=uid,
                    text="🔇 You’ve been muted for repeated violations. Contact an admin to appeal."
                )
            except Exception as e:
                logging.warning(f"🚫 Could not mute @{username}: {e}")