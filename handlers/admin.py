# handlers/admin.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.constants import ADMIN_ID
from handlers.auth import logged_in_admins

# --- Admin Panel ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    # --- In group ---
    if chat_type in ["group", "supergroup"]:
        if user_id != ADMIN_ID:
            await update.message.reply_text("🚫 You are not authorized.")
            return
        await update.message.reply_text("✅ DM me privately to access the admin panel.")
        return
    
    # --- In private chat ---
    if user_id in logged_in_admins or context.user_data.get("admin_authenticated"):
        await send_admin_panel(update)
    else:
        await update.message.reply_text("🔐 Please enter the admin password:")
        context.user_data["awaiting_admin_password"] = True

# --- Admin Buttons ---
async def send_admin_panel(update: Update):
    keyboard = [
        [InlineKeyboardButton("📊 View Stats", callback_data="admin_view_stats")],
        [InlineKeyboardButton("📤 Export Users", callback_data="admin_export_users")],
        [InlineKeyboardButton("📥 Import Users", callback_data="admin_import_users")],
        [InlineKeyboardButton("🧑‍💼 Assign Rank", callback_data="admin_assign_rank")],
        [InlineKeyboardButton("📨 Review Promotions", callback_data="admin_review_promotions")],
        [InlineKeyboardButton("🧹 Reset Violations", callback_data="admin_reset_violations")],
        [InlineKeyboardButton("⛔ Mute User", callback_data="admin_mute_user")],
        [InlineKeyboardButton("🔄 Reload Configs", callback_data="admin_reload_configs")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("👑 *Admin Panel*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- Admin Callbacks ---
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "admin_view_stats":
        await query.edit_message_text("📊 Gathering stats... (coming soon)")

    elif data == "admin_export_users":
        await query.edit_message_text("📤 Exporting users... (coming soon)")

    elif data == "admin_import_users":
        await query.edit_message_text("📥 Importing users... (coming soon)")

    elif data == "admin_assign_rank":
        await query.edit_message_text("🧑‍💼 Assigning rank... Use /assignrank <@username> <Rank>")

    elif data == "admin_review_promotions":
        await query.edit_message_text("📨 Reviewing promotion requests... (coming soon)")

    elif data == "admin_reset_violations":
        await query.edit_message_text("🧹 Resetting violations... (coming soon)")

    elif data == "admin_mute_user":
        await query.edit_message_text("⛔ Muting users... (coming soon)")

    elif data == "admin_reload_configs":
        await query.edit_message_text("🔄 Reloading configs... (coming soon)")

    else:
        await query.edit_message_text("❓ Unknown admin action.")

