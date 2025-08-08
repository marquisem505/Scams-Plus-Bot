import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.constants import GROUP_ID, ADMIN_ID
from utils.helpers import delete_old_messages, store_message_id
from db import (
    create_user_if_not_exists,
    set_user_rank,
    update_onboarding,
    get_onboarding_summary,
    get_user_rank
)

# --- Auto Rank Members On Join ---
async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member.new_chat_member
    if member.status == "member":
        user = member.user
        create_user_if_not_exists(user.id, user.username, user.first_name)
        set_user_rank(user.id, "Lookout")

        await context.bot.send_message(
            chat_id=user.id,
            text="Welcome to Scam's Plus! You've been assigned the rank: Lookout."
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"👤 {user.first_name} (@{user.username or 'NoUsername'}) just joined "
                "and was auto-ranked to Lookout."
            )
        )

# --- Welcome Message (for non-chat_member updates) ---
async def new_chat_member_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Start Onboarding", callback_data="start_onboarding")],
            [InlineKeyboardButton("📚 Group Rules", url="https://t.me/ScamsClubRules")],
            [InlineKeyboardButton("❓ Need Help?", callback_data="help")]
        ])
        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"👋 Welcome {member.mention_html()} to Scam’s Plus!\n\n"
                "Everything here is structured, ranked, and protected.\n\n"
                "Press a button below to get started 👇"
            ),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        store_message_id(context, update.effective_chat.id, msg.message_id)

# --- Forum-style ChatMemberHandler welcome ---
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
        msg = await context.bot.send_message(
            chat_id=GROUP_ID,
            text=(
                f"👋 Welcome {member.mention_html()} to Scam’s Plus!\n\n"
                "Press a button below to get started 👇"
            ),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        store_message_id(context, GROUP_ID, msg.message_id)

# --- Inline Onboarding Button Flow ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    await delete_old_messages(context, chat_id)

    if query.data == "start_onboarding":
        msg = await query.message.reply_text(
            "🧠 Let’s get you set up.\n\nWhat do you want to do first?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 Drops & Methods", callback_data="learn_drops")],
                [InlineKeyboardButton("🛠 Tools & Bots", callback_data="learn_tools")],
                [InlineKeyboardButton("🔗 Collab With Vendors", callback_data="learn_vendors")],
                [InlineKeyboardButton("🧑‍🎓 Get Mentorship?", callback_data="learn_mentorship")],
                [InlineKeyboardButton("🙋 Ask Questions?", callback_data="learn_questions")],
                [InlineKeyboardButton("🥇 VIP Lounge Info", callback_data="learn_vip")],
                [InlineKeyboardButton("❓ Not Sure Yet", callback_data="learn_unsure")]
            ])
        )
        store_message_id(context, chat_id, msg.message_id)

    elif query.data == "help":
        msg = await query.message.reply_text("👤 DM @ScamsClub_Store for help.")
        store_message_id(context, chat_id, msg.message_id)

    elif query.data.startswith("learn_"):
        choice = query.data.replace("learn_", "")
        create_user_if_not_exists(user_id, query.from_user.username, query.from_user.first_name)
        update_onboarding(user_id, learning_path=choice)

        response_map = {
            "drops":      "🔥 Check `Verified Guides` & `Con Academy`.",
            "tools":      "🛠 See the `Tools & Bots` thread.",
            "mentorship": "🧑‍🎓 A mentor will reach out via `Con Academy`.",
            "vip":        "🥇 See `VIP Lounge` for details.",
            "questions":  "🙋 Head to `Questions` for help.",
            "vendors":    "🔗 See `Verified Vendors / Collabs`.",
            "unsure":     "💡 Lurk in `Start Here` to get oriented."
        }

        msg1 = await query.message.reply_text(response_map[choice])
        msg2 = await query.message.reply_text(
            "🧠 Your experience level?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Beginner", callback_data="exp_beginner")],
                [InlineKeyboardButton("💻 Intermediate", callback_data="exp_intermediate")],
                [InlineKeyboardButton("🥇 Advanced", callback_data="exp_advanced")]
            ])
        )
        store_message_id(context, chat_id, msg1.message_id)
        store_message_id(context, chat_id, msg2.message_id)

    elif query.data.startswith("exp_"):
        level = query.data.replace("exp_", "")
        update_onboarding(user_id, experience=level)
        msg = await query.message.reply_text(
            "🔍 What are you looking for?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏦 Refunds", callback_data="target_refunds")],
                [InlineKeyboardButton("💳 CC/Fullz", callback_data="target_cards")],
                [InlineKeyboardButton("📲 Spoofing & OTPs", callback_data="target_otp")],
                [InlineKeyboardButton("🧑‍💻 Automations", callback_data="target_auto")],
                [InlineKeyboardButton("📚 Just Exploring", callback_data="target_general")]
            ])
        )
        store_message_id(context, chat_id, msg.message_id)

    elif query.data.startswith("target_"):
        focus = query.data.replace("target_", "")
        update_onboarding(user_id, interest=focus)
        summary = get_onboarding_summary(user_id)
        msg = await query.message.reply_text(
            f"✅ All set!\n\n"
            f"👤 {summary['first_name']} (@{summary['username']})\n"
            f"🧠 Goal: `{summary['learning_path']}`\n"
            f"📈 Exp: `{summary['experience']}`\n"
            f"🎯 Focus: `{summary['interest']}`\n\n"
            "👉 Tag a mentor if you’re stuck.",
            parse_mode="Markdown"
        )
        store_message_id(context, chat_id, msg.message_id)

    elif query.data == "check_rank":
        rank = get_user_rank(user_id) or "Unranked"
        msg = await query.message.reply_text(f"🏷 Your rank: `{rank}`", parse_mode="Markdown")
        store_message_id(context, chat_id, msg.message_id)