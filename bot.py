# --- Imports ---
import os
import asyncio
import logging
from dotenv import load_dotenv
from aiohttp import web
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    ChatJoinRequestHandler,
    ContextTypes,
    filters
)

# --- Local Modules ---
from db import init_db, create_user_if_not_exists
from utils.constants import BOT_TOKEN, WEBHOOK_URL, PORT
from utils.helpers import delete_old_messages, store_message_id

from handlers.logs import view_logs
from handlers.status import status_command
from handlers.general import start_command, menu_handler
from handlers.admin import admin_panel, handle_admin_dm, logout_command
from handlers.onboarding import chat_member_update, new_chat_member_message, button_handler, handle_join
from handlers.rank import assign_rank, promoteme, reply_forwarder, demote, myrank, topic_guard, promoteme_button_handler

# --- Logging Setup ---
logging.basicConfig(
    filename='scamsclub_bot.log',
    filemode='a',
    format='[%(asctime)s] %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Webhook Health Check ---
async def healthcheck(request):
    return web.Response(text="✅ Bot is alive!", status=200)

# --- Main App ---
async def main():
    print("✅ Scam's Club bot is starting...")

    app = Application.builder().token(BOT_TOKEN).build()
    await app.bot.set_webhook(WEBHOOK_URL)
    logging.info("Bot started successfully.")

    # Register bot ID if not in DB
    me = await app.bot.get_me()
    create_user_if_not_exists(me.id, me.username, me.first_name)

    # --- Bot Commands ---
    await app.bot.set_my_commands([
        BotCommand("start", "Show onboarding menu"),
        BotCommand("status", "Check bot health"),
        BotCommand("promoteme", "Request a rank promotion"),
        BotCommand("assignrank", "Assign a rank to a user"),
        BotCommand("demote", "Demote a user to Lookout"),
        BotCommand("myrank", "See your current rank"),
        BotCommand("logs", "View recent bot logs"),
        BotCommand("admin", "Open the admin panel"),
        BotCommand("logout", "Log out of the admin panel"),
    ])

    # --- Command Handlers ---
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("logout", logout_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("assignrank", assign_rank))
    app.add_handler(CommandHandler("demote", demote))
    app.add_handler(CommandHandler("myrank", myrank))
    app.add_handler(CommandHandler("promoteme", promoteme))
    app.add_handler(CommandHandler("logs", view_logs))

    # --- Admin DMs ---
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_admin_dm), group=0)

    # --- Private Menu Button Logic ---
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, menu_handler), group=1)

    # --- New Member Join / Auto Rank ---
    app.add_handler(ChatJoinRequestHandler(handle_join))
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member_message))

    # --- Message Reply Forwarder (Promotion Request Replies) ---
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, reply_forwarder))

    # --- Topic Guard (Anti-spam in restricted threads) ---
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), topic_guard))

    # --- Callback Query (Onboarding Buttons) ---
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(promoteme_button_handler, pattern="^promoteme$"))

    # --- Web Server Setup ---
    async def telegram_webhook(request):
        try:
            data = await request.json()
            update = Update.de_json(data, app.bot)
            await app.process_update(update)
            return web.Response(text="OK")
        except Exception as e:
            logging.error(f"Webhook Error: {e}")
            return web.Response(status=500, text=f"Error: {e}")

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

# --- Run ---
if __name__ == "__main__":
    init_db()
    asyncio.run(main())