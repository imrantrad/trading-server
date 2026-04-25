"""Dynamic Subscription & Billing Engine v12.3 - Razorpay Ready"""
import json, time, hashlib, sqlite3, os, secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../database/billing.db")

PLANS = {
    "FREE":{"price":0,"currency":"INR","features":{"strategies":3,"backtest_months":1,"paper_trades":50,"scanner":False,"ai_engine":False,"api_calls":1000,"alerts":5},"name":"Free Forever"},
    "BASIC":{"price":499,"currency":"INR","features":{"strategies":20,"backtest_months":6,"paper_trades":500,"scanner":True,"ai_engine":False,"api_calls":10000,"alerts":50},"name":"Basic"},
    "PRO":{"price":1499,"currency":"INR","features":{"strategies":-1,"backtest_months":12,"paper_trades":-1,"scanner":True,"ai_engine":True,"api_calls":100000,"alerts":-1},"name":"Pro"},
    "INSTITUTIONAL":{"price":4999,"currency":"INR","features":{"strategies":-1,"backtest_months":60,"paper_trades":-1,"scanner":True,"ai_engine":True,"api_calls":-1,"alerts":-1,"white_label":True,"multi_user":True},"name":"Institutional"},
}

class BillingEngine:
    def __init__(self):
        self._init_db()

    def _conn(self):
        c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS subscriptions(
                id TEXT PRIMARY KEY, user_id TEXT UNIQUE,
                plan TEXT DEFAULT 'FREE', price REAL DEFAULT 0,
                currency TEXT DEFAULT 'INR', billing_cycle TEXT DEFAULT 'MONTHLY',
                started_at TEXT, expires_at TEXT,
                auto_renew INTEGER DEFAULT 0,
                razorpay_sub_id TEXT DEFAULT '',
                payment_method TEXT DEFAULT '',
                status TEXT DEFAULT 'ACTIVE',
                usage_api_calls INTEGER DEFAULT 0,
                usage_trades INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS invoices(
                id TEXT PRIMARY KEY, user_id TEXT,
                plan TEXT, amount REAL, currency TEXT DEFAULT 'INR',
                gst_amount REAL DEFAULT 0, total_amount REAL,
                razorpay_payment_id TEXT DEFAULT '',
                razorpay_order_id TEXT DEFAULT '',
                status TEXT DEFAULT 'PENDING',
                invoice_date TEXT, due_date TEXT,
                pdf_url TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS usage_meter(
                user_id TEXT, metric TEXT, value REAL DEFAULT 0,
                billing_period TEXT, recorded_at TEXT
            );
            """)

    def create_subscription(self, user_id: str, plan: str = "FREE") -> dict:
        sub_id = f"SUB{secrets.token_hex(8).upper()}"
        expires = (datetime.now() + timedelta(days=30)).isoformat() if plan != "FREE" else "2099-12-31"
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO subscriptions(id,user_id,plan,price,started_at,expires_at) VALUES(?,?,?,?,?,?)",
                (sub_id, user_id, plan, PLANS[plan]["price"],
                 datetime.now().isoformat(), expires))
        return {"sub_id":sub_id,"plan":plan,"expires":expires}

    def upgrade(self, user_id: str, plan: str, payment_id: str = "", order_id: str = "") -> dict:
        if plan not in PLANS: return {"error":"Invalid plan"}
        amount = PLANS[plan]["price"]
        gst = round(amount * 0.18, 2)
        total = amount + gst
        # Create invoice
        inv_id = f"INV{secrets.token_hex(6).upper()}"
        with self._conn() as c:
            c.execute("INSERT INTO invoices(id,user_id,plan,amount,gst_amount,total_amount,razorpay_payment_id,razorpay_order_id,status,invoice_date,due_date) VALUES(?,?,?,?,?,?,?,?,'PAID',?,?)",
                (inv_id,user_id,plan,amount,gst,total,payment_id,order_id,
                 datetime.now().strftime("%Y-%m-%d"), (datetime.now()+timedelta(days=30)).strftime("%Y-%m-%d")))
            c.execute("UPDATE subscriptions SET plan=?,price=?,expires_at=?,status='ACTIVE',razorpay_sub_id=? WHERE user_id=?",
                (plan,amount,(datetime.now()+timedelta(days=30)).isoformat(),payment_id,user_id))
        return {"upgraded":True,"plan":plan,"invoice_id":inv_id,"total_charged":total,"gst":gst}

    def get_subscription(self, user_id: str) -> dict:
        with self._conn() as c:
            row = c.execute("SELECT * FROM subscriptions WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            self.create_subscription(user_id, "FREE")
            return {"plan":"FREE","status":"ACTIVE","features":PLANS["FREE"]["features"]}
        sub = dict(row)
        sub["features"] = PLANS.get(sub["plan"], PLANS["FREE"])["features"]
        sub["plan_details"] = PLANS.get(sub["plan"], PLANS["FREE"])
        return sub

    def check_feature(self, user_id: str, feature: str) -> bool:
        sub = self.get_subscription(user_id)
        f = sub.get("features", {})
        val = f.get(feature, False)
        if isinstance(val, bool): return val
        if isinstance(val, int): return val != 0
        return bool(val)

    def meter_usage(self, user_id: str, metric: str, value: float = 1):
        period = datetime.now().strftime("%Y-%m")
        with self._conn() as c:
            c.execute("INSERT INTO usage_meter(user_id,metric,value,billing_period,recorded_at) VALUES(?,?,?,?,?)",
                (user_id,metric,value,period,datetime.now().isoformat()))

    def get_invoices(self, user_id: str) -> List[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM invoices WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
        return [dict(r) for r in rows]

    def create_razorpay_order(self, user_id: str, plan: str) -> dict:
        """Returns order details for Razorpay frontend integration"""
        if plan not in PLANS: return {"error":"Invalid plan"}
        amount = PLANS[plan]["price"]
        gst = round(amount * 0.18, 2)
        order_id = f"order_{secrets.token_hex(10)}"
        return {
            "order_id": order_id,
            "amount": int((amount + gst) * 100),  # Razorpay uses paise
            "currency": "INR",
            "plan": plan,
            "amount_display": amount,
            "gst": gst,
            "total": amount + gst,
            "razorpay_key": "rzp_test_PLACEHOLDER",  # Replace with actual key
            "prefill": {"user_id": user_id},
            "notes": {"plan": plan, "user_id": user_id},
        }

    def admin_revenue_stats(self) -> dict:
        with self._conn() as c:
            total_rev = c.execute("SELECT SUM(total_amount) FROM invoices WHERE status='PAID'").fetchone()[0] or 0
            by_plan = c.execute("SELECT plan,COUNT(*) cnt,SUM(total_amount) rev FROM invoices WHERE status='PAID' GROUP BY plan").fetchall()
            mrr = c.execute("SELECT SUM(price) FROM subscriptions WHERE status='ACTIVE' AND plan!='FREE'").fetchone()[0] or 0
        return {"total_revenue":round(total_rev,2),"mrr":round(mrr,2),"by_plan":[dict(r) for r in by_plan]}

billing = BillingEngine()
