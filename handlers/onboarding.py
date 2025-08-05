from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMemberUpdated
from telegram.ext import ContextTypes
from db import create_user_if_not_exists, update_onboarding, get_user_rank, set_user_rank, get_onboarding_summary
from utils.constants import GROUP_ID
import logging

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

# --- Button Logic ---
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

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