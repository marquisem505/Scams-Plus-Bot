# utils/time.py

import time
from datetime import datetime

def now_ts() -> int:
    """Return current Unix timestamp."""
    return int(time.time())

def readable_time(ts: int) -> str:
    """Format timestamp into human-readable datetime string."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")