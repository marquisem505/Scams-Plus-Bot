import logging
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application
from utils.constants import WEBHOOK_URL, PORT, BOT_TOKEN
from handlers.setup import setup_handlers
from db import init_db, create_user_if_not_exists

# --- Webhook Handler ---
async def telegram_webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, request.app["bot"])
        await request.app["app"].process_update(update)
        return web.Response(text="OK")
    except Exception as e:
        logging.exception("❌ Webhook error:")
        return web.Response(status=500, text=f"Error: {e}")

# --- Healthcheck Handler ---
async def healthcheck_handler(request):
    return web.Response(text="✅ Bot is alive!", status=200)

# --- Web Server Startup ---
async def run_webhook():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s - %(message)s'
    )

    init_db()

    # Init Telegram app
    app = Application.builder().token(BOT_TOKEN).build()
    setup_handlers(app)

    me = await app.bot.get_me()
    logging.info(f"🤖 Bot user @{me.username} added to DB with ID {me.id}")
    create_user_if_not_exists(me.id, me.username, me.first_name)

    await app.bot.set_webhook(WEBHOOK_URL)
    await app.initialize()

    # Setup aiohttp server
    web_app = web.Application()
    web_app["app"] = app
    web_app["bot"] = app.bot

    web_app.router.add_post("/telegram-webhook", telegram_webhook_handler)
    web_app.router.add_get("/healthcheck", healthcheck_handler)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logging.info("🚀 Webhook server started and listening...")
    await app.start()
    await asyncio.Event().wait()

# --- Entrypoint ---
if __name__ == "__main__":
    asyncio.run(run_webhook())