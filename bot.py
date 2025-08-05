# bot.py
import os
import logging
import asyncio
from dotenv import load_dotenv
from db import init_db
from main import main

# --- Load ENV ---
load_dotenv()

# --- Logging ---
logging.basicConfig(
    filename="scamsclub_bot.log",
    filemode="a",
    format="[%(asctime)s] %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- Start ---
if __name__ == "__main__":
    logging.info("🧪 Starting main()...")
    init_db()
    asyncio.run(main())