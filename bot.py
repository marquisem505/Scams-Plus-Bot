import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ChatMemberHandler
)

# 🔐 Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-2286707356"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://scamsclub.store/telegram-webhook
PORT = int(os.getenv("PORT", 8080))

# 👋 Triggered when someone joins
async def welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member.new_chat_member.user
    if update.chat_member.chat.id != GROUP_ID:
        return

    if update.chat_member.status == "member":
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

# 🎯 Handles button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "start_onboarding":
        await query.message.reply_text("🧠 Let's get you onboarded. First, what do you want to learn?")
    elif query.data == "help":
        await query.message.reply_text("👤 DM @ScamsClubSupport or ask your inviter for help.")

# 🧠 Main async webhook runner
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(ChatMemberHandler(welcome_user, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("👋 Welcome!")))

    # Set webhook and start server
    await app.bot.set_webhook(WEBHOOK_URL)
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        path="/telegram-webhook",
    )

if __name__ == "__main__":
    asyncio.run(main())