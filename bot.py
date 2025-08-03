import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ChatMemberHandler
)

# Load environment
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-2286707356"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "6967780222"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# In-memory tracking
onboarding_memory = {}   # user_id: dict
user_ranks = {}          # user_id: rank

rank_access_topics = {
    "Lookout": ["General Chat", "Questions", "Tools & Bots"],
    "Runner": ["Verified Guides", "Con Academy"],
    "Closer": ["Verified Vendors", "Testing Lab"],
    "Inner Circle": ["VIP Lounge"],
    "OG Member": ["VIP Lounge"]
}

# Welcome message (MessageHandler)
async def new_chat_member_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Start Onboarding", callback_data="start_onboarding")],
            [InlineKeyboardButton("📚 Group Rules", url="https://t.me/ScamsClubRules")],
            [InlineKeyboardButton("❓ Need Help?", callback_data="help")]
        ])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"👋 Welcome {member.mention_html()} to Scam’s Plus!\nThis ain’t your average chat. Everything here is structured, ranked, and protected.\n\nPress a button below to get started 👇",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

# ChatMemberHandler fallback
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

# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "start_onboarding":
        await query.message.reply_text(
            "🧠 Let’s get you set up.\n\nWhat do you want to do first?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 Drops & Methods", callback_data="learn_drops")],
                [InlineKeyboardButton("🛠 Tools & Bots", callback_data="learn_tools")],
                [InlineKeyboardButton("🔗 Collab With Vendors", callback_data="learn_vendors")],
                [InlineKeyboardButton("🧑‍🎓 Get Mentorship?", callback_data="learn_mentorship")],
                [InlineKeyboardButton("🙋 Ask Questions?", callback_data="learn_questions")],
                [InlineKeyboardButton("🥇 Learn About V.I.P. Lounge?", callback_data="learn_vip")],
                [InlineKeyboardButton("❓ Not Sure Yet", callback_data="learn_unsure")]
            ])
        )

    elif query.data == "help":
        await query.message.reply_text("👤 DM @ScamsClub_Store for help.")

    elif query.data.startswith("learn_"):
        choice = query.data.replace("learn_", "")
        onboarding_memory[user_id] = {
            "username": query.from_user.username,
            "first_name": query.from_user.first_name,
            "learning_path": choice
        }

        response_map = {
            "drops": "🔥 Good choice. Check out the `Verified Guides` and `Con Academy` threads to begin.",
            "tools": "🛠 You’ll want to hit the `Tools & Bots` thread — we keep all the real builds in there.",
            "mentorship": "🧑‍🎓 Check the `Con Academy` topic — one of our mentors will reach out to you.",
            "vip": "🥇 Check the `V.I.P Lounge` topic — you'll learn how to get your rank up to become whitelisted into the lounge.",
            "questions": "🙋 Go to the `Questions` topic — one of our admins/members will answer any questions you may have.",
            "vendors": "🔗 Check the `Verified Vendors / Collabs` topic — only verified vendors are allowed.",
            "unsure": "💡 That's cool too. Scroll through the `Welcome To Scam's Plus - Start Here` thread and lurk a bit before diving in."
        }

        await query.message.reply_text(response_map.get(choice, "✅ Let’s continue..."))

        await query.message.reply_text(
            "🧠 What’s your current experience level?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🟢 Beginner", callback_data="exp_beginner")],
                [InlineKeyboardButton("🟡 Intermediate", callback_data="exp_intermediate")],
                [InlineKeyboardButton("🔴 Advanced", callback_data="exp_advanced")]
            ])
        )

    elif query.data.startswith("exp_"):
        level = query.data.replace("exp_", "")
        onboarding_memory[user_id]["experience"] = level

        await query.message.reply_text(
            "🔍 Any specific drops, tools, or methods you're looking for?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏦 Refunds", callback_data="target_refunds"),
                 InlineKeyboardButton("💳 CC/Fullz", callback_data="target_cards")],
                [InlineKeyboardButton("📲 Spoofing & OTPs", callback_data="target_otp"),
                 InlineKeyboardButton("🧑‍💻 Automations", callback_data="target_auto")],
                [InlineKeyboardButton("📚 Just Exploring", callback_data="target_general")]
            ])
        )

    elif query.data.startswith("target_"):
        focus = query.data.replace("target_", "")
        onboarding_memory[user_id]["interest"] = focus
        summary = onboarding_memory[user_id]
        await query.message.reply_text(
            f"✅ All set!\n\n"
            f"👤 {summary['first_name']} (@{summary['username']})\n"
            f"🧠 Goal: `{summary['learning_path']}`\n"
            f"📈 Experience: `{summary['experience']}`\n"
            f"🎯 Focus: `{summary['interest']}`\n\n"
            "👉 Start exploring pinned topics or tag a mentor if you’re stuck.",
            parse_mode="Markdown"
        )

# /myrank
async def myrank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    rank = user_ranks.get(uid, "❌ Unranked")
    await update.message.reply_text(f"🏷 Your current rank: `{rank}`", parse_mode="Markdown")

# Auto-delete or warn based on topic
async def topic_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != GROUP_ID or not update.message.is_topic_message:
        return

    uid = update.effective_user.id
    user_rank = user_ranks.get(uid, "Lookout")
    allowed_topics = []

    for rank, topics in rank_access_topics.items():
        allowed_topics += topics
        if rank == user_rank:
            break  # stop once we reach user's rank

    topic_name = update.message.message_thread_title or ""
    if topic_name not in allowed_topics:
        try:
            await update.message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                message_thread_id=update.message.message_thread_id,
                text=f"⚠️ @{update.effective_user.username}, this topic is restricted to higher ranks.\nUse `/promoteme` if you think you’re ready."
            )
        except:
            pass

# /promoteme
async def promoteme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📤 To request a rank promotion, reply here with:\n\n"
        "• What you’ve done or contributed\n"
        "• Screenshots or drop results (if any)\n"
        "• Your desired rank\n\n"
        "✅ After replying, an admin will be notified automatically."
    )

# Forward replies to /promoteme message to admin
async def reply_forwarder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and "rank promotion" in update.message.reply_to_message.text:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📬 Rank request from @{update.effective_user.username}:\n\n{update.message.text}"
            )
        except Exception as e:
            print(f"Failed to forward promoteme submission: {e}")

# /demote <@user>
async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")
    if len(context.args) < 1:
        return await update.message.reply_text("Usage: /demote <@username>")

    username = context.args[0].lstrip('@')
    uid = next((uid for uid, data in onboarding_memory.items() if data.get("username") == username), None)

    if uid and uid in user_ranks:
        old_rank = user_ranks.pop(uid)
        await update.message.reply_text(f"⚠️ @{username} was demoted (removed from `{old_rank}`).", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ User @{username} not found or has no rank.")

# /viewonboarding (admin)
async def view_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not onboarding_memory:
        await update.message.reply_text("🗃 No onboarding data yet.")
        return
    msg = "📋 Onboarding Activity:\n\n"
    for uid, data in onboarding_memory.items():
        rank = user_ranks.get(uid, "❌ Unranked")
        msg += f"• {data['first_name']} (@{data['username']}) → `{data['learning_path']}` | Rank: {rank}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# /assignrank <@user> <Rank>
async def assign_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /assignrank <@username> <Rank>")

    username = context.args[0].lstrip('@')
    rank = context.args[1].capitalize()
    uid = next((uid for uid, data in onboarding_memory.items() if data.get("username") == username), None)

    if uid:
        user_ranks[uid] = rank
        await update.message.reply_text(f"✅ Assigned rank `{rank}` to @{username}.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ User @{username} not found in onboarding memory.")

# /status
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is online and running smoothly.")

# Webhook health
async def healthcheck(request):
    return web.Response(text="✅ Bot is alive!", status=200)

# --- MAIN ---
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, reply_forwarder))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), topic_guard))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member_message))
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("👋 Welcome!")))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("viewonboarding", view_onboarding))
    app.add_handler(CommandHandler("assignrank", assign_rank))
    app.add_handler(CommandHandler("myrank", myrank))
    app.add_handler(CommandHandler("promoteme", promoteme))
    app.add_handler(CommandHandler("demote", demote))
    

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

    print(f"🚀 Bot running on port {PORT} — Webhook set to {WEBHOOK_URL}")
    await app.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
