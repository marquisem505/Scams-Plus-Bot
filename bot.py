# --- Imports ---
import os
import logging
import asyncio
from dotenv import load_dotenv
from aiohttp import web
from db import init_db, create_user_if_not_exists
from telegram.ext import Application
from utils.constants import BOT_TOKEN, IS_DEV_MODE, PORT
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
    app = Application.builder().token(BOT_TOKEN).build()

    # Register bot handlers
    setup_handlers(app)

    # Save bot identity to DB
    me = await app.bot.get_me()
    create_user_if_not_exists(me.id, me.username, me.first_name)
    logging.info(f"🤖 Logged in as @{me.username} (ID: {me.id})")

    await app.initialize()
    await app.start()

    if IS_DEV_MODE:
        logging.info("🚀 Dev Mode: Bot running in polling mode...")
        await asyncio.Event().wait()
    else:
        logging.info("🚀 Prod Mode: Bot running with webhook...")
        web_app = build_web_app(app)
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()

# --- Run ---
if __name__ == "__main__":
    logging.info("🧪 Starting main()...")
    init_db()
    asyncio.run(main())