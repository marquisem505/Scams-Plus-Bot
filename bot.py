import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ChatMemberHandler, CallbackQueryHandler,
    ContextTypes
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

logging.basicConfig(level=logging.INFO)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "starter_pack":
        await query.edit_message_text(
            "📦 **Starter Pack:**\n- Refund Guide\n- OTP Bot APK\n- Spoofer Tool\n\nRespect the rank system. No spoon-feeding."
        )
    elif data == "info":
        await query.edit_message_text(
            "📚 **What’s Inside:**\n\n🧠 Con Academy – Learn drops\n🛠 Tools & Bots – Installers\n📋 Verified Guides – Step-by-step\n🧪 Testing Lab – Try drops\n🪩 VIP Lounge – Ranked access only"
        )
    elif data == "rules":
        await query.edit_message_text(
            "🚫 **Rules:**\n- Don’t ask for free sauce\n- Use the right topics\n- Don’t leak\n- Don’t post unverified drops\n- Respect your rank or get bounced"
        )

async def member_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if result.new_chat_member.status == "member" and result.chat.id == GROUP_ID:
        user = result.new_chat_member.user
        username = f"@{user.username}" if user.username else user.full_name

        welcome_text = (
            f"🔥 Welcome {username} — you just entered **Scam’s Club Plus**\n\n"
            "🔰 You start as a **Lookout**\n"
            "👑 Climb to Runner, Closer, Inner Circle, OG\n\n"
            "👇 Use the buttons below to begin:"
        )

        buttons = [
            [InlineKeyboardButton("💼 Get Starter Pack", callback_data="starter_pack")],
            [InlineKeyboardButton("📚 What’s Inside", callback_data="info")],
            [InlineKeyboardButton("🚫 Rules", callback_data="rules")],
            [InlineKeyboardButton("💬 Introduce Yourself", url="https://t.me/c/2019911042/1234")]
        ]

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=welcome_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(ChatMemberHandler(member_joined, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()

if __name__ == "__main__":
    main()