# --- Imports ---
import os
import logging
import asyncio
from dotenv import load_dotenv
from db import init_db
from web.webhook import telegram_webhook_handler, healthcheck_handler
from telegram.ext import Application
from utils.constants import BOT_TOKEN, IS_DEV_MODE
from handlers.setup import setup_handlers

# --- Load ENV --- 
load_dotenv()

# --- Logging ---
logging.basicConfig(
    filename="scamsclub_bot.log",
    filemode="a",
    format="[%(asctime)s] %(levelname)s - %(message)s",
    level=logging.INFO
)
# --- Main Function ---
async def main():
    if IS_DEV_MODE:
        logging.info("🧪 DEV MODE: Verbose logs enabled")

    logging.info("✅ Loading bot and building application...")
# --- Application ---
    app = Application.builder().token(BOT_TOKEN).build()

# Register handlers
    setup_handlers(app)

# --- Bot to DB ---
    from db import create_user_if_not_exists
    me = await app.bot.get_me()
    create_user_if_not_exists(me.id, me.username, me.first_name)
    logging.info(f"🤖 Logged in as @{me.username} (ID: {me.id})")
# --- Start Polling ---
    await app.initialize()
    await app.start()
    logging.info("🚀 Bot started and polling...")
    await asyncio.Event().wait()
# --- Run ---
if __name__ == "__main__":
    logging.info("🧪 Starting main()...")
    init_db()
    asyncio.run(main())