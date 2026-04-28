"""
Smart AI Customer Care v3.0 — Human-Touch Hybrid
- Dynamic responses with variations
- Context-aware conversation
- Hindi/Hinglish/English NLP
- Session memory & follow-up detection
- Empathetic tone
"""
import re, time, random
from typing import Dict, List, Tuple, Optional

# ── RESPONSE VARIATIONS (3 per topic) ────────────────────────────────────────
KB = {
    "greeting": {
        "keywords": ["hi","hello","hey","namaste","hii","helo","namaskar","good morning","good evening","good afternoon","sat sri akal","salaam","howdy","yo","sup"],
        "responses": [
            "Namaste! 🙏 Main TRD Support hoon. Aaj aapki kaise madad kar sakta hoon?\n\n**Quick links:**\n• 📈 Trading guide\n• 💳 Plans & pricing\n• 🤖 AI Engine\n• 🔧 Technical help",
            "Hello! 👋 TRD Support mein aapka swagat hai!\n\nKoi bhi sawaal poochein — trading se lekar technical issues tak, main hoon yahan! 😊",
            "Namaste ji! 🙏 Kaise hain aap?\n\nMain aapki har trading problem mein madad kar sakta hoon. Batayein kya chahiye?"
        ],
        "suggestions": ["How to place a trade?", "Plans & Pricing", "AI Signals guide", "App not connecting"]
    },
    "thanks": {
        "keywords": ["thanks","thank you","shukriya","dhanyawad","thx","ty","helpful","great","awesome","bahut acha","perfect","superb","zabardast"],
        "responses": [
            "Bahut khushi hui ki kaam aaya! 🙏 Happy Trading!\n\n*Pro tip: Consistent छोटे profits बड़े gains se better hote hain!* 📈",
            "Shukriya aapka! 😊 Koi aur sawaal ho toh zaroor batayein.\n\n**Remember:** Knowledge + Discipline = Profitable Trading! 💪",
            "Aapka bahut bahut shukriya! 🎉 Best of luck for your trades!\n\n*Rule #1: Capital protection > Profit making* 🛡️"
        ],
        "suggestions": []
    },
    "how_to_trade": {
        "keywords": ["trade","order","buy","sell","execute","kharido","becho","kaise lagaun","position","entry","order kaise","first trade","pehla trade"],
        "responses": [
            "**Trade karne ke 3 tarike hain! 🚀**\n\n**1. Manual Order:**\nTRADE tab → Instrument → BUY/SELL → CE/PE → Strike → Lots → SL/Target → EXECUTE\n\n**2. NLP (Sabse Easy):**\nType: *'buy nifty atm call sl 100 target 300'*\nAuto-fill ho jaata hai! ✨\n\n**3. AI Signal:**\nAI ENGINE → ⚡ SIGNAL → USE SIGNAL → Execute!\n\n💡 Pehle PAPER mode mein try karein!",
            "**Order Entry Guide! 📝**\n\nTop par TRADE tab kholo.\n\nInstrument choose karo: NIFTY / BANKNIFTY / FINNIFTY / SENSEX\n\nFir:\n→ Action: BUY ya SELL\n→ Type: CE, PE, ya FUT\n→ Strike price\n→ Lots (quantity)\n→ Entry price\n→ SL aur Target (important!)\n→ EXECUTE button!\n\n⚠️ Hamesha Stop Loss lagaao!",
            "**Pehla trade step by step! 🎯**\n\nStep 1: PAPER mode select karo (real money nahi lagega)\nStep 2: NIFTY choose karo\nStep 3: BUY + CE + ATM strike\nStep 4: Lots = 1\nStep 5: SL = 80 points, Target = 200 points\nStep 6: EXECUTE karo!\n\nP&L real-time track hoga. Practice karo! 💪"
        ],
        "suggestions": ["NLP examples", "Stop loss guide", "Paper vs Live mode"]
    },
    "nlp_guide": {
        "keywords": ["nlp","natural language","auto fill","type trade","hinglish","hindi order","parse","condition","voice order","text order"],
        "responses": [
            "**NLP Order Entry — Apki best feature! 🔥**\n\n**Examples:**\n```\nbuy nifty atm call rsi under 30 sl 100 target 300\nsell banknifty weekly iron condor vix above 15\nkharido nifty 2 lots subah ema crossover trailing sl 50\nbuy banknifty 46000 PE expiry thursday sl 60 tgt 180\n```\n\n**500+ conditions:** RSI, EMA, VIX, FII, PCR, IV, Gap, Pivot...\n\n▶ PARSE → auto-fill\n▶ PARSE+EXEC → seedha execute!",
            "**NLP Magic! ✨ Hinglish mein bolo, trade ho jaao!**\n\n*Kuch examples:*\n• `nifty call kharido agar rsi 30 se neeche ho sl 80`\n• `sell banknifty straddle weekly expiry vix above 18`\n• `buy 2 lots nifty 24000 CE thursday expiry`\n• `nifty iron condor range 23500 to 24500`\n\nLanguages: English, Hindi, Hinglish — sab supported! 🇮🇳",
            "**NLP Guide — 3 steps only! 📱**\n\n1. TRADE tab → NLP ORDER ENTRY section\n2. Strategy type karo (koi bhi language)\n3. PARSE button → fields auto-fill!\n\n**Advanced conditions:**\n`if vix above 15 and pcr below 0.8 buy nifty atm call sl 100 tgt 250 trailing 30`\n\nYe sab auto-samajh jaata hai system! 🧠"
        ],
        "suggestions": ["More examples", "Conditions list", "Strategy builder"]
    },
    "stop_loss": {
        "keywords": ["stop loss","sl","stoploss","loss limit","trailing","trail","protect","cut loss","nuksan","ghata"],
        "responses": [
            "**Stop Loss — Aapka Capital Shield! 🛡️**\n\n**Types:**\n🔴 **Fixed SL:** Entry se X points pe stop\nExample: Entry ₹100, SL 80 pts → exit at ₹20\n\n🟡 **Trailing SL:** Profit ke saath SL move karta hai\nExample: 30 pts trailing → profit lock hota jaata hai\n\n**Rule of thumb:**\n✅ Risk per trade = Max 1-2% of capital\n✅ 1:2 minimum R:R ratio\n✅ Kabhi bhi SL remove mat karo!",
            "**Stop Loss kyon zaroori hai? 🤔**\n\nEk trade mein agar SL nahi laga toh:\n- ₹5000 ka loss → ₹50,000 ban sakta hai\n- Account wipe-out possible!\n\n**TRD mein kaise lagaen:**\nOrder Entry → STOP LOSS field → points enter karo\n\n**Trailing SL (advanced):**\nTrailing SL field mein value daalo\nProfit badhega toh SL automatically upar aayega! 📈\n\n💡 CALC tab mein R:R Calculator use karo!",
            "**Professional SL Rules! 💼**\n\n📊 **Position Sizer bhi use karo:**\nRISK tab → Position Sizer:\nCapital + Risk% + SL points = Optimal lots!\n\n**Common mistakes:**\n❌ SL bahut tight (market noise mein cut jaata hai)\n❌ SL bahut wide (zyada loss\n❌ SL nahi lagana\n\n✅ ATR (Average True Range) ke basis pe SL set karo\n✅ Key support/resistance pe rakho\n✅ NEVER average losing position!"
        ],
        "suggestions": ["Position sizing", "R:R calculator", "Risk management rules"]
    },
    "plans_pricing": {
        "keywords": ["plan","price","pricing","cost","kitna","fee","charge","subscription","free","pro","basic","institutional","paisa","rupee","upgrade","buy plan"],
        "responses": [
            "**TRD v12.3 — 4 Plans! 💎**\n\n| Plan | Price | Key Feature |\n|------|-------|-------------|\n| FREE | ₹0 | Paper trading |\n| BASIC | ₹499/mo | Scanner + Reports |\n| **PRO ⭐** | ₹1499/mo | AI Engine + Live |\n| INSTITUTION | ₹4999/mo | White label |\n\n**PRO = Most Popular:**\n✅ Unlimited strategies\n✅ AI signals + Auto-execute\n✅ 12-month backtest\n✅ All notifications\n\nUpgrade: PROFILE → 💳 PLANS",
            "**Plan comparison! 🔍**\n\n**FREE (₹0):**\nPaper trading, basic backtest, 3 strategies\n\n**BASIC (₹499/month):**\n+ Scanner, options chain, reports, 20 strategies\n\n**PRO (₹1499/month) — Recommended:**\n+ AI Engine, auto-execute, live API, unlimited strategies\n\n**INSTITUTIONAL (₹4999/month):**\n+ Everything + white label + 5yr backtest + priority support\n\n💡 PRO = ₹50/day. Ek profitable trade recover kar deta hai!",
            "**PRO plan kyun lein? 🤔**\n\n**ROI calculation:**\nCost: ₹1499/month\nAverage PRO user: ₹8,000-15,000 extra monthly profit\nROI: 5-10x monthly! 📈\n\n**PRO features that matter:**\n🤖 AI signals (78% accuracy backtest)\n⚡ Auto-execute (hands-free trading)\n📊 12-month backtest (strategy validation)\n🔔 Multi-channel alerts\n\nProfile → Plans → Select PRO → Upgrade!"
        ],
        "suggestions": ["Free vs PRO", "How to upgrade", "Refund policy"]
    },
    "ai_engine": {
        "keywords": ["ai","artificial intelligence","machine learning","neural network","genetic","lstm","rl","reinforcement","autonomous","robot","bot","ai engine"],
        "responses": [
            "**TRD AI Engine — 3 layers! 🤖**\n\n🧬 **Layer 1: Genetic Algorithm**\nStrategy DNA evolve karta hai (Darwin-style!)\n1000+ strategy combinations test karta hai\n\n🧠 **Layer 2: LSTM Neural Net**\nHidden market patterns discover karta hai\nPrice action patterns learn karta hai\n\n⚡ **Layer 3: RL (PPO/SAC)**\nReal-time self-optimization\nMarket regime ke hisab se adjust karta hai\n\n**Quality Gate:**\n15-day paper test + 62% WR + 1.5× PF = Approved! ✅",
            "**AI Engine kaise use karein? 📱**\n\nAI ENGINE tab kholo:\n\n1. 🧬 **EVOLVE** → New strategies generate (2-3 min)\n2. ⚡ **SIGNAL** → Current buy/sell signal\n3. 🔍 **REGIME** → Market condition analysis\n4. ★ **VIEW ALL** → All AI strategies\n5. ✅ **APPROVED** → Tested strategies only\n\n**Auto-Execute setup:**\nMinimum confidence set karo (75% recommended)\nMode: PAPER pehle, LIVE baad mein! ⚠️",
            "**AI Signal kya batata hai? 📊**\n\n**Signal types:**\n🟢 BUY_CE — Bullish setup\n🔴 SELL_PE — Bearish setup\n🔵 IRON_CONDOR — Rangebound\n⚫ WAIT — No clear setup\n\n**Components:**\n📊 Confidence % → 75%+ = Strong signal\n🌍 Market Regime → Trending/Rangebound/Volatile\n🔍 Hidden Pattern → What the algo found\n💡 Recommended strategy\n📍 Entry / SL / Target prices\n\nCircuit Breaker: VIX > 35 → Auto stop! 🔴"
        ],
        "suggestions": ["How to evolve?", "Auto-execute setup", "Signal accuracy?"]
    },
    "backtest": {
        "keywords": ["backtest","back test","historical","past data","test strategy","performance","kitna kama","returns","simulate","purana data"],
        "responses": [
            "**Backtest Engine — 100% Deterministic! 📊**\n\nBACKTEST tab:\n1. Strategy select (10 built-in, high WR)\n2. Capital enter (e.g., ₹1,00,000)\n3. Period: 1/3/6/12 months\n4. RUN BACKTEST!\n\n**Results:**\n📅 Date-wise P&L Calendar\n📈 Monthly breakdown\n💹 Sharpe Ratio, Profit Factor\n📉 Max Drawdown\n\n*Same inputs = Same outputs every time!* ✅",
            "**10 Built-in Strategies Backtest! 🏆**\n\n| Strategy | WR | Returns |\n|----------|----|---------|\n| Iron Condor | 78% | Best! |\n| Max Pain | 76% | Expiry day |\n| Theta Decay | 72% | Steady |\n| Gap Fade | 74% | Morning |\n| PCR Reversal | 71% | Contrarian |\n\nTip: 3-6 month backtest most reliable! 📈",
            "**Backtest results kaise padhein? 🤔**\n\n**Good strategy signs:**\n✅ Win Rate > 60%\n✅ Profit Factor > 1.5\n✅ Sharpe Ratio > 1.0\n✅ Max Drawdown < 15%\n✅ Profitable days > Loss days\n\n**Red flags:**\n❌ Win Rate 90%+ (overfitted!)\n❌ Only works in bull market\n❌ Very few trades (lucky, not skilled)\n\nDate calendar mein click karke daily detail dekho! 📅"
        ],
        "suggestions": ["Best strategy?", "Interpret results", "Custom strategy backtest"]
    },
    "offline_error": {
        "keywords": ["offline","not working","server down","connecting","nahi chal","band hai","error","404","502","loading","connect nahi","stuck"],
        "responses": [
            "**Connection issue fix! 🔧**\n\n**Step 1:** Hard refresh karo\n• Chrome: Ctrl+Shift+R\n• Mobile: Address bar pull down\n\n**Step 2:** Cache clear\nBrowser → Settings → Clear browsing data\n\n**Step 3:** New tab mein URL dobara type karo\n\n**Step 4:** Incognito mode try karo\n\n*Server AWS Stockholm pe hai — kabhi kabhi restart hota hai. 2-3 min wait karo!* 🙏",
            "**Server status check! 📡**\n\nHeader mein dekho:\n🟢 Green dot = ONLINE ✅\n🔴 Red dot = OFFLINE ❌\n🟡 Amber = CONNECTING...\n\n**Quick fixes:**\n1. Ctrl+Shift+R (hard refresh)\n2. Browser cache clear\n3. Incognito tab try karo\n4. Mobile: WiFi/4G switch karo\n\nAgar 5 min baad bhi nahi chala, support@trd.app pe email karo! 📧",
            "**Technical troubleshooting! 🛠️**\n\n**Browser compatibility:**\n✅ Chrome 90+\n✅ Firefox 88+\n✅ Safari 14+\n✅ Edge 90+\n\n**Mobile:**\n✅ Chrome Android\n✅ Safari iOS\n\n**Common fixes:**\n• VPN disable karo\n• Browser extension disable karo\n• JavaScript enable hai?\n\nConsole mein (F12) error copy karke bhejo — jaldi fix karenge! 🚀"
        ],
        "suggestions": ["Hard refresh karo", "Cache clear karna", "Browser compatibility"]
    },
    "chart": {
        "keywords": ["chart","graph","candlestick","candle","technical analysis","indicator","rsi","macd","ema","bollinger","vwap","timeframe","1min","5min","daily"],
        "responses": [
            "**Professional Chart Features! 📊**\n\nMarket Watch mein NIFTY/BANKNIFTY pe click karo!\n\n**Timeframes:** 1m, 5m, 15m, 30m, 1h, 4h, 1D, 1W\n\n**Indicators:**\n• EMA 20/50 — Trend direction\n• Bollinger Bands — Volatility\n• VWAP — Institutional levels\n• RSI — Overbought/Oversold\n• MACD — Momentum\n• Supertrend — Buy/Sell signals\n\n**Drawing tools coming soon!** 🎨",
            "**Chart use karne ka guide! 📱**\n\n1. TRADE tab → Market Watch\n2. Kisi bhi symbol pe click karo\n3. Chart full screen mein khulega!\n\n**Candlestick padhna:**\n🟢 Green candle = Close > Open (Bullish)\n🔴 Red candle = Close < Open (Bearish)\n\n**Quick analysis:**\nRSI < 30 = Oversold (buy opportunity)\nRSI > 70 = Overbought (sell opportunity)\nVWAP se upar = Bullish\nVWAP se neeche = Bearish",
            "**Chart tips! 💡**\n\n**Best timeframe combinations:**\n• Swing trading: Daily + 1H\n• Intraday: 15m + 5m\n• Scalping: 5m + 1m\n\n**Market hours (IST):**\n🕯️ Pre-open: 9:00-9:15\n📈 Market: 9:15-15:30\n🔴 After hours: Chart freezes at last close\n\n**Pro tip:**\nEMA 20 cross EMA 50 = Strong trend signal!\nBollinger Band squeeze = Big move coming! 🚀"
        ],
        "suggestions": ["Indicator guide", "Candlestick patterns", "Best timeframe?"]
    },
    "human_agent": {
        "keywords": ["human","real person","agent","support team","complaint","manager","escalate","live chat","call","angry","problem nahi hua"],
        "responses": [
            "**Human support se connect kar raha hoon! 🙏**\n\n✅ Escalation initiated!\n\nHamari team **2-4 business hours** mein respond karegi.\n\n**Contact:**\n📧 support@trd.app\n💬 Telegram: @TRD_Support\n⏰ Mon-Fri 9 AM - 6 PM IST\n\nTab tak main help karta rehta hoon — kya specific issue hai?",
            "**Support ticket raise ho gaya! 🎫**\n\nAapki problem note kar li gayi hai.\n\n**Priority support ke liye:**\n📧 Email: support@trd.app\nSubject mein: TRD Bug Report + aapka User ID\n\n**Response time:**\n🔴 Critical: 1 hour\n🟡 High: 4 hours\n🟢 Normal: 24 hours\n\nAapka User ID: Kya aap bata sakte hain?",
            "**Samajh gaye! Real agent se baat karni hai. 👍**\n\nMain abhi connect kar raha hoon...\n\n**Fastest way:**\nTelegram pe @TRD_Support message karo — instant response!\n\n**Ya email karo:**\nsupport@trd.app\n\n**Business hours:** Mon-Fri, 9 AM - 6 PM IST\n\nAapki problem zaroor solve hogi! 💪"
        ],
        "suggestions": ["Email support", "Telegram support", "Report bug"],
        "escalate": True
    },
    "risk_management": {
        "keywords": ["risk","risk management","position size","sizing","capital","max loss","drawdown","consecutive","safeguard","protect"],
        "responses": [
            "**Professional Risk Management! ⚠️**\n\n**The Golden Rules:**\n1. Per trade risk: **Max 1-2% of capital**\n2. Daily loss limit: **3% max** (auto kill switch)\n3. Max drawdown: **10%** (circuit breaker)\n4. Never average losing positions\n5. After 3 consecutive losses → take break!\n\n**RISK tab features:**\n📊 Live risk meters\n🧮 Position sizer calculator\n⚡ Kill switch\n🔄 Paper reset",
            "**Position Sizing Guide! 📐**\n\n**Formula:**\nOptimal Lots = (Capital × Risk%) ÷ (SL points × Lot size)\n\n**Example:**\nCapital: ₹5,00,000\nRisk: 1% = ₹5,000\nSL: 100 points\nLot size: 50\nOptimal lots = 5000 ÷ (100×50) = 1 lot\n\n**RISK tab → Position Sizer:** Auto calculate!\n\n💡 1% risk per trade = account survive karega long term!",
            "**Kill Switch kab use karein? 🔴**\n\n**Auto-trigger (system automatic):**\n• Daily loss 3% cross hone pe\n• Max drawdown 10% pe\n• VIX 35+ hone pe (circuit breaker)\n\n**Manual use karein jab:**\n• News event aane wala ho\n• System mein koi bug lage\n• Emotionally disturbed ho (FOMO/Revenge)\n\nHeader mein KILL button → sabhi trading band!\n\n**Resume:** RISK tab → RESUME button 🟢"
        ],
        "suggestions": ["Position sizer", "Kill switch guide", "Daily loss limit"]
    },
    "strategies": {
        "keywords": ["strategy","strategies","built in","iron condor","theta decay","orb","vwap","gap fade","pcr","which strategy","best strategy","kaunsi strategy"],
        "responses": [
            "**10 Best Strategies! 🏆**\n\n```\nStrategy          WR    Type\nIron Condor       78%   Options Sell\nMax Pain Expiry   76%   Expiry Day\nGap Fade          74%   Mean Revert\nTheta Decay       72%   Premium\nPCR Reversal      71%   Contrarian\nFII Momentum      69%   Institutional\nORB               68%   Breakout\n```\n\nSTRATEGIES tab → BUILT-IN → BT/PAPER/USE",
            "**Beginners ke liye best strategy? 🎯**\n\n**Recommendation:**\n1. **Weekly Iron Condor (78% WR)**\n   - Every Monday buy/sell setup\n   - Rangebound market mein best\n   - Risk defined, profit capped\n\n2. **Max Pain Expiry (76% WR)**\n   - Thursday expiry day\n   - Options sellers ka favorite\n\n**Start karo:**\nBacktest → Paper test (15 days) → Live!\n\n⚠️ Koi bhi strategy blindly use mat karo!",
            "**Strategy banana — 3 ways! ⭐**\n\n**Way 1: NLP Builder**\nType: 'buy nifty atm if rsi under 30 sl 100 tgt 300'\n→ Auto-parsed → Save!\n\n**Way 2: AI Evolve**\nAI ENGINE → EVOLVE → 1000s combinations test\n→ Best strategies auto-select!\n\n**Way 3: Copy Built-in**\nSTRATEGIES → Built-in → Modify → Save as yours\n\n**Quality check:** Every strategy goes through:\n15-day paper test + 62% WR + 1.5× PF check! ✅"
        ],
        "suggestions": ["Iron Condor guide", "Create custom strategy", "AI strategies"]
    },
}

class CustomerCareEngine:
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        self._build_index()

    def _build_index(self):
        self.kw_index: Dict[str, List[Tuple[str, float]]] = {}
        for key, item in KB.items():
            for kw in item.get("keywords", []):
                weight = 1.0 + len(kw.split()) * 0.3
                if kw not in self.kw_index:
                    self.kw_index[kw] = []
                self.kw_index[kw].append((key, weight))

    def _score(self, query: str) -> Dict[str, float]:
        q = query.lower().strip()
        scores: Dict[str, float] = {}
        # Exact keyword match
        for kw, entries in self.kw_index.items():
            if kw in q:
                for key, w in entries:
                    scores[key] = scores.get(key, 0) + w
        # Word-level partial match
        words = [w for w in re.findall(r'\b\w+\b', q) if len(w) >= 3]
        for word in words:
            for kw in self.kw_index:
                if word in kw or kw in word:
                    for key, w in self.kw_index[kw]:
                        scores[key] = scores.get(key, 0) + w * 0.4
        return scores

    def _get_session(self, uid: str) -> dict:
        if uid not in self.sessions:
            self.sessions[uid] = {
                "history": [], "last_topic": None,
                "response_indices": {},  # track which response variant used
                "msg_count": 0
            }
        return self.sessions[uid]

    def _pick_response(self, key: str, session: dict) -> str:
        """Pick varied response - never repeat same variant twice in a row"""
        responses = KB[key].get("responses", [""])
        if len(responses) == 1:
            return responses[0]
        used_idx = session["response_indices"].get(key, -1)
        available = [i for i in range(len(responses)) if i != used_idx]
        idx = random.choice(available)
        session["response_indices"][key] = idx
        return responses[idx]

    def chat(self, user_id: str, message: str, user_name: str = "Friend") -> dict:
        session = self._get_session(user_id)
        session["msg_count"] += 1
        msg = message.strip()
        msg_lower = msg.lower()

        # Greeting
        greet_words = {"hi","hello","hey","namaste","hii","helo","namaskar","good morning","good evening","good afternoon","sat sri akal"}
        if any(g in msg_lower for g in greet_words) and len(msg.split()) <= 3:
            resp = self._pick_response("greeting", session)
            return {"response": resp, "kb_hit": True, "confidence": 1.0, "suggestions": KB["greeting"]["suggestions"]}

        # Thanks
        thanks = {"thanks","thank","shukriya","dhanyawad","thx","ty","helpful","great","awesome","superb","zabardast","perfect"}
        if any(t in msg_lower for t in thanks):
            resp = self._pick_response("thanks", session)
            return {"response": resp, "kb_hit": True, "confidence": 1.0, "suggestions": []}

        # Human escalation
        escalate = {"human","real person","agent","complaint","manager","escalate","live chat"}
        if any(e in msg_lower for e in escalate):
            resp = self._pick_response("human_agent", session)
            return {"response": resp, "kb_hit": True, "confidence": 1.0,
                    "suggestions": KB["human_agent"]["suggestions"], "escalated": True}

        # Score all KB items
        scores = self._score(msg)

        if scores:
            best = max(scores, key=scores.get)
            score = scores[best]
            if score >= 0.8:
                session["last_topic"] = best
                session["history"].append({"role": "user", "msg": msg[:80]})
                resp = self._pick_response(best, session)
                return {
                    "response": resp, "kb_hit": True,
                    "confidence": min(score / 5.0, 0.98),
                    "suggestions": KB[best].get("suggestions", []),
                    "escalated": KB[best].get("escalate", False)
                }

        # Context-aware fallback
        last = session.get("last_topic")
        if last and last in KB:
            resp = self._pick_response(last, session)
            return {
                "response": f"Kya aap is baare mein aur poochhna chahte hain? 🤔\n\n" + resp,
                "kb_hit": False, "confidence": 0.4,
                "suggestions": KB[last].get("suggestions", ["Main topic pe wapas jaao", "Kuch aur poochhein"])
            }

        # Generic fallback with personality
        fallbacks = [
            f"Hmm, main bilkul samajh raha hoon aap kya poochh rahe hain! 🤔\n\nLekin mujhe thoda aur context chahiye.\n\nKya aap yeh topics mein se choose kar sakte hain?\n\n• Trading guide\n• Plans & pricing\n• AI Engine\n• Technical issues\n• Risk management\n\nYa type karein: **'talk to human'** for live support!",
            f"Interesting sawaal! 💭 Mujhe isko samajhne mein thodi help chahiye.\n\nKya aap yeh clarify kar sakte hain:\n\n1. Kya yeh trading se related hai?\n2. Kya technical problem hai?\n3. Kya billing/plan related hai?\n\nMerko batao — main zaroor help karoonga! 🙏",
            f"Aapka sawaal note kar liya! 📝\n\nSabse fast help ke liye try karein:\n\n🔍 **Search terms:**\n• 'how to trade'\n• 'plans pricing'\n• 'ai signal'\n• 'chart guide'\n• 'risk management'\n\nYa **'talk to human'** for direct support! 👨‍💼"
        ]
        idx = session["msg_count"] % len(fallbacks)
        return {
            "response": fallbacks[idx],
            "kb_hit": False, "confidence": 0.2,
            "suggestions": ["How to trade?", "Plans pricing", "AI signals", "Talk to human"]
        }

# Singleton
care_engine = CustomerCareEngine()
