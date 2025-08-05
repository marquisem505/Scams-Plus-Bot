# handlers/logs.py

import os
from telegram import Update
from telegram.ext import ContextTypes
from utils.constants import ADMIN_ID

# --- Logs ---
async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        with open('scamsclub_bot.log', 'r') as f:
            lines = f.readlines()[-20:]
            await update.message.reply_text("📝 Last 20 Log Entries:\n\n" + ''.join(lines[-20:]))
    except FileNotFoundError:
        await update.message.reply_text("⚠️ No log file found.")