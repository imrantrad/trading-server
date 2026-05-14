"""
TRD v12.3 — Institutional Middleware Layer
Provides: Audit Logging, Request Tracking, Rate Limiting, 
          Error Handling, Structured Logging, Health Monitoring
"""
import time, uuid, json, logging, traceback, hashlib, os
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse

IST = timezone(timedelta(hours=5, minutes=30))

# ══════════════════════════════════════════════════════════
# STRUCTURED LOGGING
# ══════════════════════════════════════════════════════════
LOG_DIR = os.path.join(os.path.dirname(__file__), "../logs")
os.makedirs(LOG_DIR, exist_ok=True)

def _json_log(level: str, event: str, **kwargs):
    """Write structured JSON log"""
    entry = {
        "ts":    datetime.now(IST).isoformat(),
        "level": level,
        "event": event,
        **kwargs
    }
    try:
        log_file = os.path.join(LOG_DIR, f"trd_{datetime.now(IST).strftime('%Y%m%d')}.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass
    return entry

def log_info(event: str, **kw):  return _json_log("INFO",  event, **kw)
def log_warn(event: str, **kw):  return _json_log("WARN",  event, **kw)
def log_error(event: str, **kw): return _json_log("ERROR", event, **kw)
def log_audit(event: str, **kw): return _json_log("AUDIT", event, **kw)

# ══════════════════════════════════════════════════════════
# AUDIT LOG SYSTEM (append-only, tamper-evident)
# ══════════════════════════════════════════════════════════
import sqlite3 as _sq3

AUDIT_DB = os.path.join(os.path.dirname(__file__), "../database/audit.db")

def _audit_conn():
    c = _sq3.connect(AUDIT_DB)
    c.row_factory = _sq3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id    TEXT UNIQUE NOT NULL,
        ts          TEXT NOT NULL,
        user_id     TEXT DEFAULT '',
        action      TEXT NOT NULL,
        resource    TEXT DEFAULT '',
        details     TEXT DEFAULT '{}',
        ip_address  TEXT DEFAULT '',
        request_id  TEXT DEFAULT '',
        hash_chain  TEXT DEFAULT '',
        status      TEXT DEFAULT 'OK'
    )""")
    c.commit()
    return c

def audit_log(user_id: str, action: str, resource: str = "", 
              details: dict = None, ip: str = "", req_id: str = "", status: str = "OK"):
    """Append-only audit log with hash chain for tamper detection"""
    try:
        event_id = str(uuid.uuid4())
        ts       = datetime.now(IST).isoformat()
        det_str  = json.dumps(details or {}, default=str)
        
        # Hash chain: each entry includes hash of previous
        with _audit_conn() as c:
            last = c.execute("SELECT hash_chain FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
            prev_hash = last["hash_chain"] if last else "GENESIS"
            raw = f"{event_id}{ts}{user_id}{action}{det_str}{prev_hash}"
            chain_hash = hashlib.sha256(raw.encode()).hexdigest()[:32]
            
            c.execute("""INSERT INTO audit_log 
                (event_id,ts,user_id,action,resource,details,ip_address,request_id,hash_chain,status)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (event_id, ts, user_id, action, resource, det_str, ip, req_id, chain_hash, status))
            c.commit()
        return event_id
    except Exception as e:
        log_error("audit_log_failed", error=str(e))
        return None

def get_audit_log(user_id: str = None, limit: int = 100) -> list:
    """Read audit log — admin only"""
    with _audit_conn() as c:
        if user_id:
            rows = c.execute("SELECT * FROM audit_log WHERE user_id=? ORDER BY id DESC LIMIT ?",
                           (user_id, limit)).fetchall()
        else:
            rows = c.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", 
                           (limit,)).fetchall()
    return [dict(r) for r in rows]

# ══════════════════════════════════════════════════════════
# RATE LIMITER (in-memory, per IP + per user)
# ══════════════════════════════════════════════════════════
_rate_store = defaultdict(list)

RATE_LIMITS = {
    "default":        (100, 60),   # 100 req/min
    "/users/login":   (5,   60),   # 5 login attempts/min (brute force protection)
    "/users/register":(3,   60),   # 3 registrations/min
    "/paper/v3/execute": (30, 60), # 30 paper trades/min
    "/backtest/":     (10,  60),   # 10 backtests/min
    "/admin/":        (50,  60),   # 50 admin calls/min
}

def check_rate_limit(key: str, path: str) -> tuple[bool, int]:
    """Returns (allowed, retry_after_seconds)"""
    limit, window = RATE_LIMITS.get("default", (100, 60))
    for prefix, (lim, win) in RATE_LIMITS.items():
        if path.startswith(prefix) and prefix != "default":
            limit, window = lim, win; break
    
    now = time.time()
    bucket = f"{key}:{path[:20]}"
    _rate_store[bucket] = [t for t in _rate_store[bucket] if now - t < window]
    
    if len(_rate_store[bucket]) >= limit:
        retry = window - (now - _rate_store[bucket][0])
        return False, int(retry)
    
    _rate_store[bucket].append(now)
    return True, 0

# ══════════════════════════════════════════════════════════
# HEALTH MONITOR
# ══════════════════════════════════════════════════════════
import threading

_health_stats = {
    "start_time":   time.time(),
    "total_req":    0,
    "error_count":  0,
    "last_error":   None,
    "p99_ms":       0.0,
    "_latencies":   [],
}
_stats_lock = threading.Lock()

def record_request(path: str, ms: float, status: int):
    with _stats_lock:
        _health_stats["total_req"] += 1
        lats = _health_stats["_latencies"]
        lats.append(ms)
        if len(lats) > 1000: lats.pop(0)
        if status >= 500:
            _health_stats["error_count"] += 1
            _health_stats["last_error"] = {"path": path, "ts": datetime.now(IST).isoformat(), "status": status}
        if lats:
            s = sorted(lats)
            _health_stats["p99_ms"] = round(s[int(len(s)*0.99)], 1)

def get_health() -> dict:
    uptime = time.time() - _health_stats["start_time"]
    with _stats_lock:
        total = _health_stats["total_req"]
        err   = _health_stats["error_count"]
    return {
        "status":      "healthy" if err < total * 0.05 else "degraded",
        "uptime_s":    round(uptime),
        "uptime_human":f"{int(uptime//3600)}h {int((uptime%3600)//60)}m",
        "requests":    total,
        "errors":      err,
        "error_rate":  f"{(err/max(total,1)*100):.2f}%",
        "p99_ms":      _health_stats["p99_ms"],
        "last_error":  _health_stats["last_error"],
        "version":     "TRD v12.3",
        "timestamp":   datetime.now(IST).isoformat(),
    }

# ══════════════════════════════════════════════════════════
# FASTAPI MIDDLEWARE
# ══════════════════════════════════════════════════════════
async def institutional_middleware(request: Request, call_next: Callable) -> Response:
    """
    Institutional-grade middleware:
    1. Request ID tracking
    2. Rate limiting  
    3. Timing / latency measurement
    4. Structured logging
    5. Error catching
    6. Security headers
    """
    req_id  = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    ip      = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    ip      = ip.split(",")[0].strip()
    path    = request.url.path
    method  = request.method
    start   = time.time()
    
    # Skip middleware for static/health
    if path in ["/docs", "/openapi.json", "/favicon.ico", "/manifest.json"]:
        return await call_next(request)
    
    # Rate limiting
    rate_key = ip
    allowed, retry = check_rate_limit(rate_key, path)
    if not allowed:
        log_warn("rate_limit_exceeded", ip=ip, path=path, retry_after=retry)
        return JSONResponse(
            status_code=429,
            content={"error": "Too many requests", "retry_after": retry},
            headers={"Retry-After": str(retry), "X-Request-ID": req_id}
        )
    
    # Process request
    try:
        response = await call_next(request)
    except Exception as exc:
        ms = round((time.time()-start)*1000, 2)
        log_error("unhandled_exception", path=path, method=method, 
                  error=str(exc), traceback=traceback.format_exc()[:500],
                  req_id=req_id, ip=ip, ms=ms)
        record_request(path, ms, 500)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "request_id": req_id},
            headers={"X-Request-ID": req_id}
        )
    
    # Timing
    ms     = round((time.time()-start)*1000, 2)
    status = response.status_code
    record_request(path, ms, status)
    
    # Log slow requests > 2s
    if ms > 2000:
        log_warn("slow_request", path=path, method=method, ms=ms, status=status)
    
    # Log errors
    if status >= 400:
        log_warn("request_error", path=path, method=method, status=status, ms=ms, ip=ip)
    
    # Security headers
    response.headers["X-Request-ID"]        = req_id
    response.headers["X-Response-Time"]     = f"{ms}ms"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]     = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    
    return response

print("✅ middleware.py created")
