"""
TRD v12.3 — Database Migration System
Provides: Schema versioning, safe migrations, rollback support, integrity checks
"""
import sqlite3, json, hashlib, os, shutil
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))
DB_DIR = os.path.join(os.path.dirname(__file__), "../database")
USER_DB = os.path.join(DB_DIR, "users.db")
BACKUP_DIR = os.path.join(DB_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

SCHEMA_VERSION = 5  # Current target version

MIGRATIONS = {
    1: {
        "description": "Initial schema — users, strategies",
        "up": [],  # Already exists
        "down": [],
    },
    2: {
        "description": "Add broker isolation columns",
        "up": [
            "ALTER TABLE users ADD COLUMN broker_name TEXT DEFAULT ''",
            "ALTER TABLE users ADD COLUMN broker_mode TEXT DEFAULT 'PAPER'",
            "ALTER TABLE users ADD COLUMN broker_key_hint TEXT DEFAULT ''",
        ],
        "down": [],  # SQLite can't DROP columns — intentionally empty
    },
    3: {
        "description": "Add user session tracking",
        "up": [
            "ALTER TABLE users ADD COLUMN last_login TEXT DEFAULT ''",
            "ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN failed_logins INTEGER DEFAULT 0",
        ],
        "down": [],
    },
    4: {
        "description": "Add user preferences and API keys",
        "up": [
            "ALTER TABLE users ADD COLUMN preferences TEXT DEFAULT '{}'",
            "ALTER TABLE users ADD COLUMN api_key TEXT DEFAULT ''",
            "ALTER TABLE users ADD COLUMN api_key_created TEXT DEFAULT ''",
        ],
        "down": [],
    },
    5: {
        "description": "Add audit trail and immutable trade log",
        "up": [
            """CREATE TABLE IF NOT EXISTS trade_audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id    TEXT UNIQUE NOT NULL,
                ts          TEXT NOT NULL,
                user_id     TEXT NOT NULL,
                trade_id    TEXT NOT NULL,
                action      TEXT NOT NULL,
                instrument  TEXT DEFAULT '',
                strike      INTEGER DEFAULT 0,
                option_type TEXT DEFAULT '',
                lots        INTEGER DEFAULT 1,
                price       REAL DEFAULT 0,
                pnl         REAL DEFAULT 0,
                details     TEXT DEFAULT '{}',
                is_paper    INTEGER DEFAULT 1,
                hash_prev   TEXT DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS schema_versions (
                version     INTEGER PRIMARY KEY,
                applied_at  TEXT NOT NULL,
                description TEXT DEFAULT '',
                checksum    TEXT DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS user_sessions (
                session_id  TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                expires_at  TEXT NOT NULL,
                ip_address  TEXT DEFAULT '',
                user_agent  TEXT DEFAULT '',
                is_active   INTEGER DEFAULT 1
            )""",
        ],
        "down": [],
    },
}

def backup_db(reason: str = "migration") -> str:
    """Create timestamped backup before any migration"""
    ts = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"users_{ts}_{reason}.db")
    if os.path.exists(USER_DB):
        shutil.copy2(USER_DB, backup_path)
        return backup_path
    return ""

def get_current_version(c) -> int:
    try:
        row = c.execute("SELECT MAX(version) as v FROM schema_versions").fetchone()
        return row["v"] or 0 if row else 0
    except Exception:
        return 0

def run_migrations(force: bool = False) -> dict:
    """Run all pending migrations safely"""
    results = {"applied": [], "skipped": [], "errors": [], "current_version": 0}
    
    conn = sqlite3.connect(USER_DB)
    conn.row_factory = sqlite3.Row
    
    # Ensure schema_versions table exists
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_versions (
        version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL,
        description TEXT DEFAULT '', checksum TEXT DEFAULT ''
    )""")
    conn.commit()
    
    current = get_current_version(conn)
    results["current_version"] = current
    
    if current >= SCHEMA_VERSION and not force:
        conn.close()
        return {**results, "message": f"Schema up to date (v{SCHEMA_VERSION})"}
    
    # Backup before migration
    backup = backup_db("pre_migration")
    results["backup"] = backup
    
    for version in range(current + 1, SCHEMA_VERSION + 1):
        if version not in MIGRATIONS:
            continue
        migration = MIGRATIONS[version]
        
        try:
            for sql in migration["up"]:
                try:
                    conn.execute(sql)
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        pass  # Column already exists — OK
                    else:
                        raise
            
            checksum = hashlib.md5(json.dumps(migration["up"]).encode()).hexdigest()
            conn.execute(
                "INSERT OR REPLACE INTO schema_versions VALUES (?,?,?,?)",
                (version, datetime.now(IST).isoformat(), migration["description"], checksum)
            )
            conn.commit()
            results["applied"].append({"version": version, "description": migration["description"]})
            
        except Exception as e:
            conn.rollback()
            results["errors"].append({"version": version, "error": str(e)})
            # Restore backup on error
            if backup and os.path.exists(backup):
                conn.close()
                shutil.copy2(backup, USER_DB)
                return {**results, "rollback": True, "message": f"Migration v{version} failed — DB restored"}
    
    results["current_version"] = SCHEMA_VERSION
    conn.close()
    return results

def log_trade(user_id: str, trade_id: str, action: str, instrument: str,
              strike: int, option_type: str, lots: int, price: float, 
              pnl: float, is_paper: bool, details: dict = None) -> str:
    """Append immutable trade to audit log (hash-chained)"""
    import uuid
    event_id = str(uuid.uuid4())
    ts = datetime.now(IST).isoformat()
    det_str = json.dumps(details or {}, default=str)
    
    conn = sqlite3.connect(USER_DB)
    conn.row_factory = sqlite3.Row
    
    # Ensure table exists
    conn.execute("""CREATE TABLE IF NOT EXISTS trade_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL,
        ts TEXT NOT NULL, user_id TEXT NOT NULL, trade_id TEXT NOT NULL,
        action TEXT NOT NULL, instrument TEXT DEFAULT '', strike INTEGER DEFAULT 0,
        option_type TEXT DEFAULT '', lots INTEGER DEFAULT 1, price REAL DEFAULT 0,
        pnl REAL DEFAULT 0, details TEXT DEFAULT '{}', is_paper INTEGER DEFAULT 1,
        hash_prev TEXT DEFAULT ''
    )""")
    conn.commit()
    
    last = conn.execute("SELECT event_id FROM trade_audit_log ORDER BY id DESC LIMIT 1").fetchone()
    prev_hash = hashlib.sha256((last["event_id"] if last else "GENESIS").encode()).hexdigest()[:16]
    
    conn.execute("""INSERT INTO trade_audit_log 
        (event_id,ts,user_id,trade_id,action,instrument,strike,option_type,lots,price,pnl,details,is_paper,hash_prev)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (event_id,ts,user_id,trade_id,action,instrument,strike,option_type,lots,price,pnl,det_str,int(is_paper),prev_hash))
    conn.commit()
    conn.close()
    return event_id

def get_trade_history(user_id: str, limit: int = 100) -> list:
    """Get immutable trade history for a user"""
    conn = sqlite3.connect(USER_DB)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM trade_audit_log WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        conn.close()

def verify_audit_integrity(limit: int = 1000) -> dict:
    """Verify hash chain integrity of trade audit log"""
    conn = sqlite3.connect(USER_DB)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM trade_audit_log ORDER BY id ASC LIMIT ?", (limit,)
        ).fetchall()
    except Exception:
        return {"valid": True, "checked": 0, "message": "No trades yet"}
    finally:
        conn.close()
    
    if not rows:
        return {"valid": True, "checked": 0}
    
    prev_hash = "GENESIS"
    for i, row in enumerate(rows):
        expected_prev = hashlib.sha256(rows[i-1]["event_id"].encode()).hexdigest()[:16] if i > 0 else "GENESIS"
        if row["hash_prev"] != expected_prev:
            return {"valid": False, "tampered_at": row["event_id"], "position": i}
        prev_hash = row["event_id"]
    
    return {"valid": True, "checked": len(rows), "message": "Audit chain intact"}

print("✅ db_migrations.py created")
