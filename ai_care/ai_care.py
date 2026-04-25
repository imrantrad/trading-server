"""Smart AI Customer Care v12.3 - Knowledge Base + NLP"""
import json, sqlite3, os, random
from datetime import datetime
from typing import List

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../database/ai_care.db")

KB = {
    "hello": "Hello! 👋 Welcome to TRD v12.3 Support! I\'m here to help with trading, strategies, AI engine, or any questions. What can I help you with?",
    "help": "I can help with: 📊 Trading | ∞ Backtest | ★ Strategies | 🤖 AI Engine | 💳 Plans | ⚡ Risk | ◆ Options | 👤 Account. Just ask!",
    "trade": "Go to TRADE tab → Select Instrument → Action (BUY/SELL) → Option Type → Enter Strike, Lots, Price, SL, Target → EXECUTE. Or use the NLP box — type naturally like \'buy nifty atm call sl 100\'! 🚀",
    "nlp": "Our NLP understands natural language in English, Hindi, Hinglish! Type: \'buy nifty atm call if rsi below 30 sl 100 target 300\'. It auto-fills ALL fields instantly! ✨",
    "paper": "Paper trading = practice with virtual ₹5L — zero risk, same features as live. Perfect for testing strategies! Go to TRADE tab, MODE = PAPER.",
    "stop loss": "SL is in POINTS. If CE entry ₹150 with SL 100pts → exits at ₹50. Always use SL to protect capital! Trailing SL automatically moves your stop as price moves in your favor.",
    "lot": "Lot sizes: NIFTY=50, BANKNIFTY=15, FINNIFTY=40, SENSEX=10. Use Position Sizer in RISK tab to calculate optimal lots for your capital.",
    "backtest": "BACKTEST tab → Select Strategy → Enter YOUR capital → Choose period → RUN. See date-wise calendar (🟢 profit / 🔴 loss), monthly breakdown, best/worst days! 📊",
    "strategy": "STRATEGIES tab → ◆ NLP BUILDER → Type strategy naturally → PARSE → auto-fills all fields → SAVE. Also 10 built-in strategies with 62-78% win rates!",
    "iron condor": "Iron Condor = Sell OTM Call + Buy higher Call + Sell OTM Put + Buy lower Put. Best in low-VIX, rangebound. Our built-in Weekly Iron Condor has 78% WR! 🎯",
    "ai": "AI ENGINE tab: 🧬 EVOLVE generates strategies using Genetic Algorithms + LSTM + RL(PPO). ⚡ AI SIGNAL gives entry/SL/target. 🔍 REGIME detects market conditions. Circuit Breaker stops AI at VIX>35.",
    "signal": "AI ENGINE tab → Select instrument → ⚡ AI SIGNAL. Get entry price, SL, target with confidence %. Click USE SIGNAL to auto-load to order entry!",
    "regime": "Market Regime Detection uses unsupervised ML to find: TRENDING_UP, TRENDING_DOWN, RANGEBOUND, HIGH_VOLATILITY, ULTRA_LOW_VOL. Each regime has an optimal strategy.",
    "plan": "FREE (₹0): 3 strategies, 1mo BT | BASIC (₹499): 20 strategies, 6mo BT, Scanner | PRO (₹1499): Unlimited, AI Engine, Live API | INSTITUTIONAL (₹4999): 5yr BT, Multi-user, White Label.",
    "subscribe": "PROFILE tab → 💳 PLANS → Select plan → UPGRADE. Payment via Razorpay (UPI/Cards/NetBanking). GST invoice auto-generated. Cancel anytime.",
    "free": "FREE plan: 3 strategies, 1-month backtest, paper trading (50 trades), basic NLP. Upgrade to PRO for unlimited strategies, AI signals, and live trading API.",
    "profile": "PROFILE tab: Update name, capital, risk %, broker preference, Telegram ID for alerts. Sub-tabs: ⚙ Settings | 💳 Plans | 🎨 Themes | 🔔 Alerts.",
    "theme": "PROFILE → 🎨 THEMES → Choose: Dark, Midnight Blue, Matrix Green, Cosmic Purple, Solarized, Light. Saves automatically! 🎨",
    "telegram": "For Telegram alerts: 1) Create bot with @BotFather 2) Get Chat ID from @userinfobot 3) Enter in PROFILE → Settings → Telegram Chat ID.",
    "kill switch": "Kill Switch STOPS all trading instantly. Press ■ KILL (header or RISK tab). Resume with ▶ RESUME. Use during crashes, network issues, or when limits are hit!",
    "risk": "RISK tab: Set Daily Loss Limit (default 3%), Max Drawdown (10%), Max Positions (5), Max Trades/day (10). System auto-stops when limits breached. Position Sizer calculates optimal lots.",
    "offline": "If OFFLINE: 1) Check internet 2) Server may be restarting (wait 2 min) 3) Hard refresh Ctrl+Shift+R 4) Tunnel URL may have changed. If persists, contact support.",
    "greeks": "OPTIONS tab → GREEKS CALCULATOR → Enter Spot/Strike/DTE/IV/Type → CALC. Shows: Δ Delta (price move), Γ Gamma (delta change), θ Theta (daily decay), ν Vega (volatility).",
    "delta": "Delta = option price change per ₹1 move in underlying. CE: 0 to +1, PE: -1 to 0. ATM ≈ 0.5 delta. High delta = more sensitive to price moves.",
    "theta": "Theta = daily time decay. θ = -₹2.5 means option loses ₹2.50/day. Option SELLERS profit from theta; BUYERS lose. Choose selling strategies for consistent theta income.",
    "vix": "VIX = India Volatility Index. Below 13: Ultra low, sell premium. 13-18: Normal. 18-25: Elevated. Above 25: High risk. Above 35: Extreme — Circuit Breaker activates!",
    "zerodha": "Zerodha integration: Get API key from kite.zerodha.com → My Apps → Add to server config. Currently PAPER mode. Live needs broker API keys. Supports Zerodha, Angel, Fyers.",
    "contact": "📧 support@trd.app | 💬 Telegram: @TRDSupport | Response: PRO < 2hrs, Free < 24hrs. For urgent trading issues, use Kill Switch first!",
    "scanner": "SCANNER tab → ◎ SCAN NOW. Scans all instruments for opportunities with strategy name and confidence %. Click USE to auto-fill order entry!",
    "options chain": "OPTIONS tab → Select instrument → DTE → LOAD CHAIN. Shows CE/PE: OI, LTP, Delta, Theta for each strike. ATM highlighted in amber.",
    "iv rank": "IV Rank = where current IV sits in 1-year range. >70% = high IV (sell premium), <30% = low IV (buy premium). Get it in SCANNER tab → IV RANK.",
    "margin": "OPTIONS tab → MARGIN CALC → Enter instrument/lots/price → CALCULATE. Shows required margin, contract value, and max lots possible with ₹5L capital.",
    "report": "REPORTS tab: 📊 Daily, 📈 Weekly, ∑ Performance (all-time), 📅 Expiry Calendar (days to next expiry with theta warning).",
    "journal": "JOURNAL tab: Log each trade with emotion, rating, mistakes, lessons. Builds self-awareness and improves discipline. View trade history and P&L stats.",
    "admin": "ADMIN tab (PRO+): Real-time dashboard showing users, revenue, MRR, AI strategies, feature usage, plan distribution, and security audit logs.",
}

class AICare:
    def __init__(self):
        self._init_db()

    def _conn(self):
        c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS chat_history(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT,role TEXT,message TEXT,timestamp TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT,message_id INTEGER,helpful INTEGER,timestamp TEXT DEFAULT CURRENT_TIMESTAMP);
            """)

    def _kb_lookup(self, query):
        q = query.lower().strip()
        for key, answer in KB.items():
            if key in q: return answer
        words = set(q.split())
        best, best_score = None, 0
        for key, answer in KB.items():
            score = sum(1 for w in key.split() if w in words and len(w) > 3)
            if score > best_score: best, best_score = answer, score
        return best if best_score > 0 else None

    def chat(self, user_id, message):
        with self._conn() as c:
            c.execute("INSERT INTO chat_history(user_id,role,message,timestamp) VALUES(?,?,?,?)",
                     (user_id,"user",message,datetime.now().isoformat()))
        ans = self._kb_lookup(message)
        intros = ["","Great question! ","Happy to help! ","Of course! ","Sure! "]
        if ans:
            response = random.choice(intros) + ans
            source = "knowledge_base"; confidence = 0.95
        else:
            response = f"Thanks for reaching out! 🙏 Your question about \"{message[:50]}\" has been noted. Our support team will respond shortly. Meanwhile, type \'help\' to see what I can assist with right now!"
            source = "fallback"; confidence = 0.5
        with self._conn() as c:
            cur = c.execute("INSERT INTO chat_history(user_id,role,message,timestamp) VALUES(?,?,?,?)",
                           (user_id,"assistant",response,datetime.now().isoformat()))
            mid = cur.lastrowid
        suggestions = self._suggestions(message)
        return {"response":response,"source":source,"confidence":confidence,"message_id":mid,"suggestions":suggestions,"timestamp":datetime.now().isoformat()}

    def _suggestions(self, q):
        q = q.lower()
        if any(w in q for w in ["trade","buy","sell"]): return ["How does NLP trading work?","How to set stop loss?","What is paper trading?"]
        if any(w in q for w in ["strategy","backtest"]): return ["What is the best strategy?","How to save strategy?","How does backtest work?"]
        if any(w in q for w in ["plan","price","subscribe"]): return ["What does PRO include?","How to upgrade?","What is FREE plan?"]
        if any(w in q for w in ["ai","signal"]): return ["How does AI engine work?","How reliable are signals?","What is market regime?"]
        return ["How to trade?","What are the plans?","How does AI work?"]

    def get_history(self, user_id, limit=30):
        with self._conn() as c:
            rows = c.execute("SELECT * FROM chat_history WHERE user_id=? ORDER BY timestamp DESC LIMIT ?",(user_id,limit)).fetchall()
        return [dict(r) for r in reversed(rows)]

    def save_feedback(self, user_id, msg_id, helpful):
        with self._conn() as c:
            c.execute("INSERT INTO feedback(user_id,message_id,helpful,timestamp) VALUES(?,?,?,?)",
                     (user_id,msg_id,1 if helpful else 0,datetime.now().isoformat()))

ai_care = AICare()
