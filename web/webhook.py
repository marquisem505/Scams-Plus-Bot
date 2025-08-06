import os
import asyncio
import logging
from aiohttp import web
from dotenv import load_dotenv
from telegram.ext import Application
from utils.constants import BOT_TOKEN, PORT, IS_DEV_MODE, WEBHOOK_URL, GROUP_ID
from db import init_db, create_user_if_not_exists
from handlers.setup import setup_handlers
from web.webhook import telegram_webhook_handler, healthcheck_handler

# --- Load ENV ---
load_dotenv()

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,  
    format='[%(asctime)s] %(levelname)s - %(message)s',
    filename='scamsclub_bot.log',
    filemode='a'
)

# --- Main async ---
async def main():
    if IS_DEV_MODE:
        logging.info("🧪 DEV MODE ENABLED")

    logging.info("🔧 Initializing bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    setup_handlers(app)

    me = await app.bot.get_me()
    create_user_if_not_exists(me.id, me.username, me.first_name)
    logging.info(f"🤖 Logged in as @{me.username} (ID: {me.id})")

    # Set webhook
    webhook_path = "/telegram-webhook"
    await app.bot.set_webhook(WEBHOOK_URL + webhook_path)
    await app.initialize()

    # Setup aiohttp app
    web_app = web.Application()
    web_app["bot_app"] = app
    web_app["bot"] = app.bot
    web_app.router.add_post(webhook_path, telegram_webhook_handler)
    web_app.router.add_get("/healthcheck", healthcheck_handler)

    # Start aiohttp site
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()

    # Start the bot
    await app.start()
    logging.info(f"🚀 Webhook server started at {WEBHOOK_URL}{webhook_path}")
    await asyncio.Event().wait()  # Keep running

# --- Run ---
if __name__ == "__main__":
    init_db()
    asyncio.run(main())