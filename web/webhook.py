# web/webhook.py

import logging
from aiohttp import web
from telegram import Update

async def telegram_webhook_handler(request):
    try:
        data = await request.json()
        logging.info("📥 Incoming Telegram webhook: %s", data)

        bot = request.app["bot"]
        app = request.app["bot_app"]
        update = Update.de_json(data, bot)
        await app.process_update(update)
        return web.Response(text="OK")
    except Exception as e:
        logging.exception("❌ Webhook error")
        return web.Response(status=500, text=f"Error: {e}")

async def healthcheck_handler(request):
    return web.Response(text="✅ Bot is alive", status=200)