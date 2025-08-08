import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ContextTypes

from db import (
    get_user_rank,
    set_user_rank,
    get_user_id_by_username
)

from utils.constants import (
    ADMIN_ID,
    GROUP_ID,
    rank_access_topics
)

from utils.helpers import increment_violation, delete_old_messages, store_message_id

# --- Topic Guard ---
async def topic_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != GROUP_ID or update.message.message_thread_id is None:
        return

    uid = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    topic_id = update.message.message_thread_id
    user_rank = get_user_rank(uid) or "Lookout"
    allowed_topics = rank_access_topics.get(user_rank, [])

    if topic_id not in allowed_topics:
        increment_violation(uid)

        try:
            await update.message.delete()
        except Exception as e:
            logging.warning(f"❌ Couldn't delete message from @{username}: {e}")

        try:
            warn_msg = await context.bot.send_message(
                chat_id=GROUP_ID,
                message_thread_id=topic_id,
                text=f"⚠️ @{username}, you're not allowed to post in this topic at your current rank ({user_rank}).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Request Promotion", callback_data="promoteme")]
                ])
            )
            store_message_id(GROUP_ID, warn_msg.message_id)
        except Exception as e:
            logging.warning(f"⚠️ Failed to warn user in group thread: {e}")

        try:
            dm_msg = await context.bot.send_message(
                chat_id=uid,
                text=(
                    f"🚫 You tried posting in a restricted topic (ID: `{topic_id}`).\n"
                    f"Your current rank is: *{user_rank}*\n\n"
                    f"Use /promoteme in the group to request a rank promotion if needed."
                ),
                parse_mode="Markdown"
            )
            store_message_id(uid, dm_msg.message_id)
        except Exception as e:
            logging.warning(f"❌ Failed to DM user @{username}: {e}")

        if violation_counts[uid] >= 3:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=GROUP_ID,
                    user_id=uid,
                    permissions=ChatPermissions(can_send_messages=False)
                )
                muted_msg = await context.bot.send_message(
                    chat_id=uid,
                    text="🔇 You’ve been muted for repeated violations. Contact an admin to appeal."
                )
                store_message_id(uid, muted_msg.message_id)
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
    store_message_id(update.effective_chat.id, msg.message_id)

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
        return store_message_id(update.effective_chat.id, msg.message_id)

    if len(context.args) < 2:
        msg = await update.message.reply_text("Usage: /assignrank <@username> <Rank>")
        return store_message_id(update.effective_chat.id, msg.message_id)

    username = context.args[0].lstrip('@')
    rank = context.args[1].capitalize()
    uid = get_user_id_by_username(username)

    if uid:
        set_user_rank(uid, rank)
        msg = await update.message.reply_text(f"✅ Assigned rank `{rank}` to @{username}.", parse_mode="Markdown")
    else:
        msg = await update.message.reply_text(f"⚠️ User @{username} not found in database.")

    store_message_id(update.effective_chat.id, msg.message_id)

# --- Demote Rank ---
async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_old_messages(context, update.effective_chat.id)

    if update.effective_user.id != ADMIN_ID:
        msg = await update.message.reply_text("❌ Not authorized.")
        return store_message_id(update.effective_chat.id, msg.message_id)

    if len(context.args) < 1:
        msg = await update.message.reply_text("Usage: /demote <@username>")
        return store_message_id(update.effective_chat.id, msg.message_id)

    username = context.args[0].lstrip('@')
    uid = get_user_id_by_username(username)

    if uid:
        set_user_rank(uid, "Lookout")
        msg = await update.message.reply_text(f"⚠️ @{username} was demoted to `Lookout`.", parse_mode="Markdown")
    else:
        msg = await update.message.reply_text(f"⚠️ User @{username} not found in database.")

    store_message_id(update.effective_chat.id, msg.message_id)

# --- My Rank ---
async def myrank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_old_messages(context, update.effective_chat.id)

    uid = update.effective_user.id
    rank = get_user_rank(uid) or "❌ Unranked"
    msg = await update.message.reply_text(f"🏷 Your current rank: `{rank}`", parse_mode="Markdown")

    store_message_id(update.effective_chat.id, msg.message_id)