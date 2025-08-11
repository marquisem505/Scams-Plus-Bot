# bender_module.py — persistent auto-polling for Bender API (PTB v21+)
import os, json, shlex, time, math
from typing import Dict, Any, Optional, List, Tuple
from aiohttp import ClientSession, ClientTimeout
import aiosqlite
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, Job
from telegram.ext import ConversationHandler, MessageHandler, filters

API_KEY = os.getenv("API_KEY", "").strip()
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "15"))

BALANCE_URL       = os.getenv("BALANCE_URL", "https://bender-search.ru/apiv1/check_balance").strip()
AVAILABLE_BASE_URL= os.getenv("AVAILABLE_BASE_URL", "https://bender-search.ru/apiv1/aviable_base").strip()
SEARCHDATA_URL    = os.getenv("SEARCHDATA_URL", "https://bender-search.ru/apiv1/search_data").strip()
RESULT_URL        = os.getenv("RESULT_URL", "https://bender-search.ru/apiv1/result").strip()

DB_PATH = os.getenv("BENDER_DB", "bender_jobs.db")

_TIMEOUT = ClientTimeout(total=API_TIMEOUT)

PENDING_STATUSES = {"PENDING", "IN_PROGRESS", "PROCESSING", "QUEUED", "RUNNING", "WAITING"}
POLL_INTERVALS = [5, 10, 20, 30, 60, 120]  # seconds, exponential-ish backoff

# NEW: states for /lookup wizard
LOOKUP_CHOOSE_BASE, LOOKUP_ENTER_PARAMS = range(2)

# --- Scam's Plus Brand Styling ---
SP_HEADER = "🔥 Scam’s Plus Lookups"
SP_SUB    = "_Choose your lookup. Prices update live._"

# Base ID → (emoji, display name)
SP_BASE_COPY = {
    1:  ("💳", "SSN + DOB (ZIP)"),
    23: ("💳", "SSN + DOB (Nationwide)"),
    2:  ("📍", "SSN (ZIP)"),
    3:  ("🏙️", "SSN (City)"),
    4:  ("🗺️", "SSN (State)"),
    22: ("🪪", "Driver License"),
    100:("📄", "Credit Report (TU)"),
    102:("📄", "Credit Report (WalletHub)"),
    104:("👩‍👦", "Mother’s Maiden Name"),
    20: ("📊", "Consumer Snapshot"),
    10: ("💊", "DEA License"),
    11: ("🚗", "Advanced DL"),
    14: ("🎓", "Pro License"),
    15: ("🏢", "Business Profile"),
    16: ("🔍", "Reverse SSN"),
    29: ("🕵️", "Background + DOB"),
    24: ("📞", "Reverse Phone"),
    25: ("📧", "Reverse Email"),
    26: ("☎️", "Reverse Phone (Alt)"),
    27: ("🏠", "Reverse Address"),
    28: ("✏️", "Address Autocomplete"),
    61: ("❓", "Email Reputation"),
}

def _price_str(v) -> str:
    try:
        p = float(v)
        if p >= 1000:
            p = p / 100.0
        return f"${p:.2f}"
    except Exception:
        return str(v)

def _sp_line(item: dict) -> str:
    """Return emoji + lookup type + price, no ID."""
    bid = int(item.get("id", 0))
    emoji, label = SP_BASE_COPY.get(bid, ("🛠️", item.get("name", "")))
    return f"{emoji} {label} — {_price_str(item.get('price', '—'))}"

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

# ------------- Utils -------------
async def _send_long_markdown(chat_id: int, text: str, app: Application):
    """Split long markdown messages safely within Telegram 4096 char limit."""
    MAX = 3900  # leave headroom for code fences etc.
    if len(text) <= MAX:
        await app.bot.send_message(chat_id, text, parse_mode="Markdown")
        return
    chunks = math.ceil(len(text)/MAX)
    for i in range(chunks):
        part = text[i*MAX:(i+1)*MAX]
        # wrap each chunk in code fences if it looks like JSON
        if part.lstrip().startswith('{') or part.lstrip().startswith('['):
            part = f"```{part}```"
        await app.bot.send_message(chat_id, part, parse_mode="Markdown")

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

# ------------- Parsing helpers -------------
def _to_dict_like(res: Any) -> Optional[dict]:
    if isinstance(res, list) and res:
        return res[0] if isinstance(res[0], dict) else None
    if isinstance(res, dict):
        return res
    return None

def _extract_search_id(res: Any) -> Optional[str]:
    """
    API success example:
    { "status": "SUCCESS", "result": { "search_id": "100" }, "message": "Task created" }
    """
    obj = _to_dict_like(res)
    if not isinstance(obj, dict): return None
    # try common keys first
    for k in ("search_id", "id", "request_id", "ref"):
        v = obj.get(k)
        if v: return str(v)
    # check nested "result" then "data"
    for container in ("result", "data"):
        sub = obj.get(container)
        if isinstance(sub, dict):
            for k in ("search_id", "id", "request_id", "ref"):
                v = sub.get(k)
                if v: return str(v)
    return None

def _status_from_result(res: Any) -> Optional[str]:
    obj = _to_dict_like(res)
    if not isinstance(obj, dict): return None
    # top-level status
    for k in ("status", "state", "result_status", "decision"):
        v = obj.get(k)
        if v: return str(v).upper()
    # nested result/data
    for container in ("result", "data"):
        sub = obj.get(container)
        if isinstance(sub, dict):
            for k in ("status", "state", "result_status", "decision"):
                v = sub.get(k)
                if v: return str(v).upper()
    return None

# ------------- Commands -------------
async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    try:
        res = await _post(BALANCE_URL)
        item = _to_dict_like(res) or {}
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

# NEW: /mybalance alias
async def mybalance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await balance_cmd(update, context)

async def bases_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    try:
        res = await _post(AVAILABLE_BASE_URL)
        if isinstance(res, list) and res:
            lines = [SP_HEADER, SP_SUB, ""]
            for item in res:
                if isinstance(item, dict):
                    lines.append(_sp_line(item))
            await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        else:
            await update.message.reply_text(f"{SP_HEADER}\nNo lookups available.")
    except Exception as e:
        await update.message.reply_text(f"Bases error: {type(e).__name__}: {e}")

async def searchdata_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /searchdata search_type=22 firstname=John lastname=Doe dob=01/02/1990 address="123 Main St" city=Detroit state=MI zip=48235
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

    form: Dict[str, Any] = {}
    for tok in tokens:
        if "=" in tok:
            k, v = tok.split("=", 1)
            form[k.strip()] = v.strip()

    # default search_type if not provided (you can change this)
    form.setdefault("search_type", 22)

    try:
        res = await _post(SEARCHDATA_URL, form=form)
        search_id = _extract_search_id(res)
        status = _status_from_result(res) or "UNKNOWN"
        await m.reply_text(f"Submitted. status={status} search_id={search_id or 'N/A'}")
        if search_id:
            await db_add_pending(search_id, m.chat_id)
            # schedule first poll (use ctx.job_queue, NOT job.run_once)
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
        if len(pretty) > 3900: pretty = pretty[:3900] + "\n… (truncated)"
        await update.message.reply_text(f"```{pretty}```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Result error: {type(e).__name__}: {e}")

# ------------- /lookup wizard helpers & handlers -------------
def _format_bases(res: Any) -> str:
    if not isinstance(res, list) or not res:
        return f"{SP_HEADER}\nNo lookups available."
    lines = [SP_HEADER, SP_SUB, ""]
    for item in res:
        if isinstance(item, dict):
            lines.append(_sp_line(item))
    lines.append("\nReply with the *lookup type* exactly as shown above.")
    return "\n".join(lines)

async def _get_bases() -> List[Dict[str, Any]]:
    res = await _post(AVAILABLE_BASE_URL)
    return res if isinstance(res, list) else []

async def lookup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return ConversationHandler.END
    try:
        bases = await _get_bases()
        context.user_data["lookup"] = {"bases": bases}
        await update.message.reply_text(_format_bases(bases), parse_mode="Markdown")
        return LOOKUP_CHOOSE_BASE
    except Exception as e:
        await update.message.reply_text(f"Lookup start error: {type(e).__name__}: {e}")
        return ConversationHandler.END

async def lookup_choose_base(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return ConversationHandler.END
    choice = (update.message.text or "").strip()
    if not choice.isdigit():
        await update.message.reply_text("Please send a numeric base *ID*.", parse_mode="Markdown")
        return LOOKUP_CHOOSE_BASE

    bases = context.user_data.get("lookup", {}).get("bases", [])
    choice_lower = (update.message.text or "").strip().lower()
    base = None
    for b in bases:
        if not isinstance(b, dict):
            continue
        bid = int(b.get("id"))
        emoji, label = SP_BASE_COPY.get(bid, ("", b.get("name", "")))
        if choice_lower == label.lower():
            base = b
            break

if not base:
    await update.message.reply_text("Not found. Send the exact lookup type from the list above.")
    return LOOKUP_CHOOSE_BASE

    context.user_data["lookup"]["base_id"] = int(choice)
    context.user_data["lookup"]["base_name"] = base.get("name", "Unknown")

    guide = (
        f"Chosen base: *{base.get('name','Unknown')}* (ID {choice}).\n\n"
        "Now send your parameters as `key=value` pairs separated by spaces.\n"
        "Use quotes for multi-word values. Examples:\n"
        "`firstname=John lastname=Doe dob=01/02/1990 zip=48235`\n"
        "`address=\"123 Main St\" city=Detroit state=MI`\n\n"
        "When ready, send your line. Send /cancel to abort."
    )
    await update.message.reply_text(guide, parse_mode="Markdown")
    return LOOKUP_ENTER_PARAMS

async def lookup_enter_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return ConversationHandler.END

    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("Please send parameters or /cancel.")
        return LOOKUP_ENTER_PARAMS

    try:
        tokens = shlex.split(text)
    except Exception as e:
        await update.message.reply_text(f"Parse error: {e}\nTry again or /cancel.")
        return LOOKUP_ENTER_PARAMS

    form: Dict[str, Any] = {}
    for tok in tokens:
        if "=" in tok:
            k, v = tok.split("=", 1)
            if k.strip():
                form[k.strip()] = v.strip()

    if not form:
        await update.message.reply_text("No key=value pairs found. Try again or /cancel.")
        return LOOKUP_ENTER_PARAMS

    base_id = context.user_data.get("lookup", {}).get("base_id")
    form.setdefault("search_type", base_id if base_id is not None else 22)

    try:
        res = await _post(SEARCHDATA_URL, form=form)
        search_id = _extract_search_id(res)
        status = _status_from_result(res) or "UNKNOWN"
        pretty = json.dumps(res, indent=2)
        msg = f"Submitted ✅\nstatus={status}\nsearch_id={search_id or 'N/A'}\n```{pretty[:1800]}```"
        await update.message.reply_text(msg, parse_mode="Markdown")

        if search_id:
            await db_add_pending(search_id, update.effective_chat.id)
            context.job_queue.run_once(
                poll_job,
                when=POLL_INTERVALS[0],
                data={"chat_id": update.effective_chat.id, "search_id": search_id, "attempt": 0},
                name=f"poll:{search_id}",
            )
        else:
            await update.message.reply_text("ℹ️ No search_id found. Use /checkresult <id> manually.")
    except Exception as e:
        await update.message.reply_text(f"Search error: {type(e).__name__}: {e}")

    context.user_data.pop("lookup", None)
    return ConversationHandler.END

async def lookup_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("lookup", None)
    if update.message:
        await update.message.reply_text("Lookup cancelled.")
    return ConversationHandler.END

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

        if status and status not in PENDING_STATUSES:  # done
            pretty = json.dumps(res, indent=2)
            msg = f"✅ Result ready for {search_id}:\n```{pretty}```"
            if len(msg) <= 3900:
                await ctx.application.bot.send_message(chat_id, msg, parse_mode="Markdown")
            else:
                await ctx.application.bot.send_message(chat_id, "✅ Result ready (split):")
                await _send_long_markdown(chat_id, pretty, ctx.application)
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

    # IMPORTANT: schedule via ctx.job_queue (not job.run_once)
    delay = POLL_INTERVALS[attempt]
    new_data = {"chat_id": chat_id, "search_id": search_id, "attempt": attempt}
    ctx.job_queue.run_once(poll_job, when=delay, data=new_data, name=job.name)

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
    app.add_handler(CommandHandler("mybalance", mybalance_cmd))  # alias
    app.add_handler(CommandHandler("bases", bases_cmd))
    app.add_handler(CommandHandler("searchdata", searchdata_cmd))
    app.add_handler(CommandHandler("checkresult", checkresult_cmd))

    # /lookup wizard
    lookup_conv = ConversationHandler(
        entry_points=[CommandHandler("lookup", lookup_start)],
        states={
            LOOKUP_CHOOSE_BASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lookup_choose_base)],
            LOOKUP_ENTER_PARAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, lookup_enter_params)],
        },
        fallbacks=[CommandHandler("cancel", lookup_cancel)],
        conversation_timeout=300,  # 5 minutes
        name="lookup_wizard",
        persistent=False,
    )
    app.add_handler(lookup_conv)

async def bender_init(app: Application):
    """Call once on startup (before app.start) to init DB and resume pending jobs."""
    await init_db()
    await bender_resume_pending(app)