# credits_module.py  (PTB v21+)
import os, aiosqlite
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

CREDITS_DB = os.getenv("CREDITS_DB", "credits.db")
LOOKUP_COST = int(os.getenv("LOOKUP_COST", "1"))   # credits per /searchdata

# --- DB bootstrap ---
async def credits_init():
    async with aiosqlite.connect(CREDITS_DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_credits (
            user_id   INTEGER PRIMARY KEY,
            username  TEXT,
            credits   INTEGER NOT NULL DEFAULT 0
        )""")
        await db.commit()

# --- helpers ---
async def get_credits(user_id: int) -> int:
    async with aiosqlite.connect(CREDITS_DB) as db:
        cur = await db.execute("SELECT credits FROM user_credits WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return int(row[0]) if row else 0

async def add_credits(user_id: int, username: str | None, amount: int) -> int:
    async with aiosqlite.connect(CREDITS_DB) as db:
        await db.execute(
            "INSERT INTO user_credits(user_id,username,credits) VALUES(?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET credits = credits + excluded.credits, username=excluded.username",
            (user_id, username, amount),
        )
        await db.commit()
    return await get_credits(user_id)

async def charge_credits(user_id: int, amount: int) -> bool:
    async with aiosqlite.connect(CREDITS_DB) as db:
        cur = await db.execute("SELECT credits FROM user_credits WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        have = int(row[0]) if row else 0
        if have < amount:
            return False
        await db.execute("UPDATE user_credits SET credits = credits - ? WHERE user_id=?", (amount, user_id))
        await db.commit()
        return True

# --- commands ---
async def mybalance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    uid = update.effective_user.id
    bal = await get_credits(uid)
    cost = LOOKUP_COST
    await update.message.reply_text(f"Your credits: {bal}\nLookup cost: {cost} credit(s).")

# Admin: /credit <@user|user_id> <amount>
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
async def credit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Not authorized.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /credit <@username|user_id> <amount>")
        return
    target, amount_s = context.args
    try:
        amount = int(amount_s)
    except:
        await update.message.reply_text("Amount must be an integer.")
        return

    # Resolve user_id if @username is given (fallback to numeric)
    user_id = None
    if target.startswith("@"):
        # If the user has chatted with the bot, you can map usernames via your own user DB.
        # Minimal fallback: ask admin to use numeric ID.
        await update.message.reply_text("Use numeric user_id for now (username resolution not implemented).")
        return
    else:
        try:
            user_id = int(target)
        except:
            await update.message.reply_text("Invalid user identifier.")
            return

    new_bal = await add_credits(user_id, None, amount)
    await update.message.reply_text(f"Credited {amount}. New balance for {user_id}: {new_bal}")

def register_credits_handlers(app: Application):
    app.add_handler(CommandHandler("mybalance", mybalance_cmd))
    app.add_handler(CommandHandler("credit", credit_cmd))