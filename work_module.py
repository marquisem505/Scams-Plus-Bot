# bender_module.py — persistent auto-polling for Bender API (PTB v21+)
import os, json, shlex, time
from typing import Dict, Any, Optional, List, Tuple
from aiohttp import ClientSession, ClientTimeout
import aiosqlite
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, Job

API_KEY = os.getenv("API_KEY", "").strip()
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "15"))

BALANCE_URL    = os.getenv("BALANCE_URL", "https://bender-search.ru/apiv1/check_balance").strip()
SEARCHDATA_URL = os.getenv("SEARCHDATA_URL", "https://bender-search.ru/apiv1/search_data").strip()
RESULT_URL     = os.getenv("RESULT_URL", "https://bender-search.ru/apiv1/result").strip()

DB_PATH = os.getenv("BENDER_DB", "bender_jobs.db")

_TIMEOUT = ClientTimeout(total=API_TIMEOUT)

PENDING_STATUSES = {"PENDING", "IN_PROGRESS", "PROCESSING", "QUEUED"}
POLL_INTERVALS = [5, 10, 20, 30, 60, 120]  # seconds, exponential-ish backoff

# ------------- DB -------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS pending_jobs (
            search_id   TEXT PRIMARY KEY,
            chat_id     INTEGER NOT NULL,
            created_at  INTEGER NOT NULL,
            last_check  INTEGER,
            attempt     INTEGER NOT NULL DEFAULT 0,
            status      TEXT,
            done        INTEGER NOT NULL DEFAULT 0
        );
        """)
        await db.commit()

async def db_add_pending(search_id: str, chat_id: int):
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO pending_jobs(search_id, chat_id, created_at, attempt, done) VALUES(?,?,?,?,0)",
            (search_id, chat_id, now, 0),
        )
        await db.commit()

async def db_mark_attempt(search_id: str, attempt: int, status: Optional[str]):
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE pending_jobs SET last_check=?, attempt=?, status=? WHERE search_id=?",
            (now, attempt, status, search_id),
        )
        await db.commit()

async def db_mark_done(search_id: str, status: Optional[str]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE pending_jobs SET done=1, status=? WHERE search_id=?",
            (status, search_id),
        )
        await db.commit()

async def db_get_pending() -> List[Tuple[str, int, int, int]]:
    """return list of (search_id, chat_id, attempt, created_at) for not-done rows"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT search_id, chat_id, attempt, created_at FROM pending_jobs WHERE done=0"
        )
        rows = await cur.fetchall()
        await cur.close()
        return rows

# ------------- HTTP helpers -------------
def _auth_headers() -> Dict[str, str]:
    if not API_KEY:
        raise RuntimeError("Missing API_KEY")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
    }

async def _post(url: str, *, form: Dict[str, Any] | None = None) -> Any:
    headers = _auth_headers()
    if form is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    async with ClientSession(timeout=_TIMEOUT) as s:
        async with s.post(url, headers=headers, data=form) as r:
            text = await r.text()
            try:
                return await r.json(content_type=None)
            except Exception:
                return {"status_code": r.status, "raw": text[:500]}

# ------------- Commands -------------
async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    try:
        res = await _post(BALANCE_URL)
        item = res[0] if isinstance(res, list) and res else res
        if not isinstance(item, dict):
            raise RuntimeError(f"Unexpected response: {str(res)[:200]}")
        status = str(item.get("status", "")).upper()
        balance = item.get("balance")
        msg = item.get("message", "")
        bal_str = str(balance)
        try: bal_str = f"{float(bal_str):.2f}"
        except: pass
        icon = "✅" if status == "SUCCESS" else ("⚠️" if status in ("REVIEW","PENDING") else "❌")
        await update.message.reply_text(f"{icon} Balance: {bal_str}\nStatus: {status}" + (f" — {msg}" if msg else ""))
    except Exception as e:
        await update.message.reply_text(f"Balance error: {type(e).__name__}: {e}")

def _extract_search_id(res: Any) -> Optional[str]:
    obj = res[0] if isinstance(res, list) and res else res if isinstance(res, dict) else None
    if not isinstance(obj, dict): return None
    for k in ("search_id", "id", "request_id", "ref"):
        v = obj.get(k)
        if v: return str(v)
    data = obj.get("data")
    if isinstance(data, dict):
        for k in ("search_id", "id", "request_id", "ref"):
            v = data.get(k)
            if v: return str(v)
    return None

def _status_from_result(res: Any) -> Optional[str]:
    obj = res[0] if isinstance(res, list) and res else res if isinstance(res, dict) else None
    if not isinstance(obj, dict): return None
    for k in ("status", "state", "result_status", "decision"):
        v = obj.get(k)
        if v: return str(v).upper()
    data = obj.get("data")
    if isinstance(data, dict):
        for k in ("status", "state", "result_status", "decision"):
            v = data.get(k)
            if v: return str(v).upper()
    return None

async def searchdata_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /searchdata firstname=John lastname=Doe dob=01/02/1990 address="123 Main St" city=Detroit state=MI zip=48235
    """
    m = update.message
    if not m: return

    text = m.text.partition(" ")[2]
    if not text:
        await m.reply_text("Usage: /searchdata key=value ...  (quote multi-word values)")
        return

    try:
        tokens = shlex.split(text)
    except Exception as e:
        await m.reply_text(f"Parse error: {e}")
        return

    form = {"search_type": 22}
    required = ["firstname", "lastname", "dob", "address", "city", "state", "zip"]
    for tok in tokens:
        if "=" in tok:
            k, v = tok.split("=", 1)
            form[k.strip()] = v.strip()

    missing = [k for k in required if not form.get(k)]
    if missing:
        await m.reply_text(f"Missing required keys: {', '.join(missing)}")
        return

    try:
        res = await _post(SEARCHDATA_URL, form=form)
        search_id = _extract_search_id(res)
        await m.reply_text(f"Submitted. search_id={search_id or 'N/A'}")
        if search_id:
            await db_add_pending(search_id, m.chat_id)
            # schedule first poll
            context.job_queue.run_once(
                poll_job,
                when=POLL_INTERVALS[0],
                data={"chat_id": m.chat_id, "search_id": search_id, "attempt": 0},
                name=f"poll:{search_id}",
            )
        else:
            await m.reply_text("ℹ️ No search_id found. Use /checkresult <id> manually.")
    except Exception as e:
        await m.reply_text(f"Search error: {type(e).__name__}: {e}")

async def checkresult_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /checkresult <search_id>")
        return
    form = {"search_id": context.args[0]}
    try:
        res = await _post(RESULT_URL, form=form)
        pretty = json.dumps(res, indent=2)
        if len(pretty) > 3800: pretty = pretty[:3800] + "\n… (truncated)"
        await update.message.reply_text(f"```{pretty}```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Result error: {type(e).__name__}: {e}")

# ------------- Polling Job -------------
async def poll_job(ctx: ContextTypes.DEFAULT_TYPE):
    job: Job = ctx.job
    data = job.data or {}
    chat_id = data["chat_id"]
    search_id = data["search_id"]
    attempt = data.get("attempt", 0)

    try:
        res = await _post(RESULT_URL, form={"search_id": search_id})
        status = _status_from_result(res) or ""
        await db_mark_attempt(search_id, attempt, status)

        if status not in PENDING_STATUSES and status:  # done
            pretty = json.dumps(res, indent=2)
            if len(pretty) > 3800: pretty = pretty[:3800] + "\n… (truncated)"
            await ctx.application.bot.send_message(
                chat_id, f"✅ Result ready for {search_id}:\n```{pretty}```", parse_mode="Markdown"
            )
            await db_mark_done(search_id, status)
            job.schedule_removal()
            return
    except Exception as e:
        # if final attempt, notify
        if attempt >= len(POLL_INTERVALS) - 1:
            await ctx.application.bot.send_message(
                chat_id, f"❌ Result check failed for {search_id}: {type(e).__name__}: {e}"
            )
            await db_mark_done(search_id, "ERROR")
            job.schedule_removal()
            return

    # reschedule if attempts left
    attempt += 1
    if attempt >= len(POLL_INTERVALS):
        await ctx.application.bot.send_message(
            chat_id, f"⚠️ Timed out waiting for {search_id}. Try /checkresult {search_id}."
        )
        await db_mark_done(search_id, "TIMEOUT")
        job.schedule_removal()
        return

    job.data["attempt"] = attempt
    delay = POLL_INTERVALS[attempt]
    job.run_once(poll_job, when=delay, data=job.data, name=job.name)

# ------------- Startup Resume -------------
async def bender_resume_pending(app: Application):
    rows = await db_get_pending()
    for search_id, chat_id, attempt, _created in rows:
        # clamp attempt to range
        attempt = max(0, min(attempt, len(POLL_INTERVALS) - 1))
        delay = POLL_INTERVALS[attempt]
        app.job_queue.run_once(
            poll_job,
            when=delay,
            data={"chat_id": chat_id, "search_id": search_id, "attempt": attempt},
            name=f"poll:{search_id}",
        )

# ------------- Registrar -------------
def register_bender_handlers(app: Application):
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("searchdata", searchdata_cmd))
    app.add_handler(CommandHandler("checkresult", checkresult_cmd))

async def bender_init(app: Application):
    """Call once on startup (before app.start) to init DB and resume pending jobs."""
    await init_db()
    await bender_resume_pending(app)