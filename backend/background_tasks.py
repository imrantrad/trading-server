"""
TRD v12.3 — Background Task System
Provides: Scheduled jobs, async workers, health monitoring
"""
import threading, time, logging
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))
logger = logging.getLogger("trd.background")

_tasks = {}
_running = True

def schedule(name: str, interval_s: int, fn, *args):
    """Register a background task"""
    def _worker():
        while _running:
            try:
                fn(*args)
            except Exception as e:
                logger.error(f"Task {name} failed: {e}")
            time.sleep(interval_s)
    
    t = threading.Thread(target=_worker, name=f"trd-{name}", daemon=True)
    _tasks[name] = {"thread": t, "interval": interval_s, "last_run": None}
    t.start()
    logger.info(f"Background task '{name}' started (every {interval_s}s)")

def cleanup_rate_store():
    """Clean expired rate limit buckets"""
    try:
        from middleware import _rate_store
        now = time.time()
        keys_to_del = [k for k,v in list(_rate_store.items()) if all(now-t>120 for t in v)]
        for k in keys_to_del: del _rate_store[k]
    except Exception:
        pass

def cleanup_cache():
    """Clean expired cache entries"""
    try:
        from cache_layer import cache
        now = time.time()
        with cache._lock:
            expired = [k for k,v in cache._store.items() if v["expires"] and now > v["expires"]]
            for k in expired: del cache._store[k]
    except Exception:
        pass

def rotate_logs():
    """Keep only last 7 days of logs"""
    try:
        import os, glob
        log_dir = os.path.join(os.path.dirname(__file__), "../logs")
        logs = sorted(glob.glob(os.path.join(log_dir, "trd_*.jsonl")))
        while len(logs) > 7:
            os.remove(logs.pop(0))
    except Exception:
        pass

def start_background_tasks():
    """Start all background workers"""
    schedule("rate_store_cleanup", 120,  cleanup_rate_store)
    schedule("cache_cleanup",      300,  cleanup_cache)
    schedule("log_rotation",       3600, rotate_logs)
    logger.info("All background tasks started")

print("✅ background_tasks.py created")
