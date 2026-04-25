"""Advanced Multi-Channel Notification Engine v12.3"""
import json, sqlite3, os
from datetime import datetime
from typing import List, Dict

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../database/notifications.db")

NOTIF_TYPES = {
    "TRADE_EXECUTED":{"icon":"▶","priority":"HIGH","channels":["push","email"]},
    "SL_HIT":{"icon":"🔴","priority":"CRITICAL","channels":["push","sms","email"]},
    "TARGET_HIT":{"icon":"🎯","priority":"HIGH","channels":["push","email"]},
    "MARKET_ALERT":{"icon":"📊","priority":"MEDIUM","channels":["push"]},
    "AI_SIGNAL":{"icon":"🤖","priority":"HIGH","channels":["push","email"]},
    "SUBSCRIPTION":{"icon":"💳","priority":"MEDIUM","channels":["email"]},
    "DAILY_REPORT":{"icon":"📈","priority":"LOW","channels":["email"]},
    "KILL_SWITCH":{"icon":"⚠️","priority":"CRITICAL","channels":["push","sms","email"]},
    "SYSTEM":{"icon":"⚙","priority":"LOW","channels":["push"]},
}

class NotificationEngine:
    def __init__(self):
        self._init_db()

    def _conn(self):
        c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS notifications(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT, type TEXT, title TEXT, message TEXT,
                icon TEXT DEFAULT '●', priority TEXT DEFAULT 'MEDIUM',
                read INTEGER DEFAULT 0, channels TEXT DEFAULT '[]',
                data TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS notification_prefs(
                user_id TEXT PRIMARY KEY,
                push_enabled INTEGER DEFAULT 1,
                email_enabled INTEGER DEFAULT 1,
                sms_enabled INTEGER DEFAULT 0,
                trade_alerts INTEGER DEFAULT 1,
                sl_alerts INTEGER DEFAULT 1,
                target_alerts INTEGER DEFAULT 1,
                market_alerts INTEGER DEFAULT 1,
                ai_signals INTEGER DEFAULT 1,
                daily_report INTEGER DEFAULT 1,
                telegram_id TEXT DEFAULT ''
            );
            """)

    def send(self, user_id, notif_type, title, message, data=None):
        cfg = NOTIF_TYPES.get(notif_type, NOTIF_TYPES["SYSTEM"])
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO notifications(user_id,type,title,message,icon,priority,channels,data,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (user_id,notif_type,title,message,cfg["icon"],cfg["priority"],
                 json.dumps(cfg["channels"]),json.dumps(data or {}),datetime.now().isoformat()))
            return cur.lastrowid

    def get_all(self, user_id, unread_only=False, limit=30):
        with self._conn() as c:
            q = "SELECT * FROM notifications WHERE user_id=?"
            params = [user_id]
            if unread_only: q += " AND read=0"
            q += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = c.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    def mark_read(self, user_id, notif_id=None):
        with self._conn() as c:
            if notif_id: c.execute("UPDATE notifications SET read=1 WHERE id=? AND user_id=?", (notif_id,user_id))
            else: c.execute("UPDATE notifications SET read=1 WHERE user_id=?", (user_id,))

    def unread_count(self, user_id):
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND read=0",(user_id,)).fetchone()[0]

    def get_prefs(self, user_id):
        with self._conn() as c:
            row = c.execute("SELECT * FROM notification_prefs WHERE user_id=?",(user_id,)).fetchone()
        if not row:
            with self._conn() as c:
                c.execute("INSERT OR IGNORE INTO notification_prefs(user_id) VALUES(?)",(user_id,))
            return {"user_id":user_id,"push_enabled":1,"email_enabled":1,"trade_alerts":1,"sl_alerts":1,"target_alerts":1,"market_alerts":1,"ai_signals":1,"daily_report":1}
        return dict(row)

    def save_prefs(self, user_id, prefs):
        safe=["push_enabled","email_enabled","sms_enabled","trade_alerts","sl_alerts","target_alerts","market_alerts","ai_signals","daily_report","telegram_id"]
        clean={k:v for k,v in prefs.items() if k in safe}
        if not clean: return False
        with self._conn() as c:
            c.execute("INSERT OR IGNORE INTO notification_prefs(user_id) VALUES(?)",(user_id,))
            sets=",".join(f"{k}=?" for k in clean)
            c.execute(f"UPDATE notification_prefs SET {sets} WHERE user_id=?",(*clean.values(),user_id))
        return True

notif_engine = NotificationEngine()
try:
    notif_engine.send("USR124535215","SYSTEM","TRD v12.3 Ready","All systems operational. Paper trading active.")
    notif_engine.send("USR124535215","AI_SIGNAL","AI Signal: NIFTY BUY CE","Confidence 87% | Regime: TRENDING_UP | Entry ₹23900",{"signal":"BUY_CE","confidence":0.87})
    notif_engine.send("USR124535215","MARKET_ALERT","VIX Alert","VIX crossed 20. Consider defensive positions.",{"vix":20.5})
except: pass
