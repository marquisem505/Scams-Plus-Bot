# bot.py

import os
import asyncio
import logging
from aiohttp import web
from dotenv import load_dotenv
from telegram.ext import Application
from utils.constants import BOT_TOKEN, PORT, IS_DEV_MODE, WEBHOOK_URL, GROUP_ID
from db import init_db, create_user_if_not_exists
from handlers.setup import setup_handlers
from web.webhook import telegram_webhook_handler, healthcheck_handler, setup_routes

# --- Load ENV ---
load_dotenv()

# --- Logging ---
logging.basicConfig(
    filename="scamsclub_bot.log",
    filemode="a",
    format="[%(asctime)s] %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- Main async ---
async def main():
    if IS_DEV_MODE:
        logging.info("🧪 DEV MODE ENABLED")

    logging.info("🔧 Initializing bot...")
    app = Application.builder().token(BOT_TOKEN).build()

    # Register command/message/callback handlers
    setup_handlers(app)

    # Store Telegram bot info
    me = await app.bot.get_me()
    create_user_if_not_exists(me.id, me.username, me.first_name)
    logging.info(f"🤖 Logged in as @{me.username} (ID: {me.id})")

    # --- Webhook Setup ---
    webhook_path = "/telegram-webhook"
    await app.bot.set_webhook(url=f"{WEBHOOK_URL}{webhook_path}")
    logging.info(f"🌐 Webhook set to {WEBHOOK_URL}{webhook_path}")

    # --- Aiohttp Web Server ---
    web_app = web.Application()
    web_app["bot_app"] = app
    web_app.router.add_post(webhook_path, telegram_webhook_handler)
    web_app.router.add_get("/healthcheck", healthcheck_handler)

    # --- Final Start ---
    await app.initialize()
    await app.start()
    logging.info("✅ Bot started via webhook (Railway)")
    web.run_app(web_app, port=PORT)

# --- Run ---
if __name__ == "__main__":
    init_db()
    asyncio.run(main())