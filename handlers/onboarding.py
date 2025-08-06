from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMemberUpdated, InputFile
from telegram.ext import ContextTypes
from db import create_user_if_not_exists, update_onboarding, get_user_rank, set_user_rank, get_onboarding_summary
from utils.constants import GROUP_ID, topic_name_to_id, rank_access_topics, ADMIN_ID
import logging
import os

onboarding_memory = {}

# --- Member Join Handler (via ChatMemberHandler) ---
async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.chat_member:
        return  # Exit early if chat_member is None

    member = update.chat_member.new_chat_member.user
    chat = update.chat_member.chat

    if not chat or chat.id != GROUP_ID:
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
            chat_id=chat.id,
            text=f"👋 Welcome {member.mention_html()} to Scam’s Plus!\n\nPress a button below to get started 👇",  # type: ignore
            reply_markup=keyboard,
            parse_mode="HTML"
        )

# --- Welcome Fallback (NEW_CHAT_MEMBERS) ---
async def new_chat_member_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📘 Start Onboarding", callback_data="start_onboarding")],
                [InlineKeyboardButton("📚 Group Rules", url="https://t.me/ScamsClubRules")],
                [InlineKeyboardButton("❓ Need Help?", callback_data="help")]
            ])
        for member in update.message.new_chat_members:
            if isinstance(member, User):  # ensure it's the expected type
             await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"👋 Welcome {member.mention_html()} to Scam’s Plus!\n"
                "This ain’t your average chat. Everything here is structured, ranked, and protected.\n\n"
                "Press a button below to get started 👇"
            ),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
# --- /start Command ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and update.effective_chat.type in ["group", "supergroup"]:
        if update.message:
            await update.message.reply_text("👋 DM me privately to access onboarding, rank tools, and more.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 Restart Onboarding", callback_data="start_onboarding")],
        [InlineKeyboardButton("🧠 Start Here Guide", url="https://t.me/c/2286707356/2458")],
        [InlineKeyboardButton("👤 My Rank", callback_data="check_rank")],
        [InlineKeyboardButton("📤 Request Promotion", callback_data="promoteme")]
    ])

    if update.message:
        await update.message.reply_text(
            "👋 Welcome to Scam’s Plus.\n\nThis bot helps with onboarding, ranks, and navigating the group.\n\nUse the buttons below to get started 👇",
            reply_markup=keyboard
        )
# --- Handle Private Messages ---
async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = update.effective_user.id
    text = message.text.strip()

    if context.user_data.get("admin_authenticated"):
        await message.reply_text("✅ You're already logged in as admin. Use /admin to access the panel.")
        return

    if context.user_data.get("awaiting_admin_password"):
        if text == ADMIN_PASSWORD:
            logged_in_admins.add(user_id)
            context.user_data["admin_authenticated"] = True
            context.user_data["awaiting_admin_password"] = False
            await message.reply_text("🔓 Password correct. You’re now logged in as admin. Use /admin to access the panel.")
        else:
            await message.reply_text("❌ Incorrect password. Try again or type /logout to cancel.")
        return

    # Prompt if user hasn’t started login flow
    await message.reply_text("🔐 Please enter the admin password:")
    context.user_data["awaiting_admin_password"] = True

# --- View Logs Command ---
async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not authorized to view logs.")
        return

    log_path = "scamsclub_bot.log"

    if not os.path.exists(log_path):
        await update.message.reply_text("⚠️ Log file not found.")
        return

    try:
        with open(log_path, "rb") as log_file:
            await update.message.reply_document(
                document=InputFile(log_file, filename="scamsclub_bot.log"),
                caption="📄 Here is the latest log file:"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending log file: {str(e)}")

# --- Button Logic ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query is None or query.from_user is None or query.message is None:
        return  # Defensive check for missing data

    await query.answer()
    from_user = query.from_user
    user_id = from_user.id  # noqa: F841 if not used further

    if query.data == "start_onboarding":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Drops & Methods", callback_data="learn_drops")],
            [InlineKeyboardButton("🛠 Tools & Bots", callback_data="learn_tools")],
            [InlineKeyboardButton("🔗 Collab With Vendors", callback_data="learn_vendors")],
            [InlineKeyboardButton("🧑‍🎓 Get Mentorship?", callback_data="learn_mentorship")],
            [InlineKeyboardButton("🙋 Ask Questions?", callback_data="learn_questions")],
            [InlineKeyboardButton("🥇 Learn About V.I.P. Lounge?", callback_data="learn_vip")],
            [InlineKeyboardButton("❓ Not Sure Yet", callback_data="learn_unsure")]
        ])
        if query.message:
            await query.message.reply_text(
        "🧠 Let’s get you set up.\n\nWhat do you want to do first?",
        reply_markup=keyboard
    )

    elif query.data == "help":
        await query.message.reply_text("👤 DM @ScamsClub_Store for help.")

    elif query.data.startswith("learn_"):
        choice = query.data.replace("learn_", "")
        create_user_if_not_exists(user_id, from_user.username, from_user.first_name)
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
# --- Topic Guard Handler ---
async def topic_guard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.message_thread_id:
        return

    thread_id = message.message_thread_id
    user_id = message.from_user.id
    rank = get_user_rank(user_id) or "Lookout"

    allowed_topics = rank_access_topics.get(rank, [])

    if thread_id not in allowed_topics:
        try:
            # Warn the user
            await message.reply_text(
                "🚫 You don’t have permission to post in this topic yet based on your current rank.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Request Promotion", callback_data="promoteme")]
                ])
            )

            # DM the user
            await context.bot.send_message(
                chat_id=user_id,
                text="⚠️ You posted in a restricted topic.\n\nEach topic has rank-based access. Complete onboarding and request a promotion to gain more access."
            )

            # Optionally delete the original message
            await message.delete()
        except Exception as e:
            print(f"❌ Failed to enforce topic guard: {e}")

# --- Forward Promotion Replies to Admin ---
async def reply_forwarder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.reply_to_message:
        original_text = update.message.reply_to_message.text.lower()
        if "rank promotion" in original_text or "request a rank promotion" in original_text:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        f"📨 *Promotion Request Reply*\n"
                        f"From: @{update.effective_user.username or update.effective_user.id}\n\n"
                        f"{update.message.text}"
                    ),
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"❌ Failed to forward promotion reply: {e}")
