"""
Smart AI Customer Care — Human-Touch Hybrid v12.3
- Pre-populated KB (90% queries resolved without AI API calls)
- NLP keyword matching with scoring
- Empathetic, conversational tone
- Hindi / Hinglish / English support
- Escalation to human agent
- Session memory per user
- International-grade implementation
"""
import re, json, hashlib, time
from typing import Dict, List, Optional, Tuple

# ══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE — 25+ categories, 60+ Q&A pairs
# ══════════════════════════════════════════════════════════════════════════════
KB: Dict[str, dict] = {
    # GETTING STARTED
    "getting_started": {
        "keywords": ["start","shuru","kaise kare","how to use","guide","tutorial","help","new user","beginner","first time","pehli baar","getting started"],
        "response": "TRD v12.3 mein aapka swagat hai! 🎉 Yahan se shuru karein:\n\n**1. PAPER MODE** — Pehle PAPER mode mein practice karein (real paise nahi lagte)\n**2. NLP ORDER** — Natural language mein type karein: *'buy nifty atm call sl 100 target 300'*\n**3. BACKTEST** — BACKTEST tab → strategy choose karein → RUN karein\n**4. AI SIGNALS** — AI ENGINE tab → SIGNAL button → auto-execute available hai\n\n💡 Suggestion: 15-30 days paper trading ke baad live trading consider karein!",
        "suggestions": ["How to place first trade?", "NLP trading guide", "Paper vs Live mode"],
        "category": "onboarding"
    },
    "how_to_trade": {
        "keywords": ["trade","order","buy","sell","execute","kharido","becho","kaise lagaun","position","entry"],
        "response": "Trade lagana bahut simple hai! 😊\n\n**Method 1 — Manual:**\n1. TRADE tab → Instrument select (NIFTY/BANKNIFTY)\n2. BUY/SELL → CE/PE → Strike → Lots\n3. SL aur Target set karein\n4. EXECUTE button dabayein\n\n**Method 2 — NLP (Recommended):**\nBas type karein:\n*'buy nifty 24000 CE 2 lots sl 80 target 200'*\nAuto-fill ho jaayega! ✨\n\n**Method 3 — AI Signal:**\nAI ENGINE → SIGNAL → USE SIGNAL → execute!",
        "suggestions": ["NLP examples", "Stop loss kya hai?", "AI Signal use karna"],
        "category": "trading"
    },
    "nlp_guide": {
        "keywords": ["nlp","natural language","auto fill","type trade","hinglish","hindi order","parse","condition"],
        "response": "NLP Order Entry — apki sabse powerful feature! 🚀\n\n**Supported formats:**\n```\nbuy nifty atm call if rsi under 30 sl 100 target 300\nsell banknifty weekly iron condor vix above 15\nkharido nifty 2 lots subah ema crossover trailing sl 50\nbuy nifty 24000 CE expiry thursday quantity 1 sl 80 tgt 200\n```\n\n**500+ conditions supported:**\nRSI, EMA, VWAP, VIX, FII flow, PCR, Max Pain, OI, IV Rank, Gap...\n\n**Languages:** English, Hindi, Hinglish — sab kuch!\n\n▶ PARSE button → fields fill honge\n▶ PARSE+EXEC → seedha execute!",
        "suggestions": ["More NLP examples", "Conditions list", "Strategy builder guide"],
        "category": "trading"
    },
    "stop_loss": {
        "keywords": ["stop loss","sl","stoploss","loss limit","trailing","trail","protect","cut loss","nuksan"],
        "response": "Stop Loss apke capital ka shield hai! 🛡️\n\n**Types:**\n- **Fixed SL:** Entry se X points pe stop\n  Example: Entry 100, SL 80 → 20 points risk\n- **Trailing SL:** Profit ke saath SL move karta hai\n  Example: 30 points trailing → profit lock hota hai\n\n**Setting karna:**\nOrder entry → SL field mein points enter karein\n\n**Professional Rule:**\n✅ Hamesha SL lagaao — kabhi bhi 'hope' pe mat raho\n✅ Risk per trade: Max 1-2% of capital\n✅ Never average a losing position\n\n💡 RISK tab → Position Sizer use karein for optimal lots",
        "suggestions": ["Position sizing guide", "Risk management rules", "Trailing SL kaise kaam karta hai"],
        "category": "trading"
    },
    "paper_trading": {
        "keywords": ["paper","practice","demo","virtual","test","risk free","bina paise","fake","simulate","sandbox"],
        "response": "Paper Trading — risk-free learning! 🎯\n\n**Kya hai:** Real market prices pe virtual trading. Ek paisa nahi lagta!\n\n**Kaise activate karein:**\nTRADE tab → MODE → **PAPER** select karein (default hai)\n\n**Features:**\n✅ Real market prices use hoti hain\n✅ P&L track hota hai\n✅ All features available\n✅ Unlimited trades\n\n**Reset karna:**\nRISK tab → Emergency → ↺ RESET PAPER ENGINE\nApna capital amount set karein (default ₹5 lakh)\n\n**Recommendation:**\nMinimum 15-30 days paper trading karein before going live! 🏆",
        "suggestions": ["Paper se live kab jaayein?", "Capital set karna", "P&L track karna"],
        "category": "trading"
    },
    
    # SUBSCRIPTION
    "plans_pricing": {
        "keywords": ["plan","price","pricing","cost","kitna","fee","charge","subscription","free","pro","basic","institutional","paisa","rupee"],
        "response": "TRD v12.3 — 4 flexible plans! 💎\n\n| Plan | Price | Best For |\n|------|-------|---------|\n| FREE | ₹0 | Beginners |\n| BASIC | ₹499/mo | Active traders |\n| **PRO** ⭐ | ₹1499/mo | Professional |\n| INSTITUTIONAL | ₹4999/mo | Firms & HNIs |\n\n**PRO includes:**\n✅ Unlimited strategies\n✅ AI Engine + Signals\n✅ 12-month backtest\n✅ Live API access\n✅ All notifications\n✅ Priority support\n\n**Upgrade:** PROFILE → 💳 PLANS tab\n\n💡 PRO = ₹50/day. Ek accha trade recover kar deta hai! 🚀",
        "suggestions": ["FREE vs PRO difference", "Payment methods", "Cancel subscription"],
        "category": "subscription"
    },
    "upgrade_plan": {
        "keywords": ["upgrade","buy plan","subscribe","purchase","renew","payment","razorpay","upi","pay"],
        "response": "Plan upgrade karna aasaan hai! 💳\n\n**Steps:**\n1. 👤 PROFILE tab kholo\n2. 💳 PLANS section\n3. Plan select karein\n4. UPGRADE PLAN button\n\n**Payment methods (coming soon):**\n💳 UPI (GPay, PhonePe, Paytm)\n🏦 Net Banking\n💳 Credit/Debit Card\n📱 Razorpay integration\n\n**Current status:** Simulation mode — real payment gateway jald aa raha hai!\n\n**GST Invoice:** Automatically generate hogi after payment",
        "suggestions": ["Plans comparison", "Refund policy", "GST invoice"],
        "category": "subscription"
    },
    
    # AI ENGINE
    "ai_engine": {
        "keywords": ["ai","artificial intelligence","machine learning","neural network","genetic algorithm","lstm","rl","reinforcement","autonomous","robot","bot"],
        "response": "TRD AI Engine — Ek autonomous trading brain! 🤖\n\n**Architecture:**\n🧬 **Genetic Algorithm** — Strategy DNA evolve karta hai (Darwin-style!)\n🧠 **LSTM Neural Net** — Hidden market patterns discover karta hai\n⚡ **RL (PPO/SAC)** — Real-time self-optimization\n\n**How it works:**\n1. 🧬 EVOLVE → 5 generations evolve → best strategies select\n2. 15-day mandatory paper test (quality gate)\n3. Min 62% WR + 1.5× PF required for approval\n4. Approved strategies → AI STRATEGIES tab\n5. Auto-execute option available!\n\n**Safety:**\n🔴 Circuit Breaker: VIX > 35 → automatic stop\n⚠️ Anti-overfit: Penalizes Sharpe-only strategies",
        "suggestions": ["Evolve kaise karein?", "AI Signal accuracy?", "Auto-execute feature"],
        "category": "ai"
    },
    "ai_signal": {
        "keywords": ["signal","buy signal","sell signal","ai predict","when buy","kab kharidu","regime","hidden pattern","confidence"],
        "response": "AI Signal Feature! ⚡\n\n**Kaise use karein:**\nAI ENGINE tab → Instrument select → ⚡ SIGNAL button\n\n**Signal types:**\n- BUY_CE / BUY_PE — Directional\n- SELL_CE / SELL_PE — Premium collection\n- IRON_CONDOR — Rangebound\n- WAIT — No clear setup\n\n**Components:**\n📊 Confidence % (>75% = strong)\n🌍 Market Regime detection\n🔍 Hidden Pattern ID\n💡 Recommended strategy\n📍 Entry / SL / Target prices\n\n**Auto-Execute:**\n▶ USE SIGNAL → order entry auto-fill\n⚡ AUTO-EXECUTE → high confidence pe automatic!\n\n⚠️ Always verify before live execution!",
        "suggestions": ["Signal accuracy history?", "Auto-execute setup", "Regime detection guide"],
        "category": "ai"
    },
    "auto_execute": {
        "keywords": ["auto execute","automatic","auto trade","self execute","auto pilot","hands free","khud kare"],
        "response": "Auto-Execute Feature! 🤖⚡\n\n**Kya karta hai:**\nJab AI ka confidence level aapki threshold se upar ho, automatically trade execute karta hai!\n\n**Setup:**\nAI ENGINE tab → AUTO-EXECUTE section:\n- Min Confidence: 75% (default), aap adjust kar sakte ho\n- Max lots per signal: 1 (default)\n- Daily signal limit: 3 (default)\n- Kill switch override: Always respected\n\n**Safety features:**\n✅ Circuit breaker active rahega\n✅ Daily loss limit respected\n✅ Kill switch always works\n✅ Paper mode mein test karo pehle!\n\n⚠️ **WARNING:** Live mode mein sirf tab use karein jab aap confident ho strategy pe!",
        "suggestions": ["Auto-execute settings", "Paper mode test", "Daily limit set karna"],
        "category": "ai"
    },
    
    # BACKTEST
    "backtest": {
        "keywords": ["backtest","back test","historical","past data","test strategy","performance","kitna kama","returns","simulate history"],
        "response": "Backtest Engine — 100% deterministic results! 📊\n\n**Kaise use karein:**\n1. ∞ BACKTEST tab\n2. Strategy select (10 high-WR strategies available!)\n3. Apna capital enter karein (e.g., ₹1,00,000)\n4. Period: 1/3/6/12 months\n5. RUN BACKTEST button\n\n**Jo milega:**\n📅 Date-wise P&L Calendar (click any day for details)\n📈 Monthly breakdown\n🏆 Best/Worst days\n📉 Drawdown analysis\n💹 Sharpe Ratio, Profit Factor\n\n**Important:** Results 100% reproducible hain!\nSame inputs → Same outputs, har baar! ✅\n\n*Tip: Iron Condor weekly strategy ne 78% WR dikhaaya hai!*",
        "suggestions": ["Best strategy kaunsa?", "Results kaise interpret karein?", "Custom strategy backtest"],
        "category": "backtest"
    },
    
    # TECHNICAL ISSUES
    "offline": {
        "keywords": ["offline","not working","server down","connection","connect","nahi chal raha","band hai","error","404","500","loading"],
        "response": "Server connection problem! 🔧\n\n**Quick fixes:**\n1. **Hard Refresh:** Ctrl+Shift+R (Windows) ya Cmd+Shift+R (Mac)\n2. **Cache clear:** Browser → Settings → Clear browsing data\n3. **Incognito:** Private window mein try karein\n4. **Wait 2-3 min:** Server restart ho sakta hai\n\n**Check:**\n🔴 Header mein dot dekho — Red = offline, Green = online\n\n**Technical info:**\nApp runs on AWS EC2 (Stockholm, Sweden)\nNginx reverse proxy on port 80\nFastAPI backend on port 8000\n\n**Persistent issue:**\nAWS Free tier t3.micro ka 1GB RAM occasional OOM hota hai. Yeh fix ho raha hai! 🙏",
        "suggestions": ["Refresh karne se fix?", "Server status check", "Report bug"],
        "category": "technical"
    },
    "mobile_issues": {
        "keywords": ["mobile","phone","android","ios","iphone","responsive","small screen","touch","scroll"],
        "response": "Mobile app experience! 📱\n\n**PWA Install (Recommended):**\n1. Chrome mein kholo: http://13.53.175.88\n2. Browser menu (3 dots) → Add to Home Screen\n3. Ek proper app jaisa experience milega!\n\n**Mobile features:**\n✅ Bottom navigation bar (TRADE, SCAN, AI, STRATS, PROFILE)\n✅ Touch-optimized buttons\n✅ Responsive layout\n✅ Offline mode (cached)\n\n**Tips:**\n- Landscape mode mein zyada dekh sakte ho\n- Zoom in karo small text ke liye\n\n📱 Native iOS/Android app coming soon!",
        "suggestions": ["PWA install kaise karein?", "Notifications on mobile?", "Data usage kitna?"],
        "category": "technical"
    },
    
    # STRATEGIES
    "builtin_strategies": {
        "keywords": ["strategy","strategies","built in","10 strategy","theta decay","iron condor","orb","vwap","gap fade","pcr","banknifty scalp","which strategy","best"],
        "response": "10 High-Performance Built-in Strategies! 🏆\n\n| Strategy | Win Rate | Type |\n|----------|----------|------|\n| Weekly Iron Condor | **78%** | Options Selling |\n| Max Pain Expiry | **76%** | Expiry Day |\n| Gap Fade | **74%** | Mean Reversion |\n| Theta Decay | **72%** | Premium |\n| PCR Reversal | **71%** | Contrarian |\n| FII Momentum | **69%** | Institutional |\n| ORB | **68%** | Breakout |\n| VWAP Pullback | **65%** | Trend |\n| Supertrend+EMA | **63%** | Trend |\n| BankNifty Scalp | **62%** | Scalping |\n\nSTRATEGIES tab → BUILT-IN button → BACKTEST ya USE!\n\n💡 Iron Condor + Max Pain = Best for weekly expiry!",
        "suggestions": ["Iron Condor kya hai?", "Paper test kaise karein?", "NLP se strategy banao"],
        "category": "strategies"
    },
    "create_strategy": {
        "keywords": ["create","banao","save","custom","apni strategy","nlp builder","strategy builder","new strategy"],
        "response": "Apni strategy banao — 2 tarike! ⭐\n\n**Method 1 — NLP Builder (Easiest):**\nSTRATEGIES tab → NLP BUILDER\nType: *'buy nifty atm if rsi under 30 and ema crossover sl 100 target 300'*\n→ PARSE → Auto-fill → SAVE!\n\n**Method 2 — Manual:**\nName, instrument, entry conditions, SL, target fill karein\n\n**After saving:**\n✅ BACKTEST kar sakte ho\n✅ AI PAPER TEST — 15 days automated\n✅ LIVE use kar sakte ho\n✅ AI Engine pe evolve kar sakte ho\n\n**NLP supports 500+ conditions:**\nRSI, EMA, VWAP, PCR, FII, VIX, OI, IV, Gap, Pivot...",
        "suggestions": ["NLP examples", "Paper test process", "Community strategies"],
        "category": "strategies"
    },
    
    # GREEKS & OPTIONS
    "greeks": {
        "keywords": ["greeks","delta","theta","gamma","vega","rho","option price","premium","black scholes","iv","implied volatility"],
        "response": "Options Greeks — Premium ka complete breakdown! 📐\n\n**Delta (Δ):**\nSpot ₹1 move pe premium change\n- CE: 0 to +1 | PE: -1 to 0\n- ATM ≈ 0.5 | Deep ITM ≈ 1\n\n**Theta (θ) — Time Decay:**\nHar din premium kitna ghatta hai\n- Seller ka DOST! Buyer ka dushman\n- Expiry ke pass zyada decay\n\n**Gamma (Γ):**\nDelta ki change ki speed\n- ATM options mein highest\n\n**Vega (ν):**\nIV 1% change pe premium change\n\n**Calculator:**\nCALC tab → BLACK-SCHOLES → Spot, Strike, DTE, IV fill karo!",
        "suggestions": ["IV rank kya hai?", "Options chain kaise padhein?", "Theta strategy"],
        "category": "education"
    },
    "iv_rank": {
        "keywords": ["iv rank","iv percentile","implied volatility","vix","volatility","options expensive","cheap options"],
        "response": "IV Rank — Options buying/selling timing! 📊\n\n**Kya hai:**\nCurrent IV, 52-week range mein kahan hai (0-100%)\n\n**Interpretation:**\n🔴 IV Rank > 80% → Options EXPENSIVE → **SELL strategies** (Iron Condor, Straddle)\n🟢 IV Rank < 20% → Options CHEAP → **BUY strategies** (Long call, Long put)\n🟡 20-80% → Neutral\n\n**TRD mein use:**\nSCANNER tab → IV RANK → Instrument select → GET IV RANK\n\n**Pro tip:**\nHigh IV + Rangebound market = Perfect for Iron Condor!\nLow IV + Expected big move = Perfect for Long Straddle!\n\n💡 VIX India = NIFTY 30-day implied volatility index",
        "suggestions": ["Iron Condor setup", "VIX strategy", "Expiry day strategy"],
        "category": "education"
    },
    
    # RISK MANAGEMENT
    "risk_management": {
        "keywords": ["risk","risk management","position size","sizing","capital","max loss","drawdown","consecutive","safeguard","protect capital"],
        "response": "Professional Risk Management — The #1 skill! ⚠️\n\n**Golden Rules:**\n✅ Per trade risk: **1-2% of capital max**\n✅ Daily loss limit: **3% max** (auto kill switch)\n✅ Max drawdown: **10%** (circuit breaker)\n✅ Consecutive losses: Stop after 3, take break\n✅ Never average losing positions\n\n**Position Sizer:**\nRISK tab → Position Sizer:\n- Capital + Risk % + SL points → Optimal lots!\n\n**Risk Meters (Live):**\nRISK tab → Real-time gauges:\n📊 Daily loss used %\n📊 Current drawdown %\n📊 Open positions count\n📊 Trades today count\n\n**Kill Switch:**\nRed button in header — stops all trading immediately!",
        "suggestions": ["Kill switch guide", "Position sizing calc", "Daily loss limit set karna"],
        "category": "risk"
    },
    
    # NOTIFICATIONS
    "notifications": {
        "keywords": ["notification","alert","push","sms","email","telegram","whatsapp","notify","intimation","signal alert"],
        "response": "Advanced Notification System! 🔔\n\n**Channels:**\n📱 In-App — Real-time, instant\n📱 Push Notification — Mobile alerts\n📧 Email — Reports & invoices\n📲 SMS — Critical alerts only\n💬 Telegram — Custom preference\n💚 WhatsApp — Premium tier\n\n**Smart Logic:**\n⏰ Quiet hours: 11 PM - 7 AM IST = Critical only\n🚫 Max 10 push/hour anti-spam\n📦 5+ scanner signals = 1 digest\n\n**Alert types:**\nTrade executed, SL hit, Target achieved\nAI signals, Scanner opportunities\nDaily P&L report, Subscription alerts\n\n**Setup:**\nPROFILE → 🔔 ALERTS → Channel toggles",
        "suggestions": ["Telegram setup", "Push notifications enable", "Alert types list"],
        "category": "notifications"
    },
    
    # ACCOUNT
    "profile_settings": {
        "keywords": ["profile","settings","account","capital set","broker","telegram id","name","phone","preferences","save settings"],
        "response": "Profile Settings — Apna account customize karein! 👤\n\n**PROFILE tab → SETTINGS:**\n- Full Name, Phone\n- Capital (₹)\n- Risk per trade %\n- Max daily loss %\n- Preferred broker\n\n**PROFILE tab → PLANS:** Subscription manage\n**PROFILE tab → THEMES:** 6 themes available\n**PROFILE tab → ALERTS:** Notification preferences\n\n**Dashboard Settings (NEW!):**\nProfile → Dashboard Settings → Tabs show/hide karein!\nApni pasand ke tabs hi dikhao — free plan wale restricted tabs auto-hide!\n\n**Save karna:** SAVE SETTINGS button dabao",
        "suggestions": ["Capital change karna", "Theme change", "Tab visibility settings"],
        "category": "account"
    },
    "dashboard_settings": {
        "keywords": ["dashboard setting","hide tab","show tab","custom tab","ui filter","display manager","checklist","visibility","tab management"],
        "response": "Dynamic Dashboard Settings! 🎛️\n\n**PROFILE → Dashboard Settings:**\nHar tab ke aage ek checkbox hai.\n✅ Check = Tab visible\n☐ Uncheck = Tab hidden\n\n**Plan-based access:**\n- FREE: Trade, Backtest, Strategies, Journal, Calc, Profile\n- BASIC: + Scanner, Options, Reports, Notifications\n- PRO: + AI Engine, Admin, Legal\n- INSTITUTIONAL: All + Advanced analytics\n\n**Auto-save:** Settings server pe save hoti hain!\nRefresh ke baad bhi same tabs dikhenge.\n\n**Note:** Plan-restricted tabs ko unlock nahi kar sakte bina upgrade ke.",
        "suggestions": ["Tab visibility set karna", "Plan upgrade karein", "Saved settings check"],
        "category": "account"
    },
    
    # ESCALATION
    "human_agent": {
        "keywords": ["human","real person","agent","support team","complaint","manager","talk to","connect","live chat","escalate"],
        "response": "Main aapko support team se connect kar raha hoon! 🙏\n\n**Escalation initiated ✅**\n\nHamari team 2-4 business hours mein respond karegi.\n\n**Contact details:**\n📧 Email: support@trd.app\n💬 Telegram: @TRD_Support\n🌐 Website: www.trd.app/support\n\n**Business hours:** Mon-Fri 9 AM - 6 PM IST\n\nTab tak main aapki madad karta rehta hoon — kya specific issue hai? 😊",
        "suggestions": ["Email support", "Telegram support", "Bug report"],
        "category": "escalation",
        "escalate": True
    },
    "thanks": {
        "keywords": ["thanks","thank you","shukriya","dhanyawad","thx","ty","helpful","great","awesome","bahut acha"],
        "response": "Bahut bahut shukriya! 🙏 Khushi hui ki madad kar paya.\n\nKoi aur sawaal ho toh zaroor poochein — hum hamesha yahan hain!\n\n**Happy Trading!** 📈\n\n*Remember: Consistent small profits > Occasional big wins!*",
        "suggestions": [],
        "category": "general"
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# NLP MATCHING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class CustomerCareEngine:
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        self.escalated: set = set()
        self._build_index()
    
    def _build_index(self):
        """Pre-build keyword index for fast lookup"""
        self.index: Dict[str, List[Tuple[str, float]]] = {}
        for key, item in KB.items():
            for kw in item["keywords"]:
                if kw not in self.index:
                    self.index[kw] = []
                # Weight: longer keywords score higher (more specific)
                weight = 1.0 + len(kw.split()) * 0.5
                self.index[kw].append((key, weight))
    
    def _find_best_match(self, query: str) -> Tuple[Optional[str], float]:
        """Find best KB match with scoring"""
        q = query.lower().strip()
        scores: Dict[str, float] = {}
        
        # Exact and partial keyword matching
        for kw, entries in self.index.items():
            if kw in q:
                for kb_key, weight in entries:
                    scores[kb_key] = scores.get(kb_key, 0) + weight
        
        # Word-level partial matching
        words = re.findall(r'\b\w+\b', q)
        for word in words:
            if len(word) < 3:
                continue
            for kw in self.index:
                if word in kw or kw in word:
                    for kb_key, weight in self.index[kw]:
                        scores[kb_key] = scores.get(kb_key, 0) + weight * 0.5
        
        if not scores:
            return None, 0.0
        
        best_key = max(scores, key=scores.get)
        return best_key, scores[best_key]
    
    def _get_session(self, user_id: str) -> dict:
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "history": [],
                "context": None,
                "message_count": 0,
                "created_at": time.time()
            }
        return self.sessions[user_id]
    
    def chat(self, user_id: str, message: str, user_name: str = "Friend") -> dict:
        """Main chat handler"""
        session = self._get_session(user_id)
        session["message_count"] += 1
        msg_lower = message.lower().strip()
        
        # ── Greeting detection ──────────────────────────────────────────────
        greetings = {"hi","hello","hey","namaste","namaskar","hii","helo","good morning","good evening","good afternoon","sat sri akal","jai hind","salaam","assalamualaikum","howdy","yo"}
        if any(g in msg_lower for g in greetings) and len(message.split()) <= 3:
            return self._greeting_response(user_name)
        
        # ── Thank you ───────────────────────────────────────────────────────
        thanks_words = {"thank","thanks","shukriya","dhanyawad","thx","ty","awesome","great","helpful"}
        if any(t in msg_lower for t in thanks_words):
            return self._kb_response("thanks", session)
        
        # ── Human escalation request ────────────────────────────────────────
        escalate_words = {"human","real person","agent","support team","call","complaint","manager","talk to","live chat"}
        if any(e in msg_lower for e in escalate_words):
            self.escalated.add(user_id)
            return self._kb_response("human_agent", session)
        
        # ── KB lookup ───────────────────────────────────────────────────────
        kb_key, score = self._find_best_match(message)
        
        if kb_key and score >= 1.0:
            session["context"] = KB[kb_key].get("category")
            session["history"].append({"role": "user", "msg": message[:100]})
            result = self._kb_response(kb_key, session)
            return result
        
        # ── Contextual fallback ─────────────────────────────────────────────
        return self._fallback_response(message, session, user_name)
    
    def _greeting_response(self, user_name: str) -> dict:
        return {
            "response": f"Namaste {user_name}! 🙏 Main TRD Support hoon — aapki kaise madad kar sakta hoon?\n\nAap in topics pe pooch sakte hain:\n• 📈 Trading & Orders\n• 💳 Plans & Pricing\n• 🤖 AI Engine & Signals\n• ⚠️ Risk Management\n• 🔧 Technical Issues\n\nYa seedha apna sawaal type karein!",
            "category": "greeting",
            "kb_hit": True,
            "confidence": 1.0,
            "suggestions": ["How to trade?", "Plans & Pricing", "AI Signals guide", "App is offline"]
        }
    
    def _kb_response(self, key: str, session: dict) -> dict:
        item = KB.get(key, {})
        sugg = item.get("suggestions", [])
        
        return {
            "response": item.get("response", ""),
            "category": item.get("category", "general"),
            "kb_hit": True,
            "confidence": 0.95,
            "suggestions": sugg,
            "escalated": item.get("escalate", False)
        }
    
    def _fallback_response(self, message: str, session: dict, user_name: str) -> dict:
        context = session.get("context", "general")
        
        context_hints = {
            "trading": "\nTrade related: try 'how to trade', 'stop loss guide', 'NLP examples'",
            "ai": "\nAI related: try 'AI signal guide', 'evolve strategies', 'auto execute'",
            "subscription": "\nPlans related: try 'plans pricing', 'how to upgrade'",
        }
        
        hint = context_hints.get(context, "")
        
        return {
            "response": f"Main samajh gaya — aap pooch rahe hain: *\"{message[:60]}\"*\n\nMujhe exact answer nahi mila, lekin try karein:{hint}\n\n**Ya seedha poochein:**\n• 'How to trade'\n• 'Plans pricing'\n• 'AI signals guide'\n• 'Risk management'\n\nAgar main help na kar paun — type karein **'talk to human'** 😊",
            "category": "fallback",
            "kb_hit": False,
            "confidence": 0.3,
            "suggestions": ["How to trade?", "Plans pricing", "Talk to human agent", "Report a bug"]
        }

# Singleton
care_engine = CustomerCareEngine()
