import csv
import datetime
import io
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InputFile
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ApplicationHandlerStop

from utils.constants import ADMIN_ID, ADMIN_PASSWORD
from utils.helpers import (
    violation_counts,
    logged_in_admins,
    delete_old_messages,
    store_message_id,
)
from db import get_user_count_by_rank, get_all_users

# --- Admin Reply Keyboard ---
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("📊 View Stats"), KeyboardButton("📤 Export Users")],
        [KeyboardButton("📥 Import Users"), KeyboardButton("🧑‍💼 Assign Rank")],
        [KeyboardButton("📨 Review Promotion Requests"), KeyboardButton("🧹 Reset Violations")],
        [KeyboardButton("⛔ Mute User"), KeyboardButton("🔄 Reload Configs")],
        [KeyboardButton("🚪 Logout")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    is_persistent=True,
)

# --- /admin entry point (works in group or DM) ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    if chat_type in ("group", "supergroup"):
        if user_id != ADMIN_ID:
            await update.message.reply_text("🚫 You are not authorized.")
            return
        await update.message.reply_text("✅ DM me privately to access the admin panel.")
        return

    if user_id in logged_in_admins or context.user_data.get("admin_authenticated"):
        sent = await send_admin_panel(update, context)
        store_message_id(context, update.effective_chat.id, sent.message_id)
    else:
        msg = await update.message.reply_text("🔐 Please enter the admin password:")
        context.user_data["awaiting_admin_password"] = True
        store_message_id(context, update.effective_chat.id, msg.message_id)

# --- Unified DM router for admin flows ---
async def handle_admin_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    if context.user_data.get("awaiting_admin_password"):
        await delete_old_messages(context, chat_id)

        if text == ADMIN_PASSWORD:
            context.user_data["admin_authenticated"] = True
            context.user_data["awaiting_admin_password"] = False
            logged_in_admins.add(user_id)

            ack = await update.message.reply_text("✅ Access granted.", reply_markup=admin_keyboard) 
            store_message_id(context, chat_id, ack.message_id)
            try:
                await update.message.delete()
            except Exception:
                pass

            panel_msg = await send_admin_panel(update, context)
            store_message_id(context, chat_id, panel_msg.message_id)
        else:
            warn = await update.message.reply_text("❌ Incorrect password. Try again.", reply_markup=admin_keyboard) 
            store_message_id(context, chat_id, warn.message_id)
            try:
                await update.message.delete()
            except Exception:
                pass

        raise ApplicationHandlerStop

    if user_id in logged_in_admins or context.user_data.get("admin_authenticated"):
        await handle_admin_text_selection(update, context)
        raise ApplicationHandlerStop

    if text.lower() in {"admin", "/admin"}:
        await admin_panel(update, context)
    else:
        await update.message.reply_text("🔒 Admin area. Use /admin to log in.")
    raise ApplicationHandlerStop

# --- Render admin panel ---
async def send_admin_panel(update, context):
    chat_id = update.effective_chat.id
    await delete_old_messages(context, chat_id)

    try:
        rank_breakdown = get_user_count_by_rank()
    except Exception as e:
        logging.exception("Failed to get rank breakdown")
        rank_breakdown = {}

    total_users = sum(rank_breakdown.values())
    total_violations = sum(violation_counts.values())
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary = (
        "<b>👑 Admin Panel Overview</b>\n\n"
        f"👥 Total Users: <code>{total_users}</code>\n"
        + ("\n".join([f"• {rank}: <code>{count}</code>" for rank, count in rank_breakdown.items()]) or "• No data yet")
        + f"\n\n🚫 Total Violations: <code>{total_violations}</code>"
        f"\n🕒 Last Boot: <code>{now}</code>"
    )

    return await context.bot.send_message(
        chat_id=chat_id,
        text=summary,
        parse_mode="HTML",
        reply_markup=admin_keyboard,
    )

# --- Handle panel selections ---
async def handle_admin_text_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in logged_in_admins and not context.user_data.get("admin_authenticated"):
        await update.message.reply_text("🔒 Session expired. Please /admin again.")
        return

    text = (update.message.text or "").strip()

    if text == "📊 View Stats":
        await update.message.reply_text("📊 Gathering stats... (coming soon)", reply_markup=admin_keyboard)

    elif text == "📤 Export Users":
        await admin_export_users(update, context)

    elif text == "📥 Import Users":
        await update.message.reply_text("📥 Importing users... (coming soon)", reply_markup=admin_keyboard)

    elif text == "🧑‍💼 Assign Rank":
        await update.message.reply_text("🧑‍💼 Use /assignrank <@username> <Rank>", reply_markup=admin_keyboard)

    elif text == "📨 Review Promotion Requests":
        await update.message.reply_text("📨 Reviewing promotion requests... (coming soon)", reply_markup=admin_keyboard)

    elif text == "🧹 Reset Violations":
        await update.message.reply_text("🧹 Resetting violations... (coming soon)", reply_markup=admin_keyboard)

    elif text == "⛔ Mute User":
        await update.message.reply_text("⛔ Muting users... (coming soon)", reply_markup=admin_keyboard)

    elif text == "🔄 Reload Configs":
        await update.message.reply_text("🔄 Reloading configs... (coming soon)", reply_markup=admin_keyboard)

    elif text == "🚪 Logout":
        await logout_command(update, context)

    else:
        await update.message.reply_text("❓ Not sure what you meant. Use the buttons or /admin.", reply_markup=admin_keyboard)

# --- Export to CSV in-memory ---
async def admin_export_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()

    if not users:
        await update.message.reply_text("⚠️ No users found to export.", reply_markup=admin_keyboard)
        return

    # Write CSV in memory
    text_buffer = io.StringIO()
    writer = csv.writer(text_buffer)
    writer.writerow(["ID", "Username", "First Name"])
    for user_id, username, first_name in users:
        writer.writerow([user_id, username or "", first_name or ""])
    text_buffer.seek(0)

    # Convert to bytes and send
    bytes_buffer = io.BytesIO(text_buffer.getvalue().encode("utf-8"))
    bytes_buffer.name = "exported_users.csv"

    await update.message.reply_document(
        document=InputFile(bytes_buffer, filename="exported_users.csv"),
        caption="📤 Exported user data.", reply_markup=admin_keyboard
    )

# --- Logout Admin ---
async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in logged_in_admins:
        logged_in_admins.remove(user_id)
        context.user_data["admin_authenticated"] = False
        await update.message.reply_text("🚪 You’ve been logged out of the admin panel.")
    else:
        await update.message.reply_text("⚠️ You're not logged in.")