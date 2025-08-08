import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.constants import ADMIN_ID
from utils.helpers import store_message_id, delete_old_messages

# --- Logs ---
async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    chat_id = update.effective_chat.id
    await delete_old_messages(context, chat_id)  # 🧹 Clear old messages

    try:
        with open('scamsclub_bot.log', 'r') as f:
            lines = f.readlines()[-20:]
            log_text = ''.join(lines).strip()
            msg = await update.message.reply_text(
                f"📝 *Last 20 Log Entries:*\n\n```\n{log_text}\n```",
                parse_mode="Markdown"
            )
            store_message_id(chat_id, msg.message_id)  # 💾 Store new log message
    except FileNotFoundError:
        msg = await update.message.reply_text("⚠️ No log file found.")
        store_message_id(chat_id, msg.message_id)