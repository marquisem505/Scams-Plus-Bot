from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import delete_old_messages, store_message_id  # ✅ Import

# --- Status ---
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await delete_old_messages(context, chat_id)  # 🧹 Clean up old messages

    msg = await update.message.reply_text("✅ Bot is online and running smoothly.")  # 🔔 Send fresh status message
    store_message_id(context, chat_id, msg.message_id)  # 💾 Track for future cleanup