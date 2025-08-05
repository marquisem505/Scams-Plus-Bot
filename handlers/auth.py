# handlers/auth.py

from telegram import Update
from telegram.ext import ContextTypes
from constants import ADMIN_PASSWORD
logged_in_admins = set()

# --- Admin Authentication ---
async def admin_password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if context.user_data.get("awaiting_admin_password"):
        if text == ADMIN_PASSWORD:
            logged_in_admins.add(user_id)
            context.user_data["admin_authenticated"] = True
            context.user_data["awaiting_admin_password"] = False
            await update.message.reply_text("🔓 Access granted. Use /admin again.")
        else:
            await update.message.reply_text("❌ Incorrect password. Try again.")

# --- Admin Logout ---
async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in logged_in_admins:
        logged_in_admins.remove(user_id)
        context.user_data["admin_authenticated"] = False
        await update.message.reply_text("🚪 You’ve been logged out of the admin panel.")
    else:
        await update.message.reply_text("⚠️ You're not logged in.")