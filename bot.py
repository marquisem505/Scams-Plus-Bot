import os
import asyncio
from dotenv import load_dotenv
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ChatMemberHandler, ContextTypes
)

# 🌍 Load .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1000000000000"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# 👋 New member welcome
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

# 🎯 Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_onboarding":
        await query.message.reply_text("🧠 Let's get you onboarded. First, what do you want to learn?")
    elif query.data == "help":
        await query.message.reply_text("👤 DM @ScamsClubSupport or ask your inviter for help.")

# ✅ /status command
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is online and running.")

# 🚑 HTTP healthcheck for Railway
async def healthcheck(request):
    return web.Response(text="✅ Healthcheck OK", status=200)

# 🚀 Main
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(ChatMemberHandler(welcome_user, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("status", status_command))

    # Set Telegram webhook
    await app.bot.set_webhook(WEBHOOK_URL)

    # aiohttp app for web server
    web_app = web.Application()
    web_app.router.add_get("/status", healthcheck)
    web_app.router.add_post("/telegram-webhook", app.request_handler)  # ✅ correct for v20+

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"🚀 Bot is live at port {PORT}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())