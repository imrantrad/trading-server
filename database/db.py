"""SQLite Database Engine v12.3"""
import sqlite3, json, time, os
from typing import List, Dict, Optional, Any
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading.db")

class TradingDB:
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
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY, instrument TEXT, action TEXT, option_type TEXT,
                strike INTEGER, expiry TEXT, quantity INTEGER, lot_size INTEGER,
                entry_price REAL, exit_price REAL, entry_time TEXT, exit_time TEXT,
                exit_reason TEXT, strategy TEXT, gross_pnl REAL, net_pnl REAL,
                pnl_pct REAL, broker TEXT, mode TEXT, is_hedge INTEGER DEFAULT 0,
                notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, trade_id TEXT,
                instrument TEXT, action TEXT, pnl REAL, emotion TEXT,
                mistakes TEXT, lessons TEXT, rating INTEGER, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS iv_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, instrument TEXT,
                iv REAL, iv_rank REAL, iv_percentile REAL, vix REAL, timestamp TEXT);
            CREATE TABLE IF NOT EXISTS oi_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT, instrument TEXT,
                strike INTEGER, expiry TEXT, ce_oi INTEGER, pe_oi INTEGER,
                ce_chng INTEGER, pe_chng INTEGER, timestamp TEXT);
            CREATE TABLE IF NOT EXISTS equity_curve (
                id INTEGER PRIMARY KEY AUTOINCREMENT, capital REAL,
                pnl REAL, trades INTEGER, win_rate REAL, timestamp TEXT);
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, level TEXT,
                title TEXT, message TEXT, acknowledged INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT, instrument TEXT,
                open REAL, high REAL, low REAL, close REAL,
                volume INTEGER, timestamp TEXT, timeframe TEXT DEFAULT '1D');
            """)

    def save_trade(self, t: dict) -> str:
        tid = t.get("id", f"TRD{int(time.time()*1000)%1000000:06d}")
        with self.conn() as c:
            c.execute("""INSERT OR REPLACE INTO trades
                (id,instrument,action,option_type,strike,expiry,quantity,lot_size,
                 entry_price,exit_price,entry_time,exit_time,exit_reason,strategy,
                 gross_pnl,net_pnl,pnl_pct,broker,mode,is_hedge,notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (tid,t.get("instrument","NIFTY"),t.get("action","BUY"),
                 t.get("option_type","CE"),t.get("strike",0),t.get("expiry","WEEKLY"),
                 t.get("quantity",1),t.get("lot_size",50),t.get("entry_price",0),
                 t.get("exit_price",0),t.get("entry_time",""),t.get("exit_time",""),
                 t.get("exit_reason",""),t.get("strategy",""),t.get("gross_pnl",0),
                 t.get("net_pnl",0),t.get("pnl_pct",0),t.get("broker","PAPER"),
                 t.get("mode","PAPER"),1 if t.get("is_hedge") else 0,t.get("notes","")))
        return tid

    def get_trades(self, limit=100, instrument=None):
        with self.conn() as c:
            if instrument:
                rows = c.execute("SELECT * FROM trades WHERE instrument=? ORDER BY created_at DESC LIMIT ?",
                                 (instrument,limit)).fetchall()
            else:
                rows = c.execute("SELECT * FROM trades ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self):
        with self.conn() as c:
            total = c.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
            wins = c.execute("SELECT COUNT(*) FROM trades WHERE net_pnl > 0").fetchone()[0]
            pnl = c.execute("SELECT SUM(net_pnl) FROM trades").fetchone()[0] or 0
            aw = c.execute("SELECT AVG(net_pnl) FROM trades WHERE net_pnl > 0").fetchone()[0] or 0
            al = c.execute("SELECT AVG(net_pnl) FROM trades WHERE net_pnl < 0").fetchone()[0] or 0
            best = c.execute("SELECT MAX(net_pnl) FROM trades").fetchone()[0] or 0
            worst = c.execute("SELECT MIN(net_pnl) FROM trades").fetchone()[0] or 0
        return {"total":total,"wins":wins,"losses":total-wins,
                "win_rate":round(wins/total*100 if total else 0,1),
                "total_pnl":round(pnl,0),"avg_win":round(aw,0),"avg_loss":round(al,0),
                "profit_factor":round(abs(aw*wins)/abs(al*(total-wins)+1),2),
                "best_trade":round(best,0),"worst_trade":round(worst,0)}

    def add_journal(self, e: dict) -> int:
        with self.conn() as c:
            cur = c.execute("""INSERT INTO journal
                (date,trade_id,instrument,action,pnl,emotion,mistakes,lessons,rating,notes)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (e.get("date",datetime.now().strftime("%Y-%m-%d")),e.get("trade_id",""),
                 e.get("instrument",""),e.get("action",""),e.get("pnl",0),
                 e.get("emotion",""),e.get("mistakes",""),e.get("lessons",""),
                 e.get("rating",5),e.get("notes","")))
            return cur.lastrowid

    def get_journal(self, limit=50):
        with self.conn() as c:
            rows = c.execute("SELECT * FROM journal ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def save_iv(self, inst, iv, rank, pct, vix):
        with self.conn() as c:
            c.execute("INSERT INTO iv_history (instrument,iv,iv_rank,iv_percentile,vix,timestamp) VALUES (?,?,?,?,?,?)",
                      (inst,iv,rank,pct,vix,time.strftime("%Y-%m-%d %H:%M:%S")))

    def get_iv_history(self, inst, days=30):
        with self.conn() as c:
            rows = c.execute("SELECT * FROM iv_history WHERE instrument=? ORDER BY timestamp DESC LIMIT ?",
                             (inst,days)).fetchall()
        return [dict(r) for r in rows]

    def save_oi(self, d: dict):
        with self.conn() as c:
            c.execute("INSERT INTO oi_data (instrument,strike,expiry,ce_oi,pe_oi,ce_chng,pe_chng,timestamp) VALUES (?,?,?,?,?,?,?,?)",
                      (d.get("instrument"),d.get("strike"),d.get("expiry"),
                       d.get("ce_oi",0),d.get("pe_oi",0),
                       d.get("ce_chng",0),d.get("pe_chng",0),
                       time.strftime("%Y-%m-%d %H:%M:%S")))

    def save_equity(self, capital, pnl, trades, win_rate):
        with self.conn() as c:
            c.execute("INSERT INTO equity_curve (capital,pnl,trades,win_rate,timestamp) VALUES (?,?,?,?,?)",
                      (capital,pnl,trades,win_rate,time.strftime("%Y-%m-%d %H:%M:%S")))

    def get_equity(self, limit=200):
        with self.conn() as c:
            rows = c.execute("SELECT * FROM equity_curve ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in reversed(rows)]

    def set(self, key, value):
        with self.conn() as c:
            c.execute("INSERT OR REPLACE INTO settings (key,value,updated_at) VALUES (?,?,?)",
                      (key,json.dumps(value),time.strftime("%Y-%m-%d %H:%M:%S")))

    def get(self, key, default=None):
        with self.conn() as c:
            row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def add_alert(self, atype, level, title, msg):
        with self.conn() as c:
            c.execute("INSERT INTO alerts (type,level,title,message,created_at) VALUES (?,?,?,?,?)",
                      (atype,level,title,msg,time.strftime("%Y-%m-%d %H:%M:%S")))

    def get_alerts(self, unread=False, limit=50):
        with self.conn() as c:
            q = "SELECT * FROM alerts WHERE acknowledged=0" if unread else "SELECT * FROM alerts"
            rows = c.execute(q+" ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def ack_alert(self, aid):
        with self.conn() as c:
            c.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (aid,))

    def save_market_data(self, inst, o, h, l, cl, vol=0, tf="1D"):
        with self.conn() as c:
            c.execute("INSERT INTO market_data (instrument,open,high,low,close,volume,timestamp,timeframe) VALUES (?,?,?,?,?,?,?,?)",
                      (inst,o,h,l,cl,vol,time.strftime("%Y-%m-%d %H:%M:%S"),tf))

    def get_market_data(self, inst, limit=252, tf="1D"):
        with self.conn() as c:
            rows = c.execute("SELECT * FROM market_data WHERE instrument=? AND timeframe=? ORDER BY timestamp DESC LIMIT ?",
                             (inst,tf,limit)).fetchall()
        return [dict(r) for r in reversed(rows)]


db = TradingDB()
