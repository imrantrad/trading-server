"""User Profiles + Strategy Storage + Subscriptions v12.3"""
import sqlite3, json, time, hashlib, os, secrets, string
from typing import List, Dict, Optional
from datetime import datetime, timedelta

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
                email TEXT UNIQUE,
                password_hash TEXT,
                full_name TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                avatar TEXT DEFAULT '',
                broker TEXT DEFAULT 'ZERODHA',
                capital REAL DEFAULT 500000,
                risk_per_trade REAL DEFAULT 1.0,
                max_daily_loss REAL DEFAULT 3.0,
                max_drawdown REAL DEFAULT 10.0,
                preferred_instruments TEXT DEFAULT 'NIFTY,BANKNIFTY',
                preferred_timeframe TEXT DEFAULT '15MIN',
                theme TEXT DEFAULT 'DARK',
                notifications_enabled INTEGER DEFAULT 1,
                telegram_chat_id TEXT DEFAULT '',
                timezone TEXT DEFAULT 'Asia/Kolkata',
                bio TEXT DEFAULT '',
                subscription_plan TEXT DEFAULT 'FREE',
                subscription_expires TEXT DEFAULT '',
                email_verified INTEGER DEFAULT 0,
                verification_token TEXT DEFAULT '',
                reset_token TEXT DEFAULT '',
                login_count INTEGER DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT,
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS user_strategies (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                instrument TEXT DEFAULT 'NIFTY',
                timeframe TEXT DEFAULT '15MIN',
                entry_conditions TEXT DEFAULT '[]',
                exit_conditions TEXT DEFAULT '[]',
                nlp_input TEXT DEFAULT '',
                parsed_nlp TEXT DEFAULT '{}',
                sl_type TEXT DEFAULT 'FIXED',
                sl_value REAL DEFAULT 100,
                target_type TEXT DEFAULT 'FIXED',
                target_value REAL DEFAULT 200,
                trailing_sl REAL DEFAULT 0,
                quantity INTEGER DEFAULT 1,
                risk_per_trade REAL DEFAULT 1.0,
                tags TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                is_public INTEGER DEFAULT 0,
                backtest_pnl REAL DEFAULT 0,
                backtest_winrate REAL DEFAULT 0,
                backtest_trades INTEGER DEFAULT 0,
                live_trades INTEGER DEFAULT 0,
                live_pnl REAL DEFAULT 0,
                paper_trades INTEGER DEFAULT 0,
                paper_pnl REAL DEFAULT 0,
                paper_winrate REAL DEFAULT 0,
                color TEXT DEFAULT '#00ff88',
                icon TEXT DEFAULT '★',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS paper_strategy_trades (
                id TEXT PRIMARY KEY,
                strategy_id TEXT,
                user_id TEXT,
                instrument TEXT,
                action TEXT,
                option_type TEXT,
                strike INTEGER,
                quantity INTEGER,
                lot_size INTEGER DEFAULT 50,
                entry_price REAL,
                exit_price REAL DEFAULT 0,
                entry_time TEXT,
                exit_time TEXT DEFAULT '',
                stoploss REAL DEFAULT 0,
                target REAL DEFAULT 0,
                status TEXT DEFAULT 'OPEN',
                pnl REAL DEFAULT 0,
                exit_reason TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE,
                plan TEXT DEFAULT 'FREE',
                price REAL DEFAULT 0,
                currency TEXT DEFAULT 'INR',
                billing_cycle TEXT DEFAULT 'MONTHLY',
                started_at TEXT,
                expires_at TEXT,
                auto_renew INTEGER DEFAULT 0,
                payment_id TEXT DEFAULT '',
                status TEXT DEFAULT 'ACTIVE',
                features TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS email_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                email TEXT,
                token TEXT,
                expires_at TEXT,
                verified INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS user_sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT,
                ip TEXT DEFAULT '',
                device TEXT DEFAULT '',
                created_at TEXT,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS user_watchlist (
                user_id TEXT, symbol TEXT,
                PRIMARY KEY(user_id, symbol)
            );
            CREATE TABLE IF NOT EXISTS user_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT, type TEXT, title TEXT,
                message TEXT, read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

    def _hash(self, pw): return hashlib.sha256(pw.encode()).hexdigest()
    def _uid(self): return f"USR{int(time.time()*1000)%999999999:09d}"
    def _sid(self): return f"STR{int(time.time()*1000)%999999999:09d}"
    def _token(self): return secrets.token_urlsafe(32)

    # ── USERS ────────────────────────────────────────────
    def create_user(self, username, email="", password="demo123",
                    full_name="", capital=500000, plan="FREE") -> dict:
        uid = self._uid()
        verify_token = self._token()
        try:
            with self.conn() as c:
                c.execute("""INSERT INTO users
                    (id,username,email,password_hash,full_name,capital,
                     subscription_plan,verification_token,email_verified)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (uid, username, email, self._hash(password),
                     full_name, capital, plan, verify_token,
                     0 if email else 1))  # auto-verify if no email
            # Create free subscription
            self._create_subscription(uid, plan)
            # Send verification (simulated)
            return {
                "id": uid, "username": username, "status": "created",
                "email_verification": "required" if email else "skipped",
                "verify_token": verify_token,
                "message": f"Account created! {'Check email to verify.' if email else 'Ready to use!'}"
            }
        except sqlite3.IntegrityError as e:
            if "username" in str(e): return {"error": "Username already taken"}
            if "email" in str(e): return {"error": "Email already registered"}
            return {"error": str(e)}

    def verify_email(self, token: str) -> bool:
        with self.conn() as c:
            row = c.execute("SELECT id FROM users WHERE verification_token=?", (token,)).fetchone()
            if row:
                c.execute("UPDATE users SET email_verified=1,verification_token='' WHERE id=?", (row[0],))
                return True
        return False

    def login(self, username_or_email: str, password: str) -> Optional[dict]:
        with self.conn() as c:
            row = c.execute("""SELECT * FROM users WHERE
                (username=? OR email=?) AND password_hash=? AND is_active=1""",
                (username_or_email, username_or_email, self._hash(password))).fetchone()
        if not row: return None
        user = dict(row)
        with self.conn() as c:
            c.execute("UPDATE users SET last_login=?,login_count=login_count+1 WHERE id=?",
                     (time.strftime("%Y-%m-%d %H:%M:%S"), user["id"]))
        token = self._token()
        with self.conn() as c:
            c.execute("INSERT INTO user_sessions VALUES (?,?,?,?,?,?,1)",
                     (token, user["id"], "", "web",
                      time.strftime("%Y-%m-%d %H:%M:%S"),
                      (datetime.now()+timedelta(days=30)).strftime("%Y-%m-%d")))
        user.pop("password_hash", None); user.pop("verification_token", None)
        sub = self.get_subscription(user["id"])
        return {"user": user, "token": token, "subscription": sub}

    def get_user(self, uid: str) -> Optional[dict]:
        with self.conn() as c:
            row = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        if not row: return None
        u = dict(row)
        u.pop("password_hash",None); u.pop("verification_token",None); u.pop("reset_token",None)
        u["subscription"] = self.get_subscription(uid)
        u["strategy_count"] = len(self.get_strategies(uid))
        return u

    def update_profile(self, uid: str, updates: dict) -> bool:
        safe = ["full_name","email","phone","broker","capital","risk_per_trade",
                "max_daily_loss","max_drawdown","preferred_instruments",
                "preferred_timeframe","theme","telegram_chat_id","bio",
                "notifications_enabled","avatar","timezone"]
        clean = {k:v for k,v in updates.items() if k in safe and v is not None}
        if not clean: return False
        sets = ",".join(f"{k}=?" for k in clean)
        with self.conn() as c:
            c.execute(f"UPDATE users SET {sets} WHERE id=?", (*clean.values(), uid))
        return True

    def change_password(self, uid: str, old_pw: str, new_pw: str) -> bool:
        with self.conn() as c:
            row = c.execute("SELECT id FROM users WHERE id=? AND password_hash=?",
                           (uid, self._hash(old_pw))).fetchone()
            if not row: return False
            c.execute("UPDATE users SET password_hash=? WHERE id=?", (self._hash(new_pw), uid))
        return True

    def get_all_users(self, limit=50) -> List[dict]:
        with self.conn() as c:
            rows = c.execute("""SELECT id,username,full_name,email,capital,broker,
                subscription_plan,email_verified,login_count,total_trades,
                created_at,last_login FROM users LIMIT ?""", (limit,)).fetchall()
        return [dict(r) for r in rows]

    # ── SUBSCRIPTIONS ────────────────────────────────────
    PLANS = {
        "FREE": {
            "price": 0, "strategies": 3, "paper_trades": 50,
            "backtest_months": 1, "scanner": False,
            "advanced_nlp": False, "alerts": 5,
            "features": ["Basic NLP","Paper Trading","3 Strategies","1 Month Backtest"]
        },
        "BASIC": {
            "price": 499, "strategies": 20, "paper_trades": 500,
            "backtest_months": 6, "scanner": True,
            "advanced_nlp": True, "alerts": 50,
            "features": ["Full NLP","Paper Trading","20 Strategies",
                        "6 Month Backtest","Market Scanner","50 Alerts/month"]
        },
        "PRO": {
            "price": 1499, "strategies": -1, "paper_trades": -1,
            "backtest_months": 12, "scanner": True,
            "advanced_nlp": True, "alerts": -1,
            "features": ["Full NLP","Unlimited Paper Trading","Unlimited Strategies",
                        "12 Month Backtest","Advanced Scanner","Unlimited Alerts",
                        "Priority Support","Strategy Marketplace","Real-time Signals"]
        },
        "INSTITUTIONAL": {
            "price": 4999, "strategies": -1, "paper_trades": -1,
            "backtest_months": 60, "scanner": True,
            "advanced_nlp": True, "alerts": -1,
            "features": ["Everything in PRO","Live Trading API","Custom Strategies",
                        "Dedicated Support","Multi-user","White Label","5 Year Backtest"]
        }
    }

    def _create_subscription(self, uid: str, plan: str = "FREE"):
        sid = f"SUB{int(time.time()*1000)%999999999:09d}"
        expires = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d") if plan != "FREE" else "9999-12-31"
        with self.conn() as c:
            c.execute("""INSERT OR REPLACE INTO subscriptions
                (id,user_id,plan,price,started_at,expires_at,status,features)
                VALUES (?,?,?,?,?,?,?,?)""",
                (sid, uid, plan,
                 self.PLANS.get(plan,{}).get("price",0),
                 time.strftime("%Y-%m-%d"),
                 expires, "ACTIVE",
                 json.dumps(self.PLANS.get(plan,{}).get("features",[]))))

    def get_subscription(self, uid: str) -> dict:
        with self.conn() as c:
            row = c.execute("SELECT * FROM subscriptions WHERE user_id=?", (uid,)).fetchone()
        if not row:
            return {"plan":"FREE","status":"ACTIVE","features":self.PLANS["FREE"]["features"]}
        sub = dict(row)
        plan_details = self.PLANS.get(sub["plan"], self.PLANS["FREE"])
        return {**sub, "plan_details": plan_details}

    def upgrade_subscription(self, uid: str, plan: str, payment_id: str = "") -> dict:
        if plan not in self.PLANS: return {"error": "Invalid plan"}
        expires = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        with self.conn() as c:
            c.execute("""UPDATE subscriptions SET plan=?,price=?,expires_at=?,
                payment_id=?,status='ACTIVE' WHERE user_id=?""",
                (plan, self.PLANS[plan]["price"], expires, payment_id, uid))
            c.execute("UPDATE users SET subscription_plan=? WHERE id=?", (plan, uid))
        return {"upgraded": True, "plan": plan, "expires": expires}

    # ── USER STRATEGIES ──────────────────────────────────
    def save_strategy(self, uid: str, s: dict) -> str:
        sid = s.get("id") or self._sid()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.conn() as c:
            c.execute("""INSERT OR REPLACE INTO user_strategies
                (id,user_id,name,description,instrument,timeframe,
                 entry_conditions,exit_conditions,nlp_input,parsed_nlp,
                 sl_type,sl_value,target_type,target_value,trailing_sl,
                 quantity,risk_per_trade,tags,is_public,
                 backtest_pnl,backtest_winrate,color,icon,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (sid, uid, s.get("name","My Strategy"),
                 s.get("description",""),
                 s.get("instrument","NIFTY"), s.get("timeframe","15MIN"),
                 json.dumps(s.get("entry_conditions",[])),
                 json.dumps(s.get("exit_conditions",[])),
                 s.get("nlp_input",""),
                 json.dumps(s.get("parsed_nlp",{})),
                 s.get("sl_type","FIXED"), s.get("sl_value",100),
                 s.get("target_type","FIXED"), s.get("target_value",200),
                 s.get("trailing_sl",0),
                 s.get("quantity",1), s.get("risk_per_trade",1.0),
                 json.dumps(s.get("tags",[])),
                 1 if s.get("is_public") else 0,
                 s.get("backtest_pnl",0), s.get("backtest_winrate",0),
                 s.get("color","#00ff88"), s.get("icon","★"),
                 now, now))
        return sid

    def get_strategies(self, uid=None, public=False) -> List[dict]:
        with self.conn() as c:
            if public: rows = c.execute("SELECT * FROM user_strategies WHERE is_public=1 ORDER BY backtest_winrate DESC").fetchall()
            elif uid: rows = c.execute("SELECT * FROM user_strategies WHERE user_id=? ORDER BY updated_at DESC", (uid,)).fetchall()
            else: rows = c.execute("SELECT * FROM user_strategies ORDER BY updated_at DESC").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            for f in ["entry_conditions","exit_conditions","tags"]:
                try: d[f] = json.loads(d[f] or "[]")
                except: d[f] = []
            try: d["parsed_nlp"] = json.loads(d.get("parsed_nlp") or "{}")
            except: d["parsed_nlp"] = {}
            result.append(d)
        return result

    def delete_strategy(self, sid, uid):
        with self.conn() as c:
            c.execute("DELETE FROM user_strategies WHERE id=? AND user_id=?", (sid,uid))

    def update_strategy_stats(self, sid, pnl, wr, trades, mode="paper"):
        col = f"{mode}_pnl" if mode in ["paper","live"] else "backtest_pnl"
        with self.conn() as c:
            c.execute(f"UPDATE user_strategies SET {col}=?,{mode}_winrate=?,{mode}_trades=? WHERE id=?",
                     (pnl, wr, trades, sid))

    # ── PAPER STRATEGY TRADES ────────────────────────────
    def open_paper_trade(self, uid, strategy_id, trade: dict) -> str:
        tid = f"PT{int(time.time()*1000)%999999999:09d}"
        with self.conn() as c:
            c.execute("""INSERT INTO paper_strategy_trades
                (id,strategy_id,user_id,instrument,action,option_type,
                 strike,quantity,lot_size,entry_price,stoploss,target,
                 entry_time,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (tid, strategy_id, uid,
                 trade.get("instrument","NIFTY"), trade.get("action","BUY"),
                 trade.get("option_type","CE"), trade.get("strike",0),
                 trade.get("quantity",1), trade.get("lot_size",50),
                 trade.get("entry_price",0), trade.get("stoploss",0),
                 trade.get("target",0), time.strftime("%H:%M:%S"), "OPEN"))
        return tid

    def close_paper_trade(self, tid, exit_price, reason="MANUAL") -> dict:
        with self.conn() as c:
            row = c.execute("SELECT * FROM paper_strategy_trades WHERE id=?", (tid,)).fetchone()
            if not row: return {}
            t = dict(row)
            m = 1 if t["action"]=="BUY" else -1
            pnl = m*(exit_price - t["entry_price"])*t["quantity"]*t["lot_size"]
            c.execute("""UPDATE paper_strategy_trades SET
                exit_price=?,exit_time=?,status=?,pnl=?,exit_reason=? WHERE id=?""",
                (exit_price, time.strftime("%H:%M:%S"), reason, pnl, reason, tid))
        return {"id":tid,"pnl":round(pnl,0),"exit_price":exit_price}

    def get_paper_trades(self, uid, strategy_id=None) -> List[dict]:
        with self.conn() as c:
            if strategy_id:
                rows = c.execute("SELECT * FROM paper_strategy_trades WHERE user_id=? AND strategy_id=? ORDER BY created_at DESC", (uid,strategy_id)).fetchall()
            else:
                rows = c.execute("SELECT * FROM paper_strategy_trades WHERE user_id=? ORDER BY created_at DESC LIMIT 100", (uid,)).fetchall()
        return [dict(r) for r in rows]

    def get_strategy_performance(self, strategy_id) -> dict:
        with self.conn() as c:
            trades = c.execute("SELECT * FROM paper_strategy_trades WHERE strategy_id=? AND status!='OPEN'", (strategy_id,)).fetchall()
        if not trades: return {"trades":0,"pnl":0,"win_rate":0}
        total = len(trades); wins = sum(1 for t in trades if dict(t)["pnl"]>0)
        pnl = sum(dict(t)["pnl"] for t in trades)
        return {"trades":total,"wins":wins,"losses":total-wins,
                "win_rate":round(wins/total*100,1),"total_pnl":round(pnl,0)}

    # ── NOTIFICATIONS ────────────────────────────────────
    def add_notification(self, uid, ntype, title, msg):
        with self.conn() as c:
            c.execute("INSERT INTO user_notifications (user_id,type,title,message,created_at) VALUES (?,?,?,?,?)",
                     (uid,ntype,title,msg,time.strftime("%Y-%m-%d %H:%M:%S")))

    def get_notifications(self, uid, unread=False) -> List[dict]:
        with self.conn() as c:
            q = "SELECT * FROM user_notifications WHERE user_id=?"
            if unread: q += " AND read=0"
            rows = c.execute(q+" ORDER BY created_at DESC LIMIT 20", (uid,)).fetchall()
        return [dict(r) for r in rows]

    def mark_notifications_read(self, uid):
        with self.conn() as c:
            c.execute("UPDATE user_notifications SET read=1 WHERE user_id=?", (uid,))


user_db = UserDB()
# Demo user
try: user_db.create_user("demo","demo@trading.com","demo123","Demo Trader",500000,"PRO")
except: pass
