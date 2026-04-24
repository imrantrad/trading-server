from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re, time, math

app = FastAPI(title="Trading System v12.3 - Complete NLP")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ═══════════════════════════════════════════════════════════
# INSTRUMENTS
# ═══════════════════════════════════════════════════════════
INSTRUMENTS = {
    "nifty 50":"NIFTY","nifty50":"NIFTY","nifty":"NIFTY","nifti":"NIFTY",
    "निफ्टी":"NIFTY","nf":"NIFTY",
    "bank nifty":"BANKNIFTY","banknifty":"BANKNIFTY","bnf":"BANKNIFTY",
    "बैंक निफ्टी":"BANKNIFTY","बैंकनिफ्टी":"BANKNIFTY","bank":"BANKNIFTY",
    "fin nifty":"FINNIFTY","finnifty":"FINNIFTY","fn":"FINNIFTY","फिन निफ्टी":"FINNIFTY",
    "midcap nifty":"MIDCPNIFTY","midcap":"MIDCPNIFTY","mid":"MIDCPNIFTY",
    "sensex":"SENSEX","बीएसई":"SENSEX","सेंसेक्स":"SENSEX",
    "reliance":"RELIANCE","tcs":"TCS","hdfc":"HDFCBANK",
    "infosys":"INFY","infy":"INFY","icici":"ICICIBANK",
    "sbi":"SBIN","tatasteel":"TATASTEEL","bajaj":"BAJFINANCE",
}

# ═══════════════════════════════════════════════════════════
# BUY / SELL
# ═══════════════════════════════════════════════════════════
BUY_WORDS = [
    "buy","long","bullish","upside","call buy","ce buy","entry","enter",
    "open long","go long","purchase","accumulate","add position",
    "kharido","kharid","le lo","lelo","lo","khareedna",
    "bullish hai","upar jayega","upar jaega","badhega",
    "खरीदो","खरीद","खरीदना","लेना","ले लो","लो","बढ़ेगा",
]
SELL_WORDS = [
    "sell","short","bearish","downside","put buy","pe buy","exit","close",
    "square off","squareoff","book profit","book loss","reduce",
    "becho","bech","niklo","nikal","bechna","nikal lo",
    "bearish hai","niche jayega","neeche jaega","girega",
    "बेचो","बेच","बेचना","निकलो","निकालो","गिरेगा","बाहर",
]

# ═══════════════════════════════════════════════════════════
# OPTION TYPES
# ═══════════════════════════════════════════════════════════
OPTION_TYPES = {
    "call":"CE","ce":"CE","c":"CE","कॉल":"CE",
    "put":"PE","pe":"PE","p":"PE","पुट":"PE",
}

# ═══════════════════════════════════════════════════════════
# STRATEGIES
# ═══════════════════════════════════════════════════════════
STRATEGIES = {
    # Basic
    "straddle":"STRADDLE","atm straddle":"ATM_STRADDLE",
    "strangle":"STRANGLE","otm strangle":"OTM_STRANGLE",
    "covered call":"COVERED_CALL","protective put":"PROTECTIVE_PUT",
    "naked call":"NAKED_CALL","naked put":"NAKED_PUT",
    # Spreads
    "bull call spread":"BULL_CALL_SPREAD",
    "bear call spread":"BEAR_CALL_SPREAD",
    "bull put spread":"BULL_PUT_SPREAD",
    "bear put spread":"BEAR_PUT_SPREAD",
    "calendar spread":"CALENDAR_SPREAD",
    "diagonal spread":"DIAGONAL_SPREAD",
    "ratio spread":"RATIO_SPREAD",
    "back spread":"BACK_SPREAD",
    "debit spread":"DEBIT_SPREAD",
    "credit spread":"CREDIT_SPREAD",
    # Complex
    "iron condor":"IRON_CONDOR",
    "iron butterfly":"IRON_BUTTERFLY",
    "broken wing butterfly":"BWB","bwb":"BWB",
    "butterfly":"BUTTERFLY","condor":"CONDOR",
    "jade lizard":"JADE_LIZARD",
    "double diagonal":"DOUBLE_DIAGONAL",
    "christmas tree":"CHRISTMAS_TREE",
    "collar":"COLLAR","risk reversal":"RISK_REVERSAL",
    # Hinglish
    "straddle lagao":"STRADDLE","strangle banao":"STRANGLE",
    "iron condor lagao":"IRON_CONDOR","butterfly banao":"BUTTERFLY",
}

# ═══════════════════════════════════════════════════════════
# ENTRY CONDITIONS
# ═══════════════════════════════════════════════════════════
ENTRY_CONDITIONS = {
    # Momentum Indicators
    "rsi":"RSI","rsi oversold":"RSI_OVERSOLD","rsi overbought":"RSI_OVERBOUGHT",
    "rsi crossover":"RSI_CROSS","rsi divergence":"RSI_DIV",
    "macd":"MACD","macd crossover":"MACD_CROSS","macd bullish":"MACD_BULL",
    "macd bearish":"MACD_BEAR","macd histogram":"MACD_HIST",
    "stochastic":"STOCH","stoch crossover":"STOCH_CROSS",
    "cci":"CCI","williams r":"WILLIAMS_R","roc":"ROC",
    "mfi":"MFI","money flow":"MFI",
    # Trend Indicators
    "ema":"EMA","ema crossover":"EMA_CROSS","ema200":"EMA200",
    "sma":"SMA","sma crossover":"SMA_CROSS","wma":"WMA",
    "golden cross":"GOLDEN_CROSS","death cross":"DEATH_CROSS",
    "supertrend":"SUPERTREND","super trend buy":"ST_BUY","super trend sell":"ST_SELL",
    "adx":"ADX","adx trending":"ADX_TREND","adx strong":"ADX_STRONG",
    "parabolic sar":"PSAR","psar":"PSAR","ichimoku":"ICHIMOKU",
    "ichimoku cloud":"ICHI_CLOUD","kumo breakout":"KUMO_BO",
    # Volatility
    "bollinger band":"BB","bollinger":"BB","bb squeeze":"BB_SQUEEZE",
    "bb breakout":"BB_BO","bb upper":"BB_UPPER","bb lower":"BB_LOWER",
    "atr":"ATR","keltner channel":"KELTNER",
    "vix":"VIX","india vix":"VIX","vix spike":"VIX_SPIKE",
    "iv":"IV","implied volatility":"IV","iv crush":"IV_CRUSH",
    "iv expansion":"IV_EXP","hv":"HV",
    # Volume
    "vwap":"VWAP","vwap breakout":"VWAP_BO","vwap bounce":"VWAP_BNC",
    "obv":"OBV","volume surge":"VOL_SURGE","high volume":"HIGH_VOL",
    "low volume":"LOW_VOL","volume breakout":"VOL_BO",
    # Price Action
    "support":"SUPPORT","resistance":"RESISTANCE",
    "breakout":"BREAKOUT","breakdown":"BREAKDOWN",
    "reversal":"REVERSAL","bounce":"BOUNCE",
    "higher high":"HH","lower low":"LL","higher low":"HL",
    "double top":"DOUBLE_TOP","double bottom":"DOUBLE_BOTTOM",
    "head and shoulder":"HEAD_SHOULDER","inverse head shoulder":"INV_HS",
    "cup and handle":"CUP_HANDLE","rounding bottom":"ROUND_BOTTOM",
    "flag":"FLAG","pennant":"PENNANT","wedge":"WEDGE",
    "ascending triangle":"ASC_TRI","descending triangle":"DESC_TRI",
    "symmetrical triangle":"SYM_TRI",
    "gap up":"GAP_UP","gap down":"GAP_DOWN","gap fill":"GAP_FILL",
    "engulfing":"ENGULF","doji":"DOJI","hammer":"HAMMER",
    "shooting star":"SHOOT_STAR","morning star":"MORNING_STAR",
    "evening star":"EVENING_STAR","harami":"HARAMI",
    "three white soldiers":"THREE_WS","three black crows":"THREE_BC",
    # Greeks
    "delta":"DELTA","gamma":"GAMMA","theta":"THETA",
    "vega":"VEGA","rho":"RHO","delta neutral":"DELTA_NEUTRAL",
    # Options Specific
    "open interest":"OI","oi buildup":"OI_BUILD","oi unwinding":"OI_UNWIND",
    "pcr":"PCR","put call ratio":"PCR","max pain":"MAX_PAIN",
    "gamma scalping":"GAMMA_SCALP","theta decay":"THETA_DECAY",
    "iv rank":"IV_RANK","iv percentile":"IV_PERC",
    # Market Conditions
    "trending":"TRENDING","sideways":"SIDEWAYS","rangebound":"RANGEBOUND",
    "range bound":"RANGEBOUND","consolidating":"CONSOLIDATING",
    "volatile":"VOLATILE","low volatility":"LOW_VOL_MKT",
    "bull market":"BULL_MKT","bear market":"BEAR_MKT",
    "overbought":"OVERBOUGHT","oversold":"OVERSOLD",
    # Fundamental
    "earnings":"EARNINGS","results":"RESULTS","event":"EVENT",
    "expiry":"EXPIRY","expiry day":"EXPIRY_DAY",
    "budget":"BUDGET","rbi policy":"RBI","fed":"FED",
}

# ═══════════════════════════════════════════════════════════
# EXIT CONDITIONS
# ═══════════════════════════════════════════════════════════
EXIT_CONDITIONS = {
    # Fixed
    "stop loss":"STOPLOSS","sl":"STOPLOSS","stoploss":"STOPLOSS",
    "target":"TARGET","tp":"TARGET","take profit":"TARGET",
    "trailing stop":"TRAIL_SL","trailing sl":"TRAIL_SL",
    "trailing stop loss":"TRAIL_SL",
    "break even":"BREAKEVEN","be":"BREAKEVEN",
    # P&L Based
    "max loss":"MAX_LOSS","max profit":"MAX_PROFIT",
    "daily loss limit":"DAILY_LOSS","profit target":"PROFIT_TGT",
    "book partial":"PARTIAL_EXIT","partial exit":"PARTIAL_EXIT",
    "50% exit":"HALF_EXIT","half exit":"HALF_EXIT",
    # Time Based
    "eod exit":"EOD_EXIT","end of day exit":"EOD_EXIT",
    "15 min before expiry":"PRE_EXPIRY","before expiry":"PRE_EXPIRY",
    "time stop":"TIME_STOP",
    # Technical Based
    "reverse signal":"REV_SIGNAL","signal reversal":"REV_SIGNAL",
    "target achieved":"TGT_HIT","sl hit":"SL_HIT",
    "resistance hit":"RES_HIT","support broken":"SUP_BRK",
    # Options Specific
    "theta exit":"THETA_EXIT","delta exit":"DELTA_EXIT",
    "iv exit":"IV_EXIT","premium target":"PREM_TGT",
    "50% premium":"HALF_PREM","premium stop":"PREM_SL",
    # Hinglish
    "nikal lo":"EXIT_NOW","bahar niklo":"EXIT_NOW",
    "profit book karo":"BOOK_PROFIT","loss cut karo":"CUT_LOSS",
    "nikalna hai":"EXIT_SIGNAL",
    # Hindi
    "बाहर":"EXIT_NOW","निकलो":"EXIT_NOW","मुनाफा":"BOOK_PROFIT",
}

# ═══════════════════════════════════════════════════════════
# STRIKE SELECTION
# ═══════════════════════════════════════════════════════════
STRIKE_SELECTION = {
    # Moneyness
    "atm":"ATM","at the money":"ATM",
    "itm":"ITM","in the money":"ITM",
    "otm":"OTM","out of the money":"OTM",
    "deep itm":"DEEP_ITM","deep otm":"DEEP_OTM",
    "slight otm":"SLIGHT_OTM","slight itm":"SLIGHT_ITM",
    # Relative Strikes
    "1 strike otm":"OTM_1","2 strike otm":"OTM_2","3 strike otm":"OTM_3",
    "1 strike itm":"ITM_1","2 strike itm":"ITM_2",
    "next strike":"NEXT_STRIKE","previous strike":"PREV_STRIKE",
    # Delta Based
    "delta 50":"DELTA_50","50 delta":"DELTA_50",
    "delta 25":"DELTA_25","25 delta":"DELTA_25",
    "delta 16":"DELTA_16","16 delta":"DELTA_16",
    "delta 10":"DELTA_10","10 delta":"DELTA_10",
    # Premium Based
    "100 premium":"PREM_100","200 premium":"PREM_200",
    "500 premium":"PREM_500","cheap option":"CHEAP_OPT",
    # Strategy Specific
    "same strike":"SAME_STRIKE","equidistant":"EQUIDIST",
    "symmetric":"SYMMETRIC","asymmetric":"ASYMMETRIC",
}

# ═══════════════════════════════════════════════════════════
# TIME
# ═══════════════════════════════════════════════════════════
TIME_MAP = {
    "pre market":"09:00","premarket":"09:00",
    "market open":"09:15","opening":"09:15","open":"09:15",
    "morning":"09:20","early morning":"09:20","subah":"09:20",
    "subah subah":"09:15","सुबह":"09:20",
    "9:15":"09:15","9:20":"09:20","9:30":"09:30",
    "mid day":"12:00","midday":"12:00","noon":"12:00",
    "dopahar":"12:00","दोपहर":"12:00",
    "afternoon":"14:00","post noon":"14:00",
    "closing":"15:15","market close":"15:15","close":"15:15",
    "shaam":"15:00","शाम":"15:00","बाजार बंद":"15:15",
    "eod":"15:20","end of day":"15:20",
    "expiry time":"15:25","last 30 min":"15:00",
}

# ═══════════════════════════════════════════════════════════
# EXPIRY
# ═══════════════════════════════════════════════════════════
EXPIRY_MAP = {
    "weekly":"WEEKLY","week":"WEEKLY","this week":"WEEKLY",
    "next week":"NEXT_WEEKLY","weekly expiry":"WEEKLY",
    "monthly":"MONTHLY","month":"MONTHLY","this month":"MONTHLY",
    "next month":"NEXT_MONTHLY","monthly expiry":"MONTHLY",
    "current expiry":"CURRENT","near month":"NEAR_MONTH",
    "far month":"FAR_MONTH","quarterly":"QUARTERLY",
    "is hafte":"WEEKLY","agle hafte":"NEXT_WEEKLY",
    "mahina":"MONTHLY","is mahine":"MONTHLY",
}

# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════
def extract_instrument(text):
    for k,v in sorted(INSTRUMENTS.items(),key=lambda x:-len(x[0])):
        if k in text: return v
    return "NIFTY"

def extract_action(text):
    s=sum(1 for w in SELL_WORDS if w in text)
    b=sum(1 for w in BUY_WORDS if w in text)
    return "SELL" if s>b else "BUY"

def extract_strike(text):
    nums=re.findall(r'\b(\d{4,6})\b',text)
    if not nums: return None
    return [int(x) for x in nums] if len(nums)>1 else int(nums[0])

def extract_option_type(text):
    for k,v in OPTION_TYPES.items():
        if re.search(r'\b'+re.escape(k)+r'\b',text): return v
    return None

def extract_strategy(text):
    for k,v in sorted(STRATEGIES.items(),key=lambda x:-len(x[0])):
        if k in text: return v
    return None

def extract_entry_conditions(text):
    found={}
    for k,v in sorted(ENTRY_CONDITIONS.items(),key=lambda x:-len(x[0])):
        if k in text:
            p=rf'{re.escape(k)}\s*([<>=!]+)?\s*(\d+\.?\d*)?'
            m=re.search(p,text)
            if m and m.group(2):
                found[v]={"operator":m.group(1) or "=","value":float(m.group(2))}
            else:
                found[v]=True
    return found if found else None

def extract_exit_conditions(text):
    found={}
    for k,v in sorted(EXIT_CONDITIONS.items(),key=lambda x:-len(x[0])):
        if k in text:
            p=rf'{re.escape(k)}\s*([<>=]?)\s*(\d+\.?\d*)?'
            m=re.search(p,text)
            if m and m.group(2):
                found[v]=float(m.group(2))
            else:
                found[v]=True
    return found if found else None

def extract_strike_selection(text):
    for k,v in sorted(STRIKE_SELECTION.items(),key=lambda x:-len(x[0])):
        if k in text: return v
    return None

def extract_time(text):
    for k,v in sorted(TIME_MAP.items(),key=lambda x:-len(x[0])):
        if k in text: return v
    m=re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b',text)
    if m:
        h,mn=int(m.group(1)),int(m.group(2))
        if m.group(3)=='pm' and h!=12: h+=12
        return f"{h:02d}:{mn:02d}"
    return None

def extract_quantity(text):
    m=re.search(r'(\d+)\s*(?:lot|lots|लॉट)',text)
    return int(m.group(1)) if m else 1

def extract_expiry(text):
    for k,v in sorted(EXPIRY_MAP.items(),key=lambda x:-len(x[0])):
        if k in text: return v
    return "WEEKLY"

def extract_sl_target(text):
    result={}
    sl=re.search(r'(?:sl|stop loss|stoploss)\s*[=:@]?\s*(\d+)',text)
    tgt=re.search(r'(?:target|tp|take profit)\s*[=:@]?\s*(\d+)',text)
    trail=re.search(r'trailing\s*(?:sl|stop)?\s*[=:@]?\s*(\d+)',text)
    rr=re.search(r'(?:rr|risk reward)\s*[=:@]?\s*(\d+)[:/](\d+)',text)
    if sl: result["stoploss"]=int(sl.group(1))
    if tgt: result["target"]=int(tgt.group(1))
    if trail: result["trailing_sl"]=int(trail.group(1))
    if rr: result["risk_reward"]=f"{rr.group(1)}:{rr.group(2)}"
    return result if result else None

def detect_language(text):
    hindi=len(re.findall(r'[\u0900-\u097F]',text))
    if hindi>3: return "HINDI"
    hw=["kharido","becho","lo","niklo","subah","shaam","lagao","banao","hai","karo"]
    if any(w in text for w in hw): return "HINGLISH"
    return "ENGLISH"

def calculate_confidence(result):
    score=0.65
    if result.get("instrument"): score+=0.05
    if result.get("option_type"): score+=0.05
    if result.get("strategy"): score+=0.05
    if result.get("strike"): score+=0.05
    if result.get("strike_selection"): score+=0.03
    if result.get("entry_conditions"): score+=0.05
    if result.get("exit_conditions"): score+=0.04
    if result.get("sl_target"): score+=0.03
    if result.get("execution_time"): score+=0.02
    if result.get("expiry"): score+=0.02
    return min(round(score,2),0.99)

# ═══════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════
@app.get("/")
def root():
    return {
        "status":"running","version":"12.3","nlp":"complete_v3",
        "capabilities":["entry","exit","strike_selection","options",
                        "strategies","hindi","hinglish","greeks",
                        "risk_management","time_based","condition_based"]
    }

@app.post("/strategy")
def parse_strategy(payload: dict):
    raw=payload.get("text","")
    text=raw.lower().strip()

    instrument=extract_instrument(text)
    action=extract_action(text)
    strike=extract_strike(text)
    option_type=extract_option_type(text)
    strategy=extract_strategy(text)
    entry_conditions=extract_entry_conditions(text)
    exit_conditions=extract_exit_conditions(text)
    strike_selection=extract_strike_selection(text)
    exec_time=extract_time(text)
    quantity=extract_quantity(text)
    expiry=extract_expiry(text)
    sl_target=extract_sl_target(text)
    language=detect_language(text)

    result={
        "instrument":instrument,
        "action":action,
        "language":language,
        "expiry":expiry,
        "quantity":quantity,
    }

    if option_type: result["option_type"]=option_type
    if strike: result["strike"]=strike
    if strike_selection: result["strike_selection"]=strike_selection
    if strategy: result["strategy"]=strategy
    if entry_conditions: result["entry_conditions"]=entry_conditions
    if exit_conditions: result["exit_conditions"]=exit_conditions
    if sl_target: result["sl_target"]=sl_target
    if exec_time: result["execution_time"]=exec_time

    result["confidence"]=calculate_confidence(result)
    result["raw_input"]=raw
    result["parsed_at"]=time.strftime("%H:%M:%S")

    return result

@app.post("/trade")
def execute_trade(strategy: dict):
    conf=strategy.get("confidence",0)
    if conf<0.50:
        return {"status":"REJECTED","reason":"Confidence too low","confidence":conf}
    if conf<0.70:
        return {"status":"REVIEW","reason":"Manual review needed","confidence":conf}
    return {
        "status":"EXECUTED","result":strategy,
        "order_id":f"ORD{int(time.time()*1000)%1000000:06d}",
        "executed_at":time.strftime("%H:%M:%S")
    }

@app.get("/nlp/capabilities")
def get_capabilities():
    return {
        "instruments":list(set(INSTRUMENTS.values())),
        "strategies":list(set(STRATEGIES.values())),
        "entry_conditions":list(set(ENTRY_CONDITIONS.values())),
        "exit_conditions":list(set(EXIT_CONDITIONS.values())),
        "strike_selection":list(set(STRIKE_SELECTION.values())),
        "languages":["ENGLISH","HINDI","HINGLISH"],
        "example_inputs":[
            "buy nifty 22500 call weekly if RSI < 30 stop loss 100 target 300",
            "sell banknifty atm straddle if vix > 15 at market open",
            "nifty iron condor otm 2 strike if sideways trailing sl 50",
            "kharido nifty 50 delta call if ema crossover subah",
            "बेचो बैंकनिफ्टी पुट if rsi overbought stop loss 200",
            "bull call spread nifty if breakout with target 500",
            "buy banknifty 1 strike otm call if macd bullish eod exit",
        ]
    }
