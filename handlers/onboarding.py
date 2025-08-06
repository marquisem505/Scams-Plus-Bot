# handlers/onboarding.py

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ChatMemberUpdated, InputFile, User
)
from telegram.ext import ContextTypes
from db import (
    create_user_if_not_exists, update_onboarding,
    get_user_rank, set_user_rank, get_onboarding_summary
)
from utils.constants import GROUP_ID, topic_name_to_id, rank_access_topics, ADMIN_ID
from handlers.auth import logged_in_admins, ADMIN_PASSWORD
import logging
import os

# --- Memory ---
onboarding_memory = {}

# --- Member Join (via ChatMemberHandler) ---
async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.chat_member or update.chat_member.chat.id != GROUP_ID:
        return

    member = update.chat_member.new_chat_member.user
    create_user_if_not_exists(member.id, member.username, member.first_name)
    if get_user_rank(member.id) is None:
        set_user_rank(member.id, "Lookout")
    logging.info(f"Assigned default rank 'Lookout' to user {member.id}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 Start Onboarding", callback_data="start_onboarding")],
        [InlineKeyboardButton("📚 Group Rules", url="https://t.me/ScamsClubRules")],
        [InlineKeyboardButton("❓ Need Help?", callback_data="help")]
    ])
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"👋 Welcome {member.mention_html()} to Scam’s Plus!\n\nPress a button below to get started 👇",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# --- NEW_CHAT_MEMBERS Fallback ---
async def new_chat_member_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 Start Onboarding", callback_data="start_onboarding")],
        [InlineKeyboardButton("📚 Group Rules", url="https://t.me/ScamsClubRules")],
        [InlineKeyboardButton("❓ Need Help?", callback_data="help")]
    ])

    for member in update.message.new_chat_members:
        if isinstance(member, User):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"👋 Welcome {member.mention_html()} to Scam’s Plus!\n"
                    "This ain’t your average chat. Everything here is structured, ranked, and protected.\n\n"
                    "Press a button below to get started 👇"
                ),
                reply_markup=keyboard,
                parse_mode="HTML"
            )

# --- /start Command ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("👋 DM me privately to access onboarding, rank tools, and more.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 Restart Onboarding", callback_data="start_onboarding")],
        [InlineKeyboardButton("🧠 Start Here Guide", url="https://t.me/c/2286707356/2458")],
        [InlineKeyboardButton("👤 My Rank", callback_data="check_rank")],
        [InlineKeyboardButton("📤 Request Promotion", callback_data="promoteme")]
    ])
    await update.message.reply_text(
        "👋 Welcome to Scam’s Plus.\n\nThis bot helps with onboarding, ranks, and navigating the group.\n\nUse the buttons below to get started 👇",
        reply_markup=keyboard
    )

# --- Handle Private Message (Admin Login) ---
async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = update.effective_user.id
    text = message.text.strip()

    if context.user_data.get("admin_authenticated"):
        await message.reply_text("✅ You're already logged in as admin. Use /admin to access the panel.")
        return

    if context.user_data.get("awaiting_admin_password"):
        from handlers.auth import logged_in_admins, ADMIN_PASSWORD
        if text == ADMIN_PASSWORD:
            logged_in_admins.add(user_id)
            context.user_data["admin_authenticated"] = True
            context.user_data["awaiting_admin_password"] = False
            await message.reply_text("🔓 Password correct. You’re now logged in as admin. Use /admin to access the panel.")
        else:
            await message.reply_text("❌ Incorrect password. Try again or type /logout to cancel.")
        return

    await message.reply_text("🔐 Please enter the admin password:")
    context.user_data["awaiting_admin_password"] = True

# --- View Logs (/logs) ---
async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not authorized to view logs.")
        return

    log_path = "scamsclub_bot.log"
    if not os.path.exists(log_path):
        await update.message.reply_text("⚠️ Log file not found.")
        return

    try:
        with open(log_path, "rb") as log_file:
            await update.message.reply_document(
                document=InputFile(log_file, filename="scamsclub_bot.log"),
                caption="📄 Here is the latest log file:"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending log file: {str(e)}")

# --- Topic Guard Enforcement ---
async def topic_guard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.message_thread_id:
        return

    thread_id = message.message_thread_id
    user_id = message.from_user.id
    rank = get_user_rank(user_id) or "Lookout"
    allowed_topics = rank_access_topics.get(rank, [])

    if thread_id not in allowed_topics:
        try:
            await message.reply_text(
                "🚫 You don’t have permission to post in this topic yet based on your current rank.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Request Promotion", callback_data="promoteme")]
                ])
            )
            await context.bot.send_message(
                chat_id=user_id,
                text="⚠️ You posted in a restricted topic.\n\nEach topic has rank-based access. Complete onboarding and request a promotion to gain more access."
            )
            await message.delete()
        except Exception as e:
            logging.warning(f"❌ Failed to enforce topic guard: {e}")

# --- Forward Replies to Promotion Prompt ---
async def reply_forwarder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.reply_to_message:
        original_text = update.message.reply_to_message.text.lower()
        if "rank promotion" in original_text or "request a rank promotion" in original_text:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        f"📨 *Promotion Request Reply*\n"
                        f"From: @{update.effective_user.username or update.effective_user.id}\n\n"
                        f"{update.message.text}"
                    ),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logging.warning(f"❌ Failed to forward promotion reply: {e}")