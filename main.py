import asyncio
import logging
from db import init_db
from handlers.setup import setup_handlers
from web.webhook import webhook_handler, healthcheck_handler
from telegram.ext import Application
from utils.constants import BOT_TOKEN, IS_DEV_MODE

async def main():
    if IS_DEV_MODE:
        logging.info("🧪 DEV MODE: Verbose logs enabled")

    logging.info("✅ Loading bot and building application...")
    app = Application.builder().token(BOT_TOKEN).build()

    # Setup bot info
    me = await app.bot.get_me()
    logging.info(f"🤖 Bot user @{me.username} added to DB with ID {me.id}")
    from db import create_user_if_not_exists
    create_user_if_not_exists(me.id, me.username, me.first_name)

    # Register handlers
    setup_handlers(app)

    await app.initialize()
    await app.start()
    logging.info("🚀 Bot started and polling...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    logging.info("🧪 Starting main()...")
    init_db()
    asyncio.run(main())