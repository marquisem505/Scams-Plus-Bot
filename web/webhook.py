# web/webhook.py

import logging
from aiohttp import web
from telegram import Update

# --- Telegram Webhook Handler ---
async def telegram_webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, request.app["bot"])
        await request.app["bot_app"].process_update(update)
        return web.Response(text="OK")
    except Exception as e:
        logging.error("❌ Webhook error: %s", str(e))
        return web.Response(status=500, text=f"Error: {e}")

# --- Healthcheck Route ---
async def healthcheck_handler(request):
    return web.Response(text="✅ Bot is alive!", status=200)