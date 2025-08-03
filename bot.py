import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ChatMemberHandler
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-2286707356"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# 👋 New member handler
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

# 🔘 Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_onboarding":
        await query.message.reply_text("🧠 Let's get you onboarded. First, what do you want to learn?")
    elif query.data == "help":
        await query.message.reply_text("👤 DM @ScamsClubSupport or ask your inviter for help.")

# 🟢 /status handler
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is online and running smoothly.")

# 🏥 Health check for Railway
async def healthcheck(request):
    return web.Response(text="✅ Bot is alive!", status=200)

async def main():
    # Create Telegram app
    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(ChatMemberHandler(welcome_user, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("👋 Welcome!")))
    app.add_handler(CommandHandler("status", lambda update, context: update.message.reply_text("✅ Bot is healthy.")))

    # Set webhook
    await app.bot.set_webhook(WEBHOOK_URL)

    # Build aiohttp web app BEFORE router freezes
    web_app = web.Application()
    web_app.router.add_get("/status", healthcheck)
    web_app.router.add_post("/telegram-webhook", app.webhook_handler)

    # Serve
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"🚀 Webhook running on port {PORT}")
    await asyncio.Event().wait()  # Keep running

if __name__ == "__main__":
    asyncio.run(main())