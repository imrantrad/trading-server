from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ─── INSTRUMENT MAP ───────────────────────────────────────────
INSTRUMENTS = {
    "nifty": "NIFTY", "nifty50": "NIFTY", "निफ्टी": "NIFTY",
    "banknifty": "BANKNIFTY", "bank nifty": "BANKNIFTY",
    "बैंकनिफ्टी": "BANKNIFTY", "bankनिफ्टी": "BANKNIFTY",
    "sensex": "SENSEX", "सेंसेक्स": "SENSEX",
    "finnifty": "FINNIFTY", "fin nifty": "FINNIFTY",
    "midcap": "MIDCPNIFTY",
}

# ─── ACTION MAP ───────────────────────────────────────────────
BUY_WORDS = [
    "buy", "long", "call", "bullish", "upside", "kharido",
    "le lo", "lelo", "खरीदो", "खरीद", "lo", "लो",
    "entry", "enter", "open"
]
SELL_WORDS = [
    "sell", "short", "put", "bearish", "downside", "becho",
    "bech do", "bechdo", "बेचो", "बेच", "exit", "close",
    "niklo", "nikal"
]

# ─── OPTION TYPE ──────────────────────────────────────────────
OPTION_TYPES = {
    "call": "CE", "ce": "CE", "कॉल": "CE",
    "put": "PE", "pe": "PE", "पुट": "PE",
    "straddle": "STRADDLE", "strangle": "STRANGLE",
    "iron condor": "IRON_CONDOR", "condor": "IRON_CONDOR",
    "bull call spread": "BULL_CALL_SPREAD",
    "bear put spread": "BEAR_PUT_SPREAD",
    "butterfly": "BUTTERFLY",
}

# ─── STRATEGY MAP ─────────────────────────────────────────────
STRATEGIES = {
    "straddle": "STRADDLE",
    "strangle": "STRANGLE",
    "iron condor": "IRON_CONDOR",
    "bull call spread": "BULL_CALL_SPREAD",
    "bear put spread": "BEAR_PUT_SPREAD",
    "butterfly": "BUTTERFLY",
    "atm": "ATM",
    "itm": "ITM",
    "otm": "OTM",
}

# ─── CONDITIONS ───────────────────────────────────────────────
CONDITIONS = {
    "rsi": "RSI", "ema": "EMA", "sma": "SMA",
    "macd": "MACD", "vwap": "VWAP", "bb": "BOLLINGER",
    "bollinger": "BOLLINGER", "supertrend": "SUPERTREND",
    "if price": "PRICE_CONDITION",
    "stop loss": "STOPLOSS", "sl": "STOPLOSS",
    "target": "TARGET", "tp": "TARGET",
}

# ─── TIME MAP ─────────────────────────────────────────────────
TIME_WORDS = {
    "morning": "09:20", "subah": "09:20", "सुबह": "09:20",
    "opening": "09:15", "open": "09:15",
    "closing": "15:15", "close": "15:15",
    "shaam": "15:00", "शाम": "15:00",
}

def extract_instrument(text):
    for key, val in INSTRUMENTS.items():
        if key in text:
            return val
    return "NIFTY"

def extract_action(text):
    for w in SELL_WORDS:
        if w in text:
            return "SELL"
    for w in BUY_WORDS:
        if w in text:
            return "BUY"
    return "BUY"

def extract_strike(text):
    match = re.search(r'\b(\d{4,6})\b', text)
    return int(match.group(1)) if match else None

def extract_option_type(text):
    for key, val in OPTION_TYPES.items():
        if key in text:
            return val
    return None

def extract_strategy(text):
    for key, val in STRATEGIES.items():
        if key in text:
            return val
    return None

def extract_conditions(text):
    found = []
    for key, val in CONDITIONS.items():
        if key in text:
            num = re.search(rf'{key}\s*[<>=]?\s*(\d+)', text)
            if num:
                found.append(f"{val}={num.group(1)}")
            else:
                found.append(val)
    return found if found else None

def extract_time(text):
    for key, val in TIME_WORDS.items():
        if key in text:
            return val
    time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', text)
    if time_match:
        return time_match.group(0)
    return None

def extract_quantity(text):
    match = re.search(r'(\d+)\s*(lot|lots|लॉट)', text)
    return int(match.group(1)) if match else 1

def extract_expiry(text):
    if "weekly" in text or "week" in text:
        return "WEEKLY"
    if "monthly" in text or "month" in text:
        return "MONTHLY"
    return "WEEKLY"

def detect_language(text):
    hindi_chars = re.findall(r'[\u0900-\u097F]', text)
    if len(hindi_chars) > 2:
        return "HINDI"
    hindi_words = ["kharido", "becho", "nifty", "lo", "niklo", "subah", "shaam"]
    for w in hindi_words:
        if w in text:
            return "HINGLISH"
    return "ENGLISH"

@app.get("/")
def root():
    return {"status": "running", "version": "12.3", "nlp": "advanced"}

@app.post("/strategy")
def parse_strategy(payload: dict):
    raw = payload.get("text", "")
    text = raw.lower().strip()

    instrument = extract_instrument(text)
    action = extract_action(text)
    strike = extract_strike(text)
    option_type = extract_option_type(text)
    strategy = extract_strategy(text)
    conditions = extract_conditions(text)
    exec_time = extract_time(text)
    quantity = extract_quantity(text)
    expiry = extract_expiry(text)
    language = detect_language(text)

    confidence = 0.92
    if conditions:
        confidence = 0.95
    if strategy:
        confidence = 0.93
    if strike and option_type:
        confidence = 0.97

    result = {
        "instrument": instrument,
        "action": action,
        "confidence": confidence,
        "language": language,
        "raw_input": raw,
    }

    if strike:
        result["strike"] = strike
    if option_type:
        result["option_type"] = option_type
    if strategy:
        result["strategy"] = strategy
    if conditions:
        result["conditions"] = conditions
    if exec_time:
        result["execution_time"] = exec_time
    if quantity > 1:
        result["quantity"] = quantity
    if expiry:
        result["expiry"] = expiry

    return result

@app.post("/trade")
def execute_trade(strategy: dict):
    if strategy.get("confidence", 0) < 0.5:
        return {"status": "REJECTED", "reason": "Low confidence"}
    return {
        "status": "EXECUTED",
        "result": strategy,
        "order_id": f"ORD{__import__('time').time_ns() % 1000000:06d}"
    }
