"""Enterprise Security Module v12.3"""
import hashlib, secrets, json, time, os, base64, sqlite3
from typing import List, Dict
from datetime import datetime, timedelta

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../database/security.db")
ROLES = {
    "SUPERADMIN":{"level":100,"perms":["*"]},
    "ADMIN":{"level":80,"perms":["read_all","write_all","manage_users","analytics","manage_subs"]},
    "PRO_USER":{"level":30,"perms":["read_own","write_trades","advanced_features","ai_engine"]},
    "BASIC_USER":{"level":20,"perms":["read_own","write_trades","basic_features"]},
    "FREE_USER":{"level":10,"perms":["read_own","write_trades_limited"]},
    "GUEST":{"level":1,"perms":["read_public"]},
}

class SecurityModule:
    def __init__(self):
        self._init_db()

    def _conn(self):
        c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS audit_log(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT, action TEXT, resource TEXT,
                ip TEXT DEFAULT '', status TEXT DEFAULT 'SUCCESS',
                details TEXT DEFAULT '{}', risk_score INTEGER DEFAULT 0,
                timestamp TEXT, immutable_hash TEXT, role TEXT DEFAULT 'USER'
            );
            CREATE TABLE IF NOT EXISTS mfa_tokens(
                user_id TEXT PRIMARY KEY, totp_secret TEXT,
                enabled INTEGER DEFAULT 0, created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS rbac_roles(
                user_id TEXT PRIMARY KEY, role TEXT DEFAULT 'FREE_USER',
                custom_perms TEXT DEFAULT '[]', assigned_by TEXT,
                assigned_at TEXT
            );
            CREATE TABLE IF NOT EXISTS rate_limits(
                key TEXT PRIMARY KEY, count INTEGER DEFAULT 0,
                window_start REAL, blocked_until REAL DEFAULT 0
            );
            """)

    def audit(self, user_id, action, resource, status="SUCCESS", details=None, ip="", role="USER", risk=0):
        ts = datetime.utcnow().isoformat()
        h = hashlib.sha256(f"{user_id}|{action}|{resource}|{status}|{ts}".encode()).hexdigest()
        with self._conn() as c:
            c.execute("INSERT INTO audit_log(user_id,action,resource,ip,status,details,risk_score,timestamp,immutable_hash,role) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (user_id,action,resource,ip,status,json.dumps(details or {}),risk,ts,h,role))

    def get_audit(self, user_id=None, limit=50) -> List[dict]:
        with self._conn() as c:
            if user_id:
                rows = c.execute("SELECT * FROM audit_log WHERE user_id=? ORDER BY timestamp DESC LIMIT ?", (user_id,limit)).fetchall()
            else:
                rows = c.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def check_perm(self, user_id, permission) -> bool:
        with self._conn() as c:
            row = c.execute("SELECT role FROM rbac_roles WHERE user_id=?", (user_id,)).fetchone()
        role = row["role"] if row else "FREE_USER"
        perms = ROLES.get(role, ROLES["FREE_USER"])["perms"]
        return "*" in perms or permission in perms

    def assign_role(self, user_id, role, by="SYSTEM"):
        if role not in ROLES: return False
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO rbac_roles(user_id,role,assigned_by,assigned_at) VALUES(?,?,?,?)",
                (user_id,role,by,datetime.utcnow().isoformat()))
        self.audit("SYSTEM","ROLE_ASSIGNED",f"user:{user_id}",details={"role":role})
        return True

    def get_role(self, user_id) -> str:
        with self._conn() as c:
            row = c.execute("SELECT role FROM rbac_roles WHERE user_id=?", (user_id,)).fetchone()
        return row["role"] if row else "FREE_USER"

    def rate_limit_check(self, key, max_req=100, window=60) -> bool:
        now = time.time()
        with self._conn() as c:
            row = c.execute("SELECT * FROM rate_limits WHERE key=?", (key,)).fetchone()
            if row:
                r = dict(row)
                if r["blocked_until"] and r["blocked_until"] > now: return False
                if now - (r["window_start"] or now) > window:
                    c.execute("UPDATE rate_limits SET count=1,window_start=?,blocked_until=0 WHERE key=?", (now,key)); return True
                count = r["count"] + 1
                if count > max_req:
                    c.execute("UPDATE rate_limits SET count=?,blocked_until=? WHERE key=?", (count,now+window*2,key)); return False
                c.execute("UPDATE rate_limits SET count=? WHERE key=?", (count,key))
            else:
                c.execute("INSERT INTO rate_limits VALUES(?,1,?,0)", (key,now))
        return True

    def gen_mfa_secret(self, user_id) -> str:
        secret = base64.b32encode(secrets.token_bytes(20)).decode()
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO mfa_tokens(user_id,totp_secret,enabled,created_at) VALUES(?,?,0,?)",
                (user_id,secret,datetime.utcnow().isoformat()))
        return secret

    def admin_stats(self) -> dict:
        with self._conn() as c:
            total = c.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
            failed = c.execute("SELECT COUNT(*) FROM audit_log WHERE status='FAILED'").fetchone()[0]
            top = c.execute("SELECT action,COUNT(*) cnt FROM audit_log GROUP BY action ORDER BY cnt DESC LIMIT 5").fetchall()
        return {"total_events":total,"failed_events":failed,"top_actions":[dict(r) for r in top]}

security = SecurityModule()
