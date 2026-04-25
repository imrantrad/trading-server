"""
Smart AI Customer Care — Hybrid Module
- Pre-populated Knowledge Base (saves AI costs)
- NLP for natural language matching
- Empathetic, human-like responses
- Escalation to live support
"""
import re, json, time
from typing import List, Dict, Optional

# ═══ KNOWLEDGE BASE ═══════════════════════════════════════
KB = {
    # TRADING
    "how_to_trade": {
        "keywords": ["how trade","kaise trade","execute order","order kaise","buy sell","trade karna"],
        "response": "Trading karna bahut simple hai! 😊\n\n**Steps:**\n1. **TRADE tab** kholo\n2. Instrument choose karo (NIFTY/BANKNIFTY)\n3. BUY ya SELL select karo\n4. Strike price aur lots fill karo\n5. Stop Loss aur Target set karo\n6. **EXECUTE** button dabao\n\n💡 **Pro Tip:** NLP box mein directly type karo — *'buy nifty atm call if rsi under 30 sl 100 target 300'* — sab auto-fill ho jaata hai!",
        "category": "trading"
    },
    "nlp_order": {
        "keywords": ["nlp","natural language","type trade","auto fill","hinglish","hindi trade"],
        "response": "NLP Order Entry aapki sabse powerful feature hai! 🚀\n\nBas type karo jaise aap bolte ho:\n- *'buy nifty atm call if rsi under 30 sl 100 target 300'*\n- *'sell banknifty weekly iron condor vix above 15'*\n- *'kharido nifty 2 lots subah ema crossover'*\n\n◆ PARSE dabao → sab columns auto-fill!\n▶ PARSE+EXEC dabao → seedha execute!\n\n500+ conditions support karta hai — RSI, EMA, VIX, FII flow, sab kuch! ✅",
        "category": "trading"
    },
    "paper_trading": {
        "keywords": ["paper trade","paper trading","practice","demo trade","virtual","fake money","test"],
        "response": "Paper Trading mein real paise nahi lagte — sirf practice ke liye! 🎯\n\n**Kaise use karein:**\n- MODE = PAPER select karo (default)\n- Normally trade karo\n- Real market prices pe simulate hoga\n- P&L track hoga bina real risk ke\n\n**Reset karna ho toh:**\nRISK tab → Emergency → ↺ RESET PAPER ENGINE\n\nPehle 15+ days paper trading karo phir live jaao! ✅",
        "category": "trading"
    },
    "stop_loss": {
        "keywords": ["stop loss","stoploss","sl","loss limit","trailing","trail sl","protect loss"],
        "response": "Stop Loss aapki capital protect karta hai! 🛡️\n\n**Types:**\n- **Fixed SL:** Entry se fixed points pe stop (e.g., SL = 100 pts)\n- **Trailing SL:** Profit ke saath SL bhi move karta hai\n\n**Setting karna:**\nOrder entry mein SL (pts) field fill karo\nTrailing SL ke liye TRAILING SL field use karo\n\n**Example:** Entry 100, SL 50 means agar price 50 se below aaya toh auto close!\n\n💡 SL hamesha lagao — kabhi skip mat karo! Professional traders ka rule #1 hai.",
        "category": "trading"
    },
    # SUBSCRIPTION
    "subscription_plans": {
        "keywords": ["plan","subscription","price","pricing","free plan","pro plan","upgrade","cost","kitne paise","fees"],
        "response": "Hamare 4 plans hain — apni zaroorat ke hisaab se choose karo! 💎\n\n| Plan | Price | Best For |\n|------|-------|----------|\n| **FREE** | ₹0 | Beginners, practice |\n| **BASIC** | ₹499/mo | Serious traders |\n| **PRO** ⭐ | ₹1499/mo | Professional traders |\n| **INSTITUTIONAL** | ₹4999/mo | Firms & HNIs |\n\n**PRO plan recommended** — AI Engine, unlimited strategies, 12-month backtest sab milta hai!\n\nUpgrade karne ke liye: PROFILE → 💳 PLANS tab",
        "category": "subscription"
    },
    "upgrade_plan": {
        "keywords": ["upgrade","how upgrade","plan change","kaise upgrade","payment","buy plan"],
        "response": "Plan upgrade karna bahut easy hai! 💳\n\n**Steps:**\n1. Dashboard mein **👤 PROFILE** tab kholo\n2. **💳 PLANS** tab select karo\n3. Apna plan choose karo\n4. **UPGRADE PLAN** button dabao\n\nAbhi simulation mode mein hai — real payment gateway (Razorpay) soon integrate hoga!\n\nKoi problem? Hum yahan hain! 😊",
        "category": "subscription"
    },
    "free_vs_pro": {
        "keywords": ["free vs pro","difference","kya milta","features","what included","pro features"],
        "response": "PRO plan mein yeh sab milta hai jo FREE mein nahi! ⚡\n\n✅ **AI Engine** — Autonomous strategy synthesis\n✅ **Unlimited Strategies** — Save as many as you want\n✅ **12 Month Backtest** — Full historical analysis\n✅ **Live Trading API** — Zerodha/Angel integration\n✅ **Unlimited Alerts** — Never miss a signal\n✅ **Priority Support** — Fast response\n\nFREE mein: 3 strategies, 1 month backtest, no AI engine\n\n💡 PRO = ₹1499/mo = ₹50/day — ek accha trade se recover!",
        "category": "subscription"
    },
    # AI ENGINE
    "ai_engine": {
        "keywords": ["ai engine","artificial intelligence","ai strategy","machine learning","ai signal","genetic","lstm","rl"],
        "response": "TRD AI Engine — Ek autonomous trading brain! 🤖\n\n**Architecture:**\n🧬 **Genetic Algorithm** — Strategy DNA evolve karta hai\n🧠 **LSTM Neural Net** — Hidden patterns discover karta hai\n⚡ **RL (PPO/SAC)** — Self-optimization karta hai\n\n**Kaise use karein:**\n1. AI ENGINE tab → 🧬 EVOLVE dabao\n2. 5 generations evolve hogi\n3. Best strategies approved hogi (62%+ WR required)\n4. **USE SIGNAL** → Order entry auto-fill!\n\n🔴 Circuit Breaker active rehta hai — VIX > 35 pe automatically ruk jaata hai!\n\nYeh PRO plan feature hai! 🌟",
        "category": "ai"
    },
    "ai_signal": {
        "keywords": ["ai signal","signal kya","buy signal","sell signal","regime","market regime","pattern"],
        "response": "AI Signal aapko bataata hai kab buy/sell karna chahiye! ⚡\n\n**Kaise get karein:**\nAI ENGINE tab → ⚡ AI SIGNAL button\n\n**Signal types:**\n- BUY_CE — Bullish momentum\n- BUY_PE — Bearish expected\n- SELL_CE/PE — Premium collection\n- IRON_CONDOR — Rangebound market\n- WAIT — No clear signal\n\n**Hidden Regime Detection:**\n🔍 REGIME button → Market ka hidden pattern detect karta hai!\n- Trending Up/Down, Rangebound, High Volatility detect karta hai\n\n⚠️ AI signals guarantee nahi hain — apna judgment bhi use karo!",
        "category": "ai"
    },
    # BACKTEST
    "backtest": {
        "keywords": ["backtest","back test","historical","test strategy","past data","performance test","kitna profit"],
        "response": "Backtest se aap dekh sakte ho ki strategy pehle kaisi perform karti! 📊\n\n**Kaise use karein:**\n1. **∞ BACKTEST** tab kholo\n2. Strategy select karo (10 built-in hain!)\n3. **Apna capital** enter karo (e.g., ₹1,00,000)\n4. Period choose karo (1/3/6/12 months)\n5. **RUN BACKTEST** dabao\n\n**Jo milega:**\n📅 **Date-wise P&L Calendar** — Har din ka result\n📈 Monthly breakdown\n🏆 Best/Worst days\n📉 Drawdown analysis\n\nClick karo calendar cell pe → us din ka detail milega! ✅",
        "category": "backtest"
    },
    # STRATEGIES
    "save_strategy": {
        "keywords": ["save strategy","apni strategy","create strategy","strategy banao","nlp strategy","custom strategy"],
        "response": "Apni khud ki strategy save kar sakte ho! ⭐\n\n**2 tarike hain:**\n\n**1. NLP Builder (Easy):**\nSTRATEGIES tab → ◆ NLP BUILDER\nType karo: *'buy nifty if rsi under 30 sl 100 target 300'*\n→ PARSE → Auto-fill → SAVE!\n\n**2. Manual:**\nStrategy name, instrument, entry/exit conditions, SL, target manually fill karo\n\n💡 **Tip:** NLP se banao — bahut fast hai aur 500+ conditions support karta hai!\n\nStrategy save hone ke baad BACKTEST aur PAPER TEST kar sako ge! 🚀",
        "category": "strategies"
    },
    "builtin_strategies": {
        "keywords": ["builtin strategy","built in","10 strategies","theta decay","iron condor","orb","vwap","gap fade"],
        "response": "10 proven high win-rate strategies available hain! 🏆\n\n| Strategy | Win Rate | Type |\n|----------|----------|------|\n| Weekly Iron Condor | 78% | Options Selling |\n| Max Pain Expiry | 76% | Expiry Day |\n| Weekly Theta Decay | 72% | Premium |\n| Gap Fade | 74% | Mean Reversion |\n| PCR Reversal | 71% | Contrarian |\n| FII Momentum | 69% | Institutional |\n| ORB | 68% | Breakout |\n| VWAP Pullback | 65% | Trend |\n| Supertrend+EMA | 63% | Trend |\n| BankNifty Scalp | 62% | Scalping |\n\nSTRATEGIES tab → ★ 10 BUILT-IN → BACKTEST ya USE karo!",
        "category": "strategies"
    },
    # SCANNER
    "scanner": {
        "keywords": ["scanner","market scan","opportunity","signal scan","best stock","konsa trade","which trade"],
        "response": "Market Scanner automatically best opportunities dhundta hai! 🔍\n\n**Kaise use karein:**\nSCANNER tab → ◎ SCAN NOW\n\n**Jo scan karta hai:**\n- Momentum opportunities\n- Mean reversion setups\n- Options selling opportunities\n- PCR extremes\n- IV rank opportunities\n- FII flow signals\n- VIX-based strategies\n- Breakout patterns\n\n**Directly trade karo:**\nResult mein **USE** button dabao → Order entry auto-fill!\n\n💡 Market open hone ke 30 min baad scan karo — best signals milte hain!",
        "category": "scanner"
    },
    # TECHNICAL
    "offline": {
        "keywords": ["offline","not working","server down","connection error","api error","nahi chal raha","band hai"],
        "response": "Server connection issue! Yeh try karo: 🔧\n\n**Quick fixes:**\n1. Page **hard refresh** karo (Ctrl+Shift+R)\n2. Internet connection check karo\n3. 2-3 minute wait karo — server restart ho sakta hai\n4. Incognito/Private mode mein try karo\n\n**Agar phir bhi nahi chala:**\nYeh app Cloudflare tunnel use karta hai jo restart pe URL change karta hai — permanent fix ke liye Cloudflare Named Tunnel aana chahiye!\n\nHum actively kaam kar rahe hain permanent server setup ke liye! Thoda wait karein. 🙏",
        "category": "technical"
    },
    "greeks": {
        "keywords": ["greeks","delta","theta","gamma","vega","black scholes","option price","premium"],
        "response": "Options Greeks — Premium ka breakdown! 📐\n\n**Delta (Δ):** Premium kitna change hoga agar spot ₹1 move kare\n- CE Delta: 0 to 1 | PE Delta: -1 to 0\n- ATM Delta ≈ 0.5\n\n**Theta (θ):** Har din kitna premium decay hota hai\n- Seller ka dost, buyer ka dushman!\n\n**Gamma (Γ):** Delta kitni speed se change hota hai\n- ATM options mein highest\n\n**Vega (ν):** IV 1% badhe toh premium kitna change hoga\n\n**Calculator use karo:**\nCALC tab → ◆ BLACK-SCHOLES → Spot, Strike, DTE, IV fill karo → Calculate!",
        "category": "education"
    },
    "kill_switch": {
        "keywords": ["kill switch","emergency stop","stop trading","trading band","panic","loss limit"],
        "response": "Kill Switch aapka emergency brake hai! 🛑\n\n**Kab use karein:**\n- Unusual market movement\n- Technical problem\n- Daily loss limit hit\n- Emotional trading rok'na ho\n\n**Kaise activate karein:**\n- Header mein ■ KILL button\n- Ya RISK tab → Emergency Controls\n\n**Effect:**\n- Koi naya trade execute nahi hoga\n- Existing positions safe rahenge\n- Resume ke liye ▶ RESUME dabao\n\n💡 Daily loss limit set karo PROFILE → SETTINGS mein — auto protection ke liye!",
        "category": "risk"
    },
    "risk_management": {
        "keywords": ["risk management","risk kitna","position size","lot size","capital risk","max loss","drawdown"],
        "response": "Professional risk management essential hai! ⚠️\n\n**Position Sizer use karo:**\nRISK tab → Position Sizer\n- Capital enter karo\n- Risk % (recommend: 1-2%)\n- SL points\n→ Optimal lots automatically calculate!\n\n**Golden Rules:**\n✅ Per trade risk: 1-2% of capital\n✅ Daily loss limit: 3% max\n✅ Max drawdown: 10% se kam\n✅ Consecutive losses: 3 ke baad break lo\n✅ Never average losing positions\n\n**RISK tab mein live meters hain** — daily limit, drawdown, positions sab track hota hai! 📊",
        "category": "risk"
    },
    "profile_settings": {
        "keywords": ["profile","settings","account","capital set","broker","telegram","notification","theme"],
        "response": "Profile Settings mein sab customize kar sakte ho! 👤\n\n**PROFILE tab kholo:**\n\n⚙️ **Settings:** Capital, risk %, broker, Telegram ID\n💳 **Plans:** Subscription upgrade\n🎨 **Themes:** 6 themes — Dark, Midnight, Matrix, Cosmic, Solarized, Light\n🔔 **Alerts:** Trade, SL, target notifications\n\n**Themes lagane ke liye:**\nPROFILE → 🎨 THEMES tab → Click karo!\n\n💡 Telegram Chat ID add karo — trade alerts directly Telegram pe aayenge! 📱",
        "category": "profile"
    },
    "expiry": {
        "keywords": ["expiry","expiry date","weekly expiry","monthly expiry","thursday","last thursday","theta"],
        "response": "Expiry information REPORTS tab mein milti hai! 📅\n\n**REPORTS tab → 📅 EXPIRY CALENDAR**\n- Weekly expiry date\n- Monthly expiry date\n- Kitne din bache\n- Theta warning\n\n**NSE Expiry Schedule:**\n- NIFTY: Every Thursday\n- BANKNIFTY: Every Wednesday\n- FINNIFTY: Every Tuesday\n- SENSEX: Every Friday\n\n⚠️ Expiry ke din options bahut fast move karte hain — extra caution rakhna!\n\n💡 Max Pain strategy expiry pe best work karti hai! STRATEGIES tab mein dekho.",
        "category": "education"
    },
    "how_to_use": {
        "keywords": ["how to use","kaise use","guide","tutorial","help","start","shuru","beginner","new user","getting started"],
        "response": "TRD v12.3 mein aapka swagat hai! 🎉\n\n**Quick Start Guide:**\n\n**Step 1:** TRADE tab → MODE = PAPER select karo\n**Step 2:** Instrument choose karo (NIFTY recommended for beginners)\n**Step 3:** NLP box mein type karo ya manually fill karo\n**Step 4:** Execute karo!\n\n**Important tabs:**\n📊 TRADE — Order execution\n⚡ RISK — Risk monitoring\n★ STRATEGIES — Pre-built strategies\n∞ BACKTEST — Strategy testing\n🤖 AI ENGINE — AI signals\n\n💡 **Best starting point:**\n1. Pehle BACKTEST tab mein strategies test karo\n2. Phir PAPER trading se practice karo (15+ days)\n3. Phir live trading consider karo\n\nKoi bhi sawaal ho — hum yahan hain! 😊",
        "category": "general"
    }
}

class CustomerCare:
    def __init__(self):
        self.sessions = {}  # user_id -> conversation history
        self.escalated = set()  # users who need human support
    
    def _find_kb_answer(self, query: str) -> Optional[Dict]:
        """Fast KB lookup — saves AI costs"""
        q = query.lower().strip()
        best_match = None
        best_score = 0
        
        for key, item in KB.items():
            score = 0
            for kw in item["keywords"]:
                if kw in q:
                    score += len(kw.split())  # longer match = higher score
            if score > best_score:
                best_score = score
                best_match = item
        
        return best_match if best_score > 0 else None
    
    def _humanize(self, response: str, user_name: str = "Friend") -> str:
        """Make response feel human and warm"""
        greetings = ["", ""]  # no prefix needed, already in response
        return response
    
    def chat(self, user_id: str, message: str, user_name: str = "Friend") -> Dict:
        """Main chat handler"""
        # Init session
        if user_id not in self.sessions:
            self.sessions[user_id] = {"history": [], "context": None}
        
        session = self.sessions[user_id]
        msg_lower = message.lower().strip()
        
        # Greeting detection
        greetings = ["hi","hello","hey","namaste","namaskar","hii","helo","good morning","good evening","sat sri akal","jai hind"]
        if any(g in msg_lower for g in greetings):
            return {
                "response": f"Namaste {user_name}! 🙏 Main TRD Support hoon.\n\nAapki kaise madad kar sakta hoon?\n\nAap pooch sakte hain:\n• Trading kaise karein\n• Plans & pricing\n• AI Engine kaise use karein\n• Strategies & backtest\n• Technical issues\n\nYa seedha apni problem type karo! 😊",
                "category": "greeting",
                "kb_hit": True,
                "suggestions": ["Trading kaise karein?", "Plans & Pricing", "AI Signals kaise kaam karte hain?"]
            }
        
        # Thank you
        if any(w in msg_lower for w in ["thank","thanks","shukriya","dhanyawad","thx","ty"]):
            return {
                "response": "Bahut bahut shukriya! 🙏 Khushi hui ki madad kar paya.\n\nKoi aur sawaal ho toh zaroor poochein — hum hamesha yahan hain! 😊\n\nHappy Trading! 📈",
                "category": "thanks",
                "kb_hit": True,
                "suggestions": []
            }
        
        # Human agent request
        if any(w in msg_lower for w in ["human","real person","agent","support team","call","complaint","manager"]):
            self.escalated.add(user_id)
            return {
                "response": "Bilkul samajh gaya! 🙏 Main aapko humari support team se connect kar raha hoon.\n\n**Escalation initiated!**\n\nHumari team 2-4 business hours mein respond karegi.\n\n📧 Email: support@trd.app\n📱 Telegram: @TRD_Support\n\nTab tak main aapki madad karne ki koshish karta hoon — kya specific problem hai?",
                "category": "escalation",
                "kb_hit": True,
                "escalated": True,
                "suggestions": []
            }
        
        # KB lookup
        kb_result = self._find_kb_answer(message)
        if kb_result:
            session["context"] = kb_result["category"]
            session["history"].append({"role": "user", "msg": message})
            session["history"].append({"role": "bot", "msg": kb_result["response"][:100]})
            
            # Generate contextual suggestions
            suggestions = self._get_suggestions(kb_result["category"])
            
            return {
                "response": kb_result["response"],
                "category": kb_result["category"],
                "kb_hit": True,
                "suggestions": suggestions
            }
        
        # Fallback — contextual response
        fallback = self._contextual_fallback(message, session.get("context"))
        return {
            "response": fallback,
            "category": "fallback",
            "kb_hit": False,
            "suggestions": ["Trading guide", "Subscription plans", "Talk to support"]
        }
    
    def _get_suggestions(self, category: str) -> List[str]:
        sugg_map = {
            "trading": ["NLP trading kaise karein?", "Paper trading guide", "Risk management tips"],
            "subscription": ["FREE vs PRO difference", "Payment methods", "Refund policy"],
            "ai": ["AI signal accuracy?", "Paper test kaise karein?", "Regime detection"],
            "backtest": ["Strategy comparison", "Best win-rate strategy", "Backtest accuracy"],
            "strategies": ["10 built-in strategies", "NLP strategy builder", "Community strategies"],
            "scanner": ["Best scan time?", "Scanner accuracy", "Custom scan setup"],
            "risk": ["Kill switch guide", "Daily loss limit", "Position sizing"],
            "education": ["Options basics", "Greeks explained", "Expiry strategy"],
            "general": ["Quick start guide", "Video tutorials", "Contact support"],
        }
        return sugg_map.get(category, ["Quick guide", "Pricing", "Support"])
    
    def _contextual_fallback(self, message: str, context: str) -> str:
        return f"""Main samjha — aap pooch rahe hain: *"{message}"*

Iska seedha jawab mujhe pata nahi, lekin main koshish karta hoon! 🙏

**Yeh try karo:**
• Apna sawaal thoda differently type karo
• Ya in mein se kuch poochho:
  - "How to trade?" — Trading guide
  - "Plans pricing" — Subscription info  
  - "AI signals" — AI Engine help
  - "Backtest kaise karein?" — Backtest guide

**Ya directly support se baat karo:**
Type karo *"talk to human"* — main connect karta hoon! 😊

Main sikhta rehta hoon — aapka feedback bahut important hai! 🌟"""

care = CustomerCare()
