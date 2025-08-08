from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.admin import admin_panel, logout_command
from handlers.rank import promoteme, myrank
from utils.helpers import delete_old_messages, store_message_id

# --- Menu Handler (reply buttons) ---
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only handle private chat menu; ignore groups
    if update.effective_chat.type != "private":
        return

    # Don’t interfere with admin login flow
    if context.user_data.get("admin_authenticated") or context.user_data.get("awaiting_admin_password"):
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text == "📊 Admin Panel":
        await admin_panel(update, context)

    elif text == "📤 Request Promotion":
        await promoteme(update, context)

    elif text == "👤 My Rank":
        await myrank(update, context)

    elif text == "🚪 Logout Admin":
        await logout_command(update, context)

    elif text == "🧠 Start Here Guide":
        await update.message.reply_text("Start here: https://t.me/c/2286707356/2458")

    elif text == "📘 Restart Onboarding":
        # You can hook into onboarding logic here
        await update.message.reply_text("Onboarding restart coming soon. Use /start for now.")

# --- /start command ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ("group", "supergroup"):
        await update.message.reply_text(
            "👋 DM me privately to access onboarding, rank tools, and more."
        )
        return

    chat_id = update.effective_chat.id
    await delete_old_messages(context, chat_id, keep_last=1)

    reply_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("📘 Restart Onboarding"), KeyboardButton("🧠 Start Here Guide")],
            [KeyboardButton("👤 My Rank"), KeyboardButton("📤 Request Promotion")],
            [KeyboardButton("📊 Admin Panel"), KeyboardButton("🚪 Logout Admin")],
        ],
        resize_keyboard=True
    )

    msg = await update.message.reply_text(
        "👋 Welcome to Scam’s Plus.\n\n"
        "This bot helps with onboarding, ranks, and navigating the group.\n\n"
        "Use the buttons below to get started 👇",
        reply_markup=reply_kb
    )

    store_message_id(context, chat_id, msg.message_id)