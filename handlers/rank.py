# handlers/rank.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ContextTypes, CallbackQueryHandler

from db import (
    get_user_rank,
    set_user_rank,
    get_user_id_by_username,
)

from utils.constants import (
    ADMIN_ID,
    GROUP_ID,
    rank_access_topics,
)

from utils.helpers import (
    increment_violation,
    delete_old_messages,
    store_message_id,
    violation_counts,   # required for the >= 3 check
)

# --- Topic Guard ---
async def topic_guard(update, context):
    """
    Enforce topic access by rank in the main group.
    Triggers only for text (your bot.py already filters TEXT & ~COMMAND).
    """

    chat = update.effective_chat
    msg = update.effective_message  # safer alias
    user = update.effective_user

    # Hard guards: wrong chat, no message, no thread, bots/service msgs
    if not chat or chat.id != GROUP_ID:
        return
    if not msg or getattr(msg, "message_thread_id", None) is None:
        return
    if not user or getattr(user, "is_bot", False):
        return

    uid = user.id
    username = user.username or "Unknown"
    topic_id = msg.message_thread_id

    # Admin bypass
    if uid == ADMIN_ID:
        return

    # Get rank safely; default to Lookout on any issue
    try:
        user_rank = get_user_rank(uid) or "Lookout"
    except Exception as e:
        logging.warning(f"Rank lookup failed for {uid}: {e}")
        user_rank = "Lookout"

    allowed_topics = rank_access_topics.get(user_rank, [])
    if topic_id in allowed_topics:
        return  # allowed, do nothing

    # Record violation count
    count = increment_violation(uid)

    # Delete offending message (best-effort)
    try:
        await msg.delete()
    except Exception as e:
        logging.warning(f"❌ Couldn't delete message from @{username} in topic {topic_id}: {e}")

    # Public warning in the same topic (best-effort)
    try:
        warn = await context.bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=topic_id,
            text=(
                f"⚠️ @{username}, you're not allowed to post in this topic at your current rank "
                f"(*{user_rank}*). Use the button to request a promotion."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Request Promotion", callback_data="promoteme")]
            ]),
            parse_mode="Markdown"
        )
        store_message_id(context, GROUP_ID, warn.message_id)
    except Exception as e:
        logging.warning(f"⚠️ Failed to warn @{username} in topic {topic_id}: {e}")

    # Private DM (best-effort)
    try:
        dm = await context.bot.send_message(
            chat_id=uid,
            text=(
                f"🚫 You tried posting in a restricted topic (ID: `{topic_id}`).\n"
                f"Your current rank is: *{user_rank}*\n\n"
                f"Use /promoteme in the group to request a rank promotion if needed."
            ),
            parse_mode="Markdown"
        )
        store_message_id(context, uid, dm.message_id)
    except Exception as e:
        logging.warning(f"❌ Failed to DM user @{username}: {e}")

    # Optional auto-mute after 3+ violations (best-effort)
    try:
        if violation_counts.get(uid, 0) >= 3:
            await context.bot.restrict_chat_member(
                chat_id=GROUP_ID,
                user_id=uid,
                permissions=ChatPermissions(can_send_messages=False)
            )
            logging.info(f"🔇 Auto-muted user {uid} after {violation_counts.get(uid)} violations.")
    except Exception as e:
        logging.warning(f"🚫 Could not mute @{username}: {e}")

# --- Promote Me ---
async def promoteme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_old_messages(context, update.effective_chat.id)

    msg = await update.message.reply_text(
        "📤 To request a rank promotion, reply here with:\n\n"
        "• What you’ve done or contributed\n"
        "• Screenshots or drop results (if any)\n"
        "• Your desired rank\n\n"
        "✅ After replying, an admin will be notified."
    )
    store_message_id(context, update.effective_chat.id, msg.message_id)

# --- Promote Me Button Handler ---
async def promoteme_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Runs the same flow as the /promoteme command when a button is clicked."""
    query = update.callback_query
    await query.answer()
    # Call the existing promoteme command function
    await promoteme(update, context)

# --- Forward Promote Me Replies ---
async def reply_forwarder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and "rank promotion" in update.message.reply_to_message.text:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📬 Rank request from @{update.effective_user.username}:\n\n{update.message.text}"
        )

# --- Assign Rank ---
async def assign_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_old_messages(context, update.effective_chat.id)

    if update.effective_user.id != ADMIN_ID:
        msg = await update.message.reply_text("❌ Not authorized.")
        store_message_id(context, update.effective_chat.id, msg.message_id)
        return

    if len(context.args) < 2:
        msg = await update.message.reply_text("Usage: /assignrank <@username> <Rank>")
        store_message_id(context, update.effective_chat.id, msg.message_id)
        return

    username = context.args[0].lstrip('@')
    rank = context.args[1].capitalize()
    uid = get_user_id_by_username(username)

    if uid:
        set_user_rank(uid, rank)
        msg = await update.message.reply_text(
            f"✅ Assigned rank `{rank}` to @{username}.", parse_mode="Markdown"
        )
    else:
        msg = await update.message.reply_text(f"⚠️ User @{username} not found in database.")

    store_message_id(context, update.effective_chat.id, msg.message_id)

# --- Demote Rank ---
async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_old_messages(context, update.effective_chat.id)

    if update.effective_user.id != ADMIN_ID:
        msg = await update.message.reply_text("❌ Not authorized.")
        store_message_id(context, update.effective_chat.id, msg.message_id)
        return

    if len(context.args) < 1:
        msg = await update.message.reply_text("Usage: /demote <@username>")
        store_message_id(context, update.effective_chat.id, msg.message_id)
        return

    username = context.args[0].lstrip('@')
    uid = get_user_id_by_username(username)

    if uid:
        set_user_rank(uid, "Lookout")
        msg = await update.message.reply_text(
            f"⚠️ @{username} was demoted to `Lookout`.", parse_mode="Markdown"
        )
    else:
        msg = await update.message.reply_text(f"⚠️ User @{username} not found in database.")

    store_message_id(context, update.effective_chat.id, msg.message_id)

# --- My Rank ---
async def myrank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_old_messages(context, update.effective_chat.id)

    uid = update.effective_user.id
    rank = get_user_rank(uid) or "❌ Unranked"
    msg = await update.message.reply_text(f"🏷 Your current rank: `{rank}`", parse_mode="Markdown")

    store_message_id(context, update.effective_chat.id, msg.message_id)