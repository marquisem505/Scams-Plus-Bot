import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ChatMemberHandler
)

# 🔐 Load environment
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-2286707356"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# 👋 Greet new members via MessageHandler
async def new_chat_member_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ Detected new_chat_members (via message)")
    for member in update.message.new_chat_members:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Start Onboarding", callback_data="start_onboarding")],
            [InlineKeyboardButton("📚 Group Rules", url="https://t.me/ScamsClubRules")],
            [InlineKeyboardButton("❓ Need Help?", callback_data="help")]
        ])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"👋 Welcome {member.mention_html()} to Scam’s Plus!\n\nPress a button below to get started 👇",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

# 👋 Greet new members via ChatMemberHandler (for privacy mode)
async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ Detected new member (via chat_member update)")
    member = update.chat_member.new_chat_member.user
    if update.chat_member.chat.id != GROUP_ID:
        return

    if update.chat_member.new_chat_member.status == "member":
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

# 🔘 Button interaction
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_onboarding":
        await query.message.reply_text("🧠 Let's get you onboarded. First, what do you want to learn?")
    elif query.data == "help":
        await query.message.reply_text("👤 DM @ScamsClubSupport or ask your inviter for help.")

# ✅ /status command
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is online and running smoothly.")

# 🩺 Healthcheck route
async def healthcheck(request):
    return web.Response(text="✅ Bot is alive!", status=200)

# 🚀 Main function
async def main():
    # Create telegram app
    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member_message))
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("👋 Welcome!")))
    app.add_handler(CommandHandler("status", status_command))

    # Telegram webhook POST receiver
    async def telegram_webhook(request):
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        return web.Response(text="OK")

    # aiohttp app with webhook & healthcheck
    web_app = web.Application()
    web_app.router.add_get("/status", healthcheck)
    web_app.router.add_post("/telegram-webhook", telegram_webhook)

    # Set Telegram webhook
    await app.bot.set_webhook(WEBHOOK_URL)

    # REQUIRED: initialize before starting
    await app.initialize()

    # Start web server
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"🚀 Running on port {PORT} — Webhook: {WEBHOOK_URL}")
    await app.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())