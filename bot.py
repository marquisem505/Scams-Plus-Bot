import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
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

# 🧠 In-memory onboarding tracker
onboarding_memory = {}

# 👋 Greet new members via MessageHandler
async def new_chat_member_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# 👋 Greet new members via ChatMemberHandler (privacy mode fallback)
async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# 🔘 Button interaction handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "start_onboarding":
        # Start onboarding Q1
        await query.message.reply_text(
            "🧠 Let’s get you set up.\n\nWhat do you want to learn first?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 Drops & Methods", callback_data="learn_drops")],
                [InlineKeyboardButton("🛠 Tools & Bots", callback_data="learn_tools")],
                [InlineKeyboardButton("💳 Credit & Funding", callback_data="learn_credit")],
                [InlineKeyboardButton("❓ Not Sure Yet", callback_data="learn_unsure")]
            ])
        )

    elif query.data == "help":
        await query.message.reply_text("👤 DM @ScamsClubSupport or ask your inviter for help.")

    elif query.data.startswith("learn_"):
        choice = query.data.replace("learn_", "")
        onboarding_memory[user_id] = {
            "username": query.from_user.username,
            "first_name": query.from_user.first_name,
            "learning_path": choice
        }

        response_map = {
            "drops": "🔥 Solid choice. Check out the `Verified Guides` and `Con Academy` threads to begin.",
            "tools": "🛠 You’ll want to hit the `Tools & Bots` thread — we keep all the real builds in there.",
            "credit": "💳 Check the `Con Academy` and `Questions` topics — tons of sauce on credit plays.",
            "unsure": "💡 No worries. Scroll through the `Start Here` thread and lurk a bit before diving in."
        }
        await query.message.reply_text(response_map.get(choice, "✅ You're all set."))

# ✅ /status command
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is online and running smoothly.")

# 🩺 Healthcheck route
async def healthcheck(request):
    return web.Response(text="✅ Bot is alive!", status=200)

# 🚀 Main function
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member_message))
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("👋 Welcome!")))
    app.add_handler(CommandHandler("status", status_command))

    async def telegram_webhook(request):
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        return web.Response(text="OK")

    web_app = web.Application()
    web_app.router.add_get("/status", healthcheck)
    web_app.router.add_post("/telegram-webhook", telegram_webhook)

    await app.bot.set_webhook(WEBHOOK_URL)
    await app.initialize()

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"🚀 Running on port {PORT} — Webhook: {WEBHOOK_URL}")
    await app.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
