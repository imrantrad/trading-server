"""User Profiles + Strategy Storage v12.3"""
import sqlite3, json, time, hashlib, os
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")

class UserDB:
    def __init__(self, path=DB_PATH):
        self.path = path
        self._init()

    def conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with self.conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT,
                full_name TEXT,
                phone TEXT,
                broker TEXT DEFAULT 'ZERODHA',
                capital REAL DEFAULT 500000,
                risk_per_trade REAL DEFAULT 1.0,
                max_daily_loss REAL DEFAULT 3.0,
                preferred_instruments TEXT DEFAULT 'NIFTY,BANKNIFTY',
                preferred_timeframe TEXT DEFAULT '15MIN',
                theme TEXT DEFAULT 'DARK',
                notifications_enabled INTEGER DEFAULT 1,
                telegram_chat_id TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT,
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS user_strategies (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT NOT NULL,
                description TEXT,
                instrument TEXT DEFAULT 'NIFTY',
                timeframe TEXT DEFAULT '15MIN',
                entry_conditions TEXT,
                exit_conditions TEXT,
                sl_type TEXT DEFAULT 'FIXED',
                sl_value REAL DEFAULT 100,
                target_type TEXT DEFAULT 'FIXED',
                target_value REAL DEFAULT 200,
                quantity INTEGER DEFAULT 1,
                risk_per_trade REAL DEFAULT 1.0,
                tags TEXT,
                is_active INTEGER DEFAULT 1,
                is_public INTEGER DEFAULT 0,
                backtest_pnl REAL DEFAULT 0,
                backtest_winrate REAL DEFAULT 0,
                live_trades INTEGER DEFAULT 0,
                live_pnl REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS strategy_tags (
                strategy_id TEXT, tag TEXT,
                PRIMARY KEY(strategy_id, tag)
            );
            CREATE TABLE IF NOT EXISTS user_watchlist (
                user_id TEXT, symbol TEXT,
                PRIMARY KEY(user_id, symbol)
            );
            CREATE TABLE IF NOT EXISTS user_sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TEXT,
                expires_at TEXT
            );
            """)

    def _hash(self, pw): return hashlib.sha256(pw.encode()).hexdigest()
    def _uid(self): return f"USR{int(time.time()*1000)%1000000000:09d}"
    def _sid(self): return f"STR{int(time.time()*1000)%1000000000:09d}"

    # ── USERS ────────────────────────────────────────────
    def create_user(self, username: str, email: str = "", password: str = "demo123",
                    full_name: str = "", capital: float = 500000) -> dict:
        uid = self._uid()
        try:
            with self.conn() as c:
                c.execute("""INSERT INTO users (id,username,email,password_hash,full_name,capital)
                    VALUES (?,?,?,?,?,?)""",
                    (uid, username, email, self._hash(password), full_name, capital))
            return {"id":uid,"username":username,"status":"created"}
        except sqlite3.IntegrityError:
            return {"error":"Username already exists"}

    def login(self, username: str, password: str) -> Optional[dict]:
        with self.conn() as c:
            row = c.execute("SELECT * FROM users WHERE username=? AND password_hash=? AND is_active=1",
                           (username, self._hash(password))).fetchone()
        if not row: return None
        user = dict(row)
        # Update last login
        with self.conn() as c:
            c.execute("UPDATE users SET last_login=? WHERE id=?",
                     (time.strftime("%Y-%m-%d %H:%M:%S"), user["id"]))
        token = hashlib.sha256(f"{user['id']}{time.time()}".encode()).hexdigest()
        with self.conn() as c:
            c.execute("INSERT INTO user_sessions VALUES (?,?,?,?)",
                     (token, user["id"], time.strftime("%Y-%m-%d %H:%M:%S"),
                      time.strftime("%Y-%m-%d", time.localtime(time.time()+86400*7))))
        user.pop("password_hash", None)
        return {"user": user, "token": token}

    def get_user(self, user_id: str) -> Optional[dict]:
        with self.conn() as c:
            row = c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not row: return None
        u = dict(row); u.pop("password_hash", None)
        return u

    def update_profile(self, user_id: str, updates: dict) -> bool:
        safe_fields = ["full_name","email","phone","broker","capital","risk_per_trade",
                      "max_daily_loss","preferred_instruments","preferred_timeframe",
                      "theme","telegram_chat_id","notifications_enabled"]
        clean = {k:v for k,v in updates.items() if k in safe_fields}
        if not clean: return False
        sets = ",".join(f"{k}=?" for k in clean)
        with self.conn() as c:
            c.execute(f"UPDATE users SET {sets} WHERE id=?", (*clean.values(), user_id))
        return True

    def get_all_users(self) -> List[dict]:
        with self.conn() as c:
            rows = c.execute("SELECT id,username,full_name,capital,broker,created_at,last_login FROM users").fetchall()
        return [dict(r) for r in rows]

    # ── USER STRATEGIES ──────────────────────────────────
    def save_strategy(self, user_id: str, strategy: dict) -> str:
        sid = strategy.get("id") or self._sid()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.conn() as c:
            c.execute("""INSERT OR REPLACE INTO user_strategies
                (id,user_id,name,description,instrument,timeframe,entry_conditions,
                 exit_conditions,sl_type,sl_value,target_type,target_value,
                 quantity,risk_per_trade,tags,is_active,is_public,
                 backtest_pnl,backtest_winrate,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (sid, user_id, strategy.get("name","My Strategy"),
                 strategy.get("description",""),
                 strategy.get("instrument","NIFTY"),
                 strategy.get("timeframe","15MIN"),
                 json.dumps(strategy.get("entry_conditions",[])),
                 json.dumps(strategy.get("exit_conditions",[])),
                 strategy.get("sl_type","FIXED"),
                 strategy.get("sl_value",100),
                 strategy.get("target_type","FIXED"),
                 strategy.get("target_value",200),
                 strategy.get("quantity",1),
                 strategy.get("risk_per_trade",1.0),
                 json.dumps(strategy.get("tags",[])),
                 1, strategy.get("is_public",0),
                 strategy.get("backtest_pnl",0),
                 strategy.get("backtest_winrate",0),
                 now, now))
        return sid

    def get_strategies(self, user_id: str = None, public_only: bool = False) -> List[dict]:
        with self.conn() as c:
            if public_only:
                rows = c.execute("SELECT * FROM user_strategies WHERE is_public=1 ORDER BY backtest_winrate DESC").fetchall()
            elif user_id:
                rows = c.execute("SELECT * FROM user_strategies WHERE user_id=? ORDER BY updated_at DESC", (user_id,)).fetchall()
            else:
                rows = c.execute("SELECT * FROM user_strategies ORDER BY updated_at DESC").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try: d["entry_conditions"] = json.loads(d["entry_conditions"] or "[]")
            except: pass
            try: d["exit_conditions"] = json.loads(d["exit_conditions"] or "[]")
            except: pass
            try: d["tags"] = json.loads(d["tags"] or "[]")
            except: pass
            result.append(d)
        return result

    def delete_strategy(self, sid: str, user_id: str) -> bool:
        with self.conn() as c:
            c.execute("DELETE FROM user_strategies WHERE id=? AND user_id=?", (sid, user_id))
        return True

    def update_strategy_performance(self, sid: str, pnl: float, winrate: float, trades: int):
        with self.conn() as c:
            c.execute("UPDATE user_strategies SET backtest_pnl=?,backtest_winrate=?,live_trades=? WHERE id=?",
                     (pnl, winrate, trades, sid))

    # ── WATCHLIST ────────────────────────────────────────
    def add_watchlist(self, user_id: str, symbol: str):
        with self.conn() as c:
            try: c.execute("INSERT INTO user_watchlist VALUES (?,?)", (user_id, symbol))
            except: pass

    def get_watchlist(self, user_id: str) -> List[str]:
        with self.conn() as c:
            rows = c.execute("SELECT symbol FROM user_watchlist WHERE user_id=?", (user_id,)).fetchall()
        return [r[0] for r in rows]


user_db = UserDB()

# Create default demo user
try:
    user_db.create_user("demo", "demo@trading.com", "demo123", "Demo Trader", 500000)
except:
    pass
