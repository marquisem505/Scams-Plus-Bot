# handlers/topic_guard.py

from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from utils.constants import  GROUP_ID
from db import get_user_rank
import time

# --- Memory ---
violation_counts = {}  # optional: move to SQLite later

# --- Topic Guard ---
async def topic_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ignore if not from the main group or not in a thread
    if update.message.chat_id != GROUP_ID or update.message.message_thread_id is None:
        return

    uid = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    topic_id = update.message.message_thread_id
    user_rank = get_user_rank(uid) or "Lookout"  # Default to Lookout if unknown

    allowed_topics = rank_access_topics.get(user_rank, [])

    if topic_id not in allowed_topics:
        # Count and store violations
        increment_violation(uid)

        # Attempt to delete the message
        try:
            await update.message.delete()
        except Exception as e:
            logging.warning(f"❌ Couldn't delete message from @{username}: {e}")

        # Public warning in the thread
        try:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                message_thread_id=topic_id,
                text=f"⚠️ @{username}, you're not allowed to post in this topic at your current rank ({user_rank}).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Request Promotion", callback_data="promoteme")]
                ])
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
                    f"Use /promoteme in the group to request a rank promotion if needed."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.warning(f"❌ Failed to DM user @{username}: {e}")

        # Optional mute if too many violations
        if violation_counts[uid] >= 3:
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