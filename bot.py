# --- Imports ---
import os
import asyncio
import logging
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ChatMemberHandler
)
from db import (
    create_user_if_not_exists,
    set_user_rank,
    get_user_id_by_username,
    get_user_rank,
    update_onboarding,
    get_onboarding_summary,
    init_db
)

# --- Load ENV ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-2286707356"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "6967780222"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# --- Logging ---
logging.basicConfig(
    filename='scamsclub_bot.log',
    filemode='a',
    format='[%(asctime)s] %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Memory ---
onboarding_memory = {}   # user_id: dict
user_ranks = {}          # user_id: rank
violation_counts = {}  # user_id: int
logged_in_admins = set()  # Stores Telegram user_ids who have logged in as admin

# --- Topic Mapping ---
topic_name_to_id = {
    "Welcome To Scam's Plus - Start Here": 2458,
    "General Chat": 2401,
    "Scammers Warnings": 2408,
    "Announcements": 2405,
    "Con Academy": 2406,
    "Questions": 2411,
    "Tools & Bots": 2404,
    "Verified Guides": 2403,
    "Verified Vendors / Collabs": 2407,
    "Testing Lab": 2454,
    "VIP Lounge": 2402
}

# --- Rank Access ---
rank_access_topics = {
    "Lookout": [
        topic_name_to_id["Welcome To Scam's Plus - Start Here"],
        topic_name_to_id["General Chat"],
        topic_name_to_id["Scammers Warnings"],
        topic_name_to_id["Announcements"],
        topic_name_to_id["Con Academy"],
        topic_name_to_id["Tools & Bots"],
        topic_name_to_id["Verified Guides"]
    ],
    "Runner": [
        topic_name_to_id["Welcome To Scam's Plus - Start Here"],
        topic_name_to_id["General Chat"],
        topic_name_to_id["Scammers Warnings"],
        topic_name_to_id["Announcements"],
        topic_name_to_id["Con Academy"],
        topic_name_to_id["Questions"],
        topic_name_to_id["Tools & Bots"],
        topic_name_to_id["Verified Guides"]
    ],
    "Closer": [
        topic_name_to_id["Welcome To Scam's Plus - Start Here"],
        topic_name_to_id["General Chat"],
        topic_name_to_id["Scammers Warnings"],
        topic_name_to_id["Announcements"],
        topic_name_to_id["Con Academy"],
        topic_name_to_id["Questions"],
        topic_name_to_id["Tools & Bots"],
        topic_name_to_id["Verified Guides"],
        topic_name_to_id["Verified Vendors / Collabs"],
        topic_name_to_id["Testing Lab"]
    ],
    "Inner Circle": [
        topic_name_to_id["Welcome To Scam's Plus - Start Here"],
        topic_name_to_id["General Chat"],
        topic_name_to_id["Scammers Warnings"],
        topic_name_to_id["Announcements"],
        topic_name_to_id["Con Academy"],
        topic_name_to_id["Questions"],
        topic_name_to_id["Tools & Bots"],
        topic_name_to_id["Verified Guides"],
        topic_name_to_id["Verified Vendors / Collabs"],
        topic_name_to_id["Testing Lab"],
        topic_name_to_id["VIP Lounge"]
    ],
    "OG Member": [
        topic_name_to_id["Welcome To Scam's Plus - Start Here"],
        topic_name_to_id["General Chat"],
        topic_name_to_id["Scammers Warnings"],
        topic_name_to_id["Announcements"],
        topic_name_to_id["Con Academy"],
        topic_name_to_id["Questions"],
        topic_name_to_id["Tools & Bots"],
        topic_name_to_id["Verified Guides"],
        topic_name_to_id["Verified Vendors / Collabs"],
        topic_name_to_id["Testing Lab"],
        topic_name_to_id["VIP Lounge"]
    ]
}

# --- Admin Panel ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    # --- In group ---
    if chat_type in ["group", "supergroup"]:
        if user_id != ADMIN_ID:
            await update.message.reply_text("🚫 You are not authorized.")
            return
        else:
            await update.message.reply_text("✅ DM me privately to access the admin panel.")
            return

    # --- In DM ---
    if user_id in logged_in_admins or context.user_data.get("admin_authenticated"):
        await send_admin_panel(update)
    else:
        await update.message.reply_text("🔐 Please enter the admin password:")
        context.user_data["awaiting_admin_password"] = True

# --- Admin Buttons ---
async def send_admin_panel(update: Update):
    keyboard = [
        [InlineKeyboardButton("📊 View Stats", callback_data="admin_view_stats")],
        [InlineKeyboardButton("📤 Export Users", callback_data="admin_export_users")],
        [InlineKeyboardButton("📥 Import Users", callback_data="admin_import_users")],
        [InlineKeyboardButton("🧑‍💼 Assign Rank", callback_data="admin_assign_rank")],
        [InlineKeyboardButton("📨 Review Promotion Requests", callback_data="admin_review_promotions")],
        [InlineKeyboardButton("🧹 Reset Violations", callback_data="admin_reset_violations")],
        [InlineKeyboardButton("⛔ Mute User", callback_data="admin_mute_user")],
        [InlineKeyboardButton("🔄 Reload Configs", callback_data="admin_reload_configs")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("👑 *Admin Panel* 👑", reply_markup=reply_markup, parse_mode="Markdown")

# --- Admin Callbacks ---
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "admin_view_stats":
        await query.edit_message_text("📊 Gathering stats... (coming soon)")

    elif data == "admin_export_users":
        await query.edit_message_text("📤 Exporting users... (coming soon)")

    elif data == "admin_import_users":
        await query.edit_message_text("📥 Importing users... (coming soon)")

    elif data == "admin_assign_rank":
        await query.edit_message_text("🧑‍💼 Assigning rank... Use /assignrank <@username> <Rank>")

    elif data == "admin_review_promotions":
        await query.edit_message_text("📨 Reviewing promotion requests... (coming soon)")

    elif data == "admin_reset_violations":
        await query.edit_message_text("🧹 Resetting violations... (coming soon)")

    elif data == "admin_mute_user":
        await query.edit_message_text("⛔ Muting users... (coming soon)")

    elif data == "admin_reload_configs":
        await query.edit_message_text("🔄 Reloading configs... (coming soon)")

    else:
        await query.edit_message_text("❓ Unknown admin action.")

# --- Admin Logout ---
async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in logged_in_admins:
        logged_in_admins.remove(user_id)
        context.user_data["admin_authenticated"] = False
        await update.message.reply_text("🚪 You’ve been logged out of the admin panel.")
    else:
        await update.message.reply_text("⚠️ You're not logged in.")

# --- Welcome Fallback ---
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

# --- Auto Rank Members On Join ---
async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member.new_chat_member
    if member.status == "member":
        user = member.user
        create_user_if_not_exists(user.id, user.username, user.first_name)
        set_user_rank(user.id, "Lookout")
        await context.bot.send_message(chat_id=user.id, text="Welcome to Scam's Plus! You've been assigned the rank: Lookout.")
        
# --- Welcome ---
async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member.new_chat_member.user
    if update.chat_member.chat.id != GROUP_ID:
        return

    if update.chat_member.new_chat_member.status == "member":
        create_user_if_not_exists(member.id, member.username, member.first_name)
        if get_user_rank(member.id) is None:
            set_user_rank(member.id, "Lookout")
        logging.info(f"Assigned default rank 'Lookout' to user {member.id}")

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

# --- Start ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("👋 DM me privately to access onboarding, rank tools, and more.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 Restart Onboarding", callback_data="start_onboarding")],
        [InlineKeyboardButton("🧠 Start Here Guide", url="https://t.me/c/2286707356/2458")], 
        [InlineKeyboardButton("👤 My Rank", callback_data="check_rank")],
        [InlineKeyboardButton("📤 Request Promotion", callback_data="promoteme")]
    ])

    await update.message.reply_text(
        "👋 Welcome to Scam’s Plus.\n\nThis bot helps with onboarding, ranks, and navigating the group.\n\nUse the buttons below to get started 👇",
        reply_markup=keyboard
    )
    
# --- Buttons ---
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

# --- Elifs ---
    elif query.data == "help":
        await query.message.reply_text("👤 DM @ScamsClub_Store for help.")

    elif query.data.startswith("learn_"):
        choice = query.data.replace("learn_", "")
        create_user_if_not_exists(user_id, query.from_user.username, query.from_user.first_name)
        update_onboarding(user_id, learning_path=choice)

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
                [InlineKeyboardButton("💳 Beginner", callback_data="exp_beginner")],
                [InlineKeyboardButton("💻 Intermediate", callback_data="exp_intermediate")],
                [InlineKeyboardButton("🥇 Advanced", callback_data="exp_advanced")]
            ])
        )

    elif query.data.startswith("exp_"):
        level = query.data.replace("exp_", "")
        update_onboarding(user_id, experience=level)

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
        update_onboarding(user_id, interest=focus)
        summary = get_onboarding_summary(user_id)
        await query.message.reply_text(
            f"✅ All set!\n\n"
            f"👤 {summary['first_name']} (@{summary['username']})\n"
            f"🧠 Goal: `{summary['learning_path']}`\n"
            f"📈 Experience: `{summary['experience']}`\n"
            f"🎯 Focus: `{summary['interest']}`\n\n"
            "👉 Start exploring pinned topics or tag a mentor if you’re stuck.",
            parse_mode="Markdown"
        )
# --- Check Rank --
    elif query.data == "check_rank":
        rank = get_user_rank(user_id) or "❌ Unranked"
        await query.message.reply_text(f"🏷 Your current rank: `{rank}`", parse_mode="Markdown")
        
# --- Topic Guard ---
async def topic_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ignore if not from the main group or not in a thread
    if update.message.chat_id != GROUP_ID or update.message.message_thread_id is None:
        return

    uid = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    topic_id = update.message.message_thread_id
    user_rank = get_user_rank(uid) or "Lookout"  # Default to Lookout if unknown

    allowed_topics = rank_access_topics.get(user_rank, [])

    if topic_id not in allowed_topics:
        # Count and store violations
        increment_violation(uid)

        # Attempt to delete the message
        try:
            await update.message.delete()
        except Exception as e:
            logging.warning(f"❌ Couldn't delete message from @{username}: {e}")

        # Public warning in the thread
        try:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                message_thread_id=topic_id,
                text=f"⚠️ @{username}, you're not allowed to post in this topic at your current rank ({user_rank}).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Request Promotion", callback_data="promoteme")]
                ])
            )
        except Exception as e:
            logging.warning(f"⚠️ Failed to warn user in group thread: {e}")

        # Private DM
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=(
                    f"🚫 You tried posting in a restricted topic (ID: `{topic_id}`).\n"
                    f"Your current rank is: *{user_rank}*\n\n"
                    f"Use /promoteme in the group to request a rank promotion if needed."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.warning(f"❌ Failed to DM user @{username}: {e}")

        # Optional mute if too many violations
        if violation_counts[uid] >= 3:
            try:
                await context.bot.restrict_chat_member(
                chat_id=GROUP_ID,
                user_id=uid,
                permissions=ChatPermissions(can_send_messages=False)
                )
                await context.bot.send_message(
                    chat_id=uid,
                    text="🔇 You’ve been muted for repeated violations. Contact an admin to appeal."
                )
            except Exception as e:
                logging.warning(f"🚫 Could not mute @{username}: {e}")

# --- Promote Me ---
async def promoteme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📤 To request a rank promotion, reply here with:\n\n"
        "• What you’ve done or contributed\n"
        "• Screenshots or drop results (if any)\n"
        "• Your desired rank\n\n"
        "✅ After replying, an admin will be notified."
    )

# --- Forward Promote Me Replies ---
async def reply_forwarder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and "rank promotion" in update.message.reply_to_message.text:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📬 Rank request from @{update.effective_user.username}:\n\n{update.message.text}"
        )

# --- Assign Rank ---
# --- Assign Rank ---
async def assign_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /assignrank <@username> <Rank>")

    username = context.args[0].lstrip('@')
    rank = context.args[1].capitalize()
    uid = get_user_id_by_username(username)

    if uid:
        set_user_rank(uid, rank)
        await update.message.reply_text(f"✅ Assigned rank `{rank}` to @{username}.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ User @{username} not found in database.")

# --- Demote Rank ---
async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not authorized.")
    if len(context.args) < 1:
        return await update.message.reply_text("Usage: /demote <@username>")

    username = context.args[0].lstrip('@')
    uid = get_user_id_by_username(username)

    if uid:
        set_user_rank(uid, "Lookout")
        await update.message.reply_text(f"⚠️ @{username} was demoted to `Lookout`.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ User @{username} not found in database.")

# --- My Rank ---
async def myrank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    rank = get_user_rank(uid) or "❌ Unranked"
    await update.message.reply_text(f"🏷 Your current rank: `{rank}`", parse_mode="Markdown")

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

# --- Status ---
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is online and running smoothly.")

# --- Webhook Health Check ---
async def healthcheck(request):
    return web.Response(text="✅ Bot is alive!", status=200)

# --- Main Debugging ---


# --- Main ---
async def main():
    # --- Setup Telegram Application ---
    app = Application.builder().token(BOT_TOKEN).build()
    await app.bot.set_webhook(f"{WEBHOOK_URL}/telegram-webhook")
    logging.info("Bot started successfully.")

    me = await app.bot.get_me()
    create_user_if_not_exists(me.id, me.username, me.first_name)

    # --- Handlers ---
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("logout", logout_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("assignrank", assign_rank))
    app.add_handler(CommandHandler("demote", demote))
    app.add_handler(CommandHandler("myrank", myrank))
    app.add_handler(CommandHandler("promoteme", promoteme))
    app.add_handler(CommandHandler("logs", view_logs))

    app.add_handler(ChatMemberHandler(handle_join, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member_message))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, admin_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, reply_forwarder))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), topic_guard))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(admin_callback_handler))

    # --- Web Server for Webhook ---
    async def telegram_webhook(request):
        try:
            data = await request.json()
            update = Update.de_json(data, app.bot)
            await app.process_update(update)
            return web.Response(text="OK")
        except Exception as e:
            logging.error("Webhook Error: " + str(e))
            return web.Response(status=500, text=f"Error: {e}")

    async def healthcheck(request):
        return web.Response(text="✅ Bot is alive!", status=200)

    web_app = web.Application()
    web_app.router.add_get("/status", healthcheck)
    web_app.router.add_post("/telegram-webhook", telegram_webhook)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    await app.initialize()
    await app.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    init_db()
    asyncio.run(main())