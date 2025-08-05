# handlers/ranks.py

from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from db import set_user_rank, get_user_rank, get_user_id_by_username
from constants import ADMIN_ID, GROUP_ID
from handlers.auth import logged_in_admins

# --- Memory ---
user_ranks = {}          # user_id: rank

# --- Auto Rank Members On Join ---
async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member.new_chat_member
    if member.status == "member":
        user = member.user
        create_user_if_not_exists(user.id, user.username, user.first_name)
        set_user_rank(user.id, "Lookout")
        await context.bot.send_message(chat_id=user.id, text="Welcome to Scam's Plus! You've been assigned the rank: Lookout.")
# --- Assign Rank ---
async def assign_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /assignrank <@username> <Rank>")

    username = context.args[0].lstrip('@')
    rank = context.args[1].capitalize()
    uid = get_user_id_by_username(username)

    if uid:
        set_user_rank(uid, rank)
        await update.message.reply_text(f"✅ Assigned rank `{rank}` to @{username}.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ User @{username} not found in database.")
# --- My Rank ---
async def myrank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    rank = get_user_rank(uid) or "❌ Unranked"
    await update.message.reply_text(f"🏷 Your current rank: `{rank}`", parse_mode="Markdown")
# --- Promote Me ---
async def promoteme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📤 To request a rank promotion, reply here with:\n\n"
        "• What you’ve done or contributed\n"
        "• Screenshots or drop results (if any)\n"
        "• Your desired rank\n\n"
        "✅ After replying, an admin will be notified."
    )
# --- Forward Promote Me Replies ---
async def reply_forwarder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and "rank promotion" in update.message.reply_to_message.text:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📬 Rank request from @{update.effective_user.username}:\n\n{update.message.text}"
        )
# --- Demote Rank ---
async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")
    if len(context.args) < 1:
        return await update.message.reply_text("Usage: /demote <@username>")

    username = context.args[0].lstrip('@')
    uid = get_user_id_by_username(username)

    if uid:
        set_user_rank(uid, "Lookout")
        await update.message.reply_text(f"⚠️ @{username} was demoted to `Lookout`.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ User @{username} not found in database.")

# --- Check Rank --
    elif query.data == "check_rank":
        rank = get_user_rank(user_id) or "❌ Unranked"
        await query.message.reply_text(f"🏷 Your current rank: `{rank}`", parse_mode="Markdown")
async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member: ChatMemberUpdated = update.chat_member
    if member.chat.id != GROUP_ID:
        return
    await handle_join(member, context)

