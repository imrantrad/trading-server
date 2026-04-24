from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re, time, json

app = FastAPI(title="Trading System v12.3 - Advanced NLP")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ═══════════════════════════════════════════════
# 1. INSTRUMENTS
# ═══════════════════════════════════════════════
INSTRUMENTS = {
    # English
    "nifty 50": "NIFTY", "nifty50": "NIFTY", "nifty": "NIFTY",
    "bank nifty": "BANKNIFTY", "banknifty": "BANKNIFTY", "bnf": "BANKNIFTY",
    "fin nifty": "FINNIFTY", "finnifty": "FINNIFTY", "fn": "FINNIFTY",
    "midcap nifty": "MIDCPNIFTY", "midcap": "MIDCPNIFTY", "mid cap": "MIDCPNIFTY",
    "sensex": "SENSEX", "bse": "SENSEX",
    "reliance": "RELIANCE", "tcs": "TCS", "hdfc": "HDFCBANK",
    "infosys": "INFY", "infy": "INFY", "icici": "ICICIBANK",
    # Hindi
    "निफ्टी": "NIFTY", "बैंक निफ्टी": "BANKNIFTY", "बैंकनिफ्टी": "BANKNIFTY",
    "सेंसेक्स": "SENSEX", "फिन निफ्टी": "FINNIFTY",
    # Hinglish
    "nifti": "NIFTY", "bank nifti": "BANKNIFTY", "banknifti": "BANKNIFTY",
}

# ═══════════════════════════════════════════════
# 2. BUY / SELL WORDS
# ═══════════════════════════════════════════════
BUY_WORDS = [
    # English
    "buy", "long", "bullish", "upside", "call buy", "ce buy",
    "entry", "enter", "open long", "go long", "purchase",
    "accumulate", "add", "increase position",
    # Hindi
    "खरीदो", "खरीद", "खरीदना", "लेना", "ले लो",
    # Hinglish
    "kharido", "kharid", "le lo", "lelo", "lo", "khareedna",
    "bullish hai", "upar jayega", "upar jaega",
]
SELL_WORDS = [
    # English
    "sell", "short", "bearish", "downside", "put buy", "pe buy",
    "exit", "close", "square off", "squareoff", "book profit",
    "book loss", "reduce", "decrease position",
    # Hindi
    "बेचो", "बेच", "बेचना", "निकलो", "निकालो",
    # Hinglish
    "becho", "bech", "niklo", "nikal", "bechna",
    "bearish hai", "niche jayega", "neeche jaega",
    "square off karo", "exit karo", "nikal lo",
]

# ═══════════════════════════════════════════════
# 3. OPTION TYPES
# ═══════════════════════════════════════════════
OPTION_TYPES = {
    "call": "CE", "ce": "CE", "c": "CE", "कॉल": "CE",
    "put": "PE", "pe": "PE", "p": "PE", "पुट": "PE",
}

# ═══════════════════════════════════════════════
# 4. STRATEGIES (Full Derivatives)
# ═══════════════════════════════════════════════
STRATEGIES = {
    # Basic
    "straddle": "STRADDLE",
    "strangle": "STRANGLE",
    "covered call": "COVERED_CALL",
    "protective put": "PROTECTIVE_PUT",
    "naked call": "NAKED_CALL",
    "naked put": "NAKED_PUT",
    # Spreads
    "bull call spread": "BULL_CALL_SPREAD",
    "bear call spread": "BEAR_CALL_SPREAD",
    "bull put spread": "BULL_PUT_SPREAD",
    "bear put spread": "BEAR_PUT_SPREAD",
    "calendar spread": "CALENDAR_SPREAD",
    "diagonal spread": "DIAGONAL_SPREAD",
    "ratio spread": "RATIO_SPREAD",
    "back spread": "BACK_SPREAD",
    # Complex
    "iron condor": "IRON_CONDOR",
    "iron butterfly": "IRON_BUTTERFLY",
    "butterfly": "BUTTERFLY",
    "condor": "CONDOR",
    "jade lizard": "JADE_LIZARD",
    "broken wing butterfly": "BWB",
    "double diagonal": "DOUBLE_DIAGONAL",
    # Moneyness
    "atm straddle": "ATM_STRADDLE",
    "otm strangle": "OTM_STRANGLE",
    "atm": "ATM", "itm": "ITM", "otm": "OTM",
    "deep itm": "DEEP_ITM", "deep otm": "DEEP_OTM",
    # Hinglish
    "straddle lagao": "STRADDLE",
    "strangle banao": "STRANGLE",
    "iron condor lagao": "IRON_CONDOR",
    "butterfly banao": "BUTTERFLY",
}

# ═══════════════════════════════════════════════
# 5. TECHNICAL INDICATORS & CONDITIONS
# ═══════════════════════════════════════════════
INDICATORS = {
    # Momentum
    "rsi": "RSI", "relative strength": "RSI",
    "macd": "MACD", "macd crossover": "MACD_CROSS",
    "stochastic": "STOCH", "stoch": "STOCH",
    "cci": "CCI", "roc": "ROC", "williams": "WILLIAMS_R",
    "mfi": "MFI", "money flow": "MFI",
    # Trend
    "ema": "EMA", "sma": "SMA", "wma": "WMA",
    "ema crossover": "EMA_CROSS", "golden cross": "GOLDEN_CROSS",
    "death cross": "DEATH_CROSS",
    "supertrend": "SUPERTREND", "super trend": "SUPERTREND",
    "adx": "ADX", "parabolic sar": "PSAR", "psar": "PSAR",
    "ichimoku": "ICHIMOKU",
    # Volatility
    "bollinger": "BB", "bb": "BB", "bollinger band": "BB",
    "atr": "ATR", "average true range": "ATR",
    "vix": "VIX", "india vix": "VIX",
    "volatility": "VOLATILITY", "iv": "IV", "implied volatility": "IV",
    "hv": "HV", "historical volatility": "HV",
    # Volume
    "vwap": "VWAP", "volume weighted": "VWAP",
    "obv": "OBV", "on balance volume": "OBV",
    "volume": "VOLUME",
    # Price Action
    "support": "SUPPORT", "resistance": "RESISTANCE",
    "breakout": "BREAKOUT", "breakdown": "BREAKDOWN",
    "reversal": "REVERSAL",
    "higher high": "HH", "lower low": "LL",
    "double top": "DOUBLE_TOP", "double bottom": "DOUBLE_BOTTOM",
    "head and shoulder": "HEAD_SHOULDER",
    "cup and handle": "CUP_HANDLE",
    "flag": "FLAG", "pennant": "PENNANT",
    "wedge": "WEDGE", "triangle": "TRIANGLE",
    # Greeks
    "delta": "DELTA", "gamma": "GAMMA",
    "theta": "THETA", "vega": "VEGA", "rho": "RHO",
    # Risk
    "stop loss": "STOPLOSS", "sl": "STOPLOSS",
    "stoploss": "STOPLOSS", "stop": "STOPLOSS",
    "target": "TARGET", "tp": "TARGET",
    "trailing stop": "TRAILING_STOP",
    "risk reward": "RISK_REWARD", "rr": "RISK_REWARD",
    "max loss": "MAX_LOSS", "max profit": "MAX_PROFIT",
}

# ═══════════════════════════════════════════════
# 6. TIME EXPRESSIONS
# ═══════════════════════════════════════════════
TIME_MAP = {
    # English
    "market open": "09:15", "opening": "09:15", "open": "09:15",
    "morning": "09:20", "early morning": "09:20",
    "pre market": "09:00", "premarket": "09:00",
    "mid day": "12:00", "midday": "12:00", "noon": "12:00",
    "afternoon": "14:00", "post noon": "14:00",
    "closing": "15:15", "market close": "15:15",
    "eod": "15:20", "end of day": "15:20",
    "expiry": "15:30", "expiry day": "15:30",
    # Hinglish
    "subah": "09:20", "subah subah": "09:15",
    "dopahar": "12:00", "dopehar": "12:00",
    "shaam": "15:00", "closing time": "15:15",
    # Hindi
    "सुबह": "09:20", "दोपहर": "12:00", "शाम": "15:00",
    "बाजार खुलने पर": "09:15", "बाजार बंद होने पर": "15:15",
}

# ═══════════════════════════════════════════════
# 7. EXPIRY
# ═══════════════════════════════════════════════
EXPIRY_MAP = {
    "weekly": "WEEKLY", "week": "WEEKLY", "this week": "WEEKLY",
    "next week": "NEXT_WEEKLY", "weekly expiry": "WEEKLY",
    "monthly": "MONTHLY", "month": "MONTHLY", "this month": "MONTHLY",
    "next month": "NEXT_MONTHLY", "monthly expiry": "MONTHLY",
    "current": "CURRENT", "near": "NEAR_MONTH",
    "far": "FAR_MONTH", "quarterly": "QUARTERLY",
    # Hindi/Hinglish
    "weekly expiry hai": "WEEKLY", "mahina": "MONTHLY",
    "is hafte": "WEEKLY", "agle hafte": "NEXT_WEEKLY",
}

# ═══════════════════════════════════════════════
# 8. MARKET CONDITIONS
# ═══════════════════════════════════════════════
MARKET_CONDITIONS = {
    "trending": "TRENDING", "sideways": "SIDEWAYS",
    "range bound": "RANGEBOUND", "volatile": "VOLATILE",
    "low volatility": "LOW_VOL", "high volatility": "HIGH_VOL",
    "bull market": "BULLISH", "bear market": "BEARISH",
    "gap up": "GAP_UP", "gap down": "GAP_DOWN",
    "overbought": "OVERBOUGHT", "oversold": "OVERSOLD",
}

# ═══════════════════════════════════════════════
# EXTRACTOR FUNCTIONS
# ═══════════════════════════════════════════════
def extract_instrument(text):
    for key, val in sorted(INSTRUMENTS.items(), key=lambda x: -len(x[0])):
        if key in text:
            return val
    return "NIFTY"

def extract_action(text):
    sell_score = sum(1 for w in SELL_WORDS if w in text)
    buy_score = sum(1 for w in BUY_WORDS if w in text)
    if sell_score > buy_score:
        return "SELL"
    return "BUY"

def extract_strike(text):
    matches = re.findall(r'\b(\d{4,6})\b', text)
    if matches:
        return [int(m) for m in matches] if len(matches) > 1 else int(matches[0])
    return None

def extract_option_type(text):
    for key, val in OPTION_TYPES.items():
        if re.search(r'\b' + re.escape(key) + r'\b', text):
            return val
    return None

def extract_strategy(text):
    for key, val in sorted(STRATEGIES.items(), key=lambda x: -len(x[0])):
        if key in text:
            return val
    return None

def extract_indicators(text):
    found = {}
    for key, val in sorted(INDICATORS.items(), key=lambda x: -len(x[0])):
        if key in text:
            # Try to find operator and value
            pattern = rf'{re.escape(key)}\s*([<>=!]+)?\s*(\d+\.?\d*)?'
            m = re.search(pattern, text)
            if m and m.group(2):
                op = m.group(1) or "="
                found[val] = {"operator": op, "value": float(m.group(2))}
            else:
                found[val] = True
    return found if found else None

def extract_time(text):
    for key, val in sorted(TIME_MAP.items(), key=lambda x: -len(x[0])):
        if key in text:
            return val
    m = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b', text)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        if m.group(3) == 'pm' and h != 12:
            h += 12
        return f"{h:02d}:{mn:02d}"
    return None

def extract_quantity(text):
    m = re.search(r'(\d+)\s*(?:lot|lots|लॉट|laat)', text)
    return int(m.group(1)) if m else 1

def extract_expiry(text):
    for key, val in sorted(EXPIRY_MAP.items(), key=lambda x: -len(x[0])):
        if key in text:
            return val
    return "WEEKLY"

def extract_market_condition(text):
    for key, val in MARKET_CONDITIONS.items():
        if key in text:
            return val
    return None

def detect_language(text):
    hindi = len(re.findall(r'[\u0900-\u097F]', text))
    if hindi > 3:
        return "HINDI"
    hinglish_words = ["kharido","becho","lo","niklo","subah","shaam","lagao","banao","hai","karo","nahi"]
    if any(w in text for w in hinglish_words):
        return "HINGLISH"
    return "ENGLISH"

def extract_numbers(text):
    return [float(x) for x in re.findall(r'\b\d+\.?\d*\b', text)]

def calculate_confidence(result):
    score = 0.70
    if result.get("instrument"): score += 0.05
    if result.get("option_type"): score += 0.05
    if result.get("strategy"): score += 0.05
    if result.get("strike"): score += 0.05
    if result.get("indicators"): score += 0.05
    if result.get("execution_time"): score += 0.03
    if result.get("expiry"): score += 0.02
    return min(round(score, 2), 0.99)

# ═══════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════
@app.get("/")
def root():
    return {
        "status": "running",
        "version": "12.3",
        "nlp": "advanced_v2",
        "features": ["options","strategies","hindi","hinglish","conditions","time","greeks","risk"]
    }

@app.post("/strategy")
def parse_strategy(payload: dict):
    raw = payload.get("text", "")
    text = raw.lower().strip()

    instrument = extract_instrument(text)
    action = extract_action(text)
    strike = extract_strike(text)
    option_type = extract_option_type(text)
    strategy = extract_strategy(text)
    indicators = extract_indicators(text)
    exec_time = extract_time(text)
    quantity = extract_quantity(text)
    expiry = extract_expiry(text)
    market_condition = extract_market_condition(text)
    language = detect_language(text)
    numbers = extract_numbers(text)

    result = {
        "instrument": instrument,
        "action": action,
        "language": language,
        "expiry": expiry,
        "quantity": quantity,
    }

    if option_type: result["option_type"] = option_type
    if strike: result["strike"] = strike
    if strategy: result["strategy"] = strategy
    if indicators: result["indicators"] = indicators
    if exec_time: result["execution_time"] = exec_time
    if market_condition: result["market_condition"] = market_condition
    if len(numbers) > 0: result["numbers_found"] = numbers

    result["confidence"] = calculate_confidence(result)
    result["raw_input"] = raw
    result["parsed_at"] = time.strftime("%H:%M:%S")

    return result

@app.post("/trade")
def execute_trade(strategy: dict):
    conf = strategy.get("confidence", 0)
    if conf < 0.50:
        return {"status": "REJECTED", "reason": "Confidence too low", "confidence": conf}
    if conf < 0.70:
        return {"status": "REVIEW", "reason": "Manual review needed", "confidence": conf}
    return {
        "status": "EXECUTED",
        "result": strategy,
        "order_id": f"ORD{int(time.time() * 1000) % 1000000:06d}",
        "executed_at": time.strftime("%H:%M:%S")
    }

@app.get("/nlp/test")
def test_nlp():
    test_cases = [
        "buy nifty 22500 call weekly",
        "sell banknifty atm straddle",
        "nifty iron condor if vix > 15",
        "buy nifty if RSI < 30 and EMA crossover",
        "kharido nifty 50 lots subah",
        "बेचो बैंकनिफ्टी पुट",
        "nifty bull call spread at market open",
        "sell banknifty straddle if sideways",
    ]
    results = []
    for t in test_cases:
        from fastapi.testclient import TestClient
        results.append({"input": t, "parsed": parse_strategy({"text": t})})
    return results
