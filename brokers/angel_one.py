"""
TRD v12.3 — Angel One SmartAPI Integration
Full live trading: Auth, Quotes, Orders, Portfolio
"""
import json, hashlib, time, os
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))
ANGEL_BASE = "https://apiconnect.angelone.in"

# ── HTTP Helper (no requests dependency) ────────────────────────
def _http(method, url, headers=None, body=None, timeout=15):
    import urllib.request, urllib.error
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read())
        except: return {"errorcode": str(e.code), "message": str(e)}
    except Exception as e:
        return {"errorcode": "NETWORK", "message": str(e)}

# ── Session Store (per user) ─────────────────────────────────────
_sessions = {}  # {user_id: {jwt_token, refresh_token, feed_token, expires_at, client_code}}

def _get_headers(api_key: str, jwt_token: str = "") -> dict:
    return {
        "Content-Type":      "application/json",
        "Accept":            "application/json",
        "X-UserType":        "USER",
        "X-SourceID":        "WEB",
        "X-ClientLocalIP":   "13.53.175.88",
        "X-ClientPublicIP":  "13.53.175.88",
        "X-MACAddress":      "fe:80:00:00:00:00",
        "X-PrivateKey":      api_key,
        **({"Authorization": f"Bearer {jwt_token}"} if jwt_token else {}),
    }

# ── AUTHENTICATION ───────────────────────────────────────────────
def login(api_key: str, client_code: str, mpin: str, totp: str = "") -> dict:
    """
    Login to Angel One SmartAPI
    Returns: {success, jwt_token, refresh_token, feed_token, client_code}
    """
    url = f"{ANGEL_BASE}/rest/auth/angelbroking/user/v1/loginByPassword"
    body = {
        "clientcode": client_code,
        "password":   mpin,
        "totp":       totp,
    }
    headers = _get_headers(api_key)
    result  = _http("POST", url, headers=headers, body=body)
    
    if result.get("status") == True and result.get("data"):
        data = result["data"]
        return {
            "success":       True,
            "jwt_token":     data.get("jwtToken",""),
            "refresh_token": data.get("refreshToken",""),
            "feed_token":    data.get("feedToken",""),
            "client_code":   client_code,
            "name":          data.get("name",""),
            "message":       "Login successful"
        }
    else:
        return {
            "success": False,
            "error":   result.get("message") or result.get("errorMessage") or "Login failed",
            "code":    result.get("errorcode",""),
        }

def generate_totp(secret: str) -> str:
    """Generate TOTP from secret (for automated login)"""
    try:
        import hmac, struct
        # Base32 decode
        import base64
        key = base64.b32decode(secret.upper().replace(' ',''))
        # Time counter (30-second window)
        counter = int(time.time() // 30)
        msg = struct.pack(">Q", counter)
        h   = hmac.new(key, msg, "sha1").digest()
        o   = h[-1] & 0xf
        code= (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
        return str(code).zfill(6)
    except Exception as e:
        return ""

# ── STORE SESSION ────────────────────────────────────────────────
def store_session(user_id: str, session_data: dict):
    """Store session for reuse"""
    _sessions[user_id] = {
        **session_data,
        "expires_at": time.time() + 7*3600  # Valid ~7 hours
    }

def get_session(user_id: str) -> dict:
    """Get valid session or None"""
    s = _sessions.get(user_id)
    if s and s.get("jwt_token") and time.time() < s.get("expires_at", 0):
        return s
    return None

# ── LIVE MARKET DATA ─────────────────────────────────────────────
EXCHANGE_TOKENS = {
    "NIFTY":      {"exchange":"NSE","token":"26000","symbol":"Nifty 50"},
    "BANKNIFTY":  {"exchange":"NSE","token":"26009","symbol":"Nifty Bank"},
    "FINNIFTY":   {"exchange":"NSE","token":"26037","symbol":"Nifty Fin Service"},
    "MIDCPNIFTY": {"exchange":"NSE","token":"26074","symbol":"Nifty Midcap Select"},
    "SENSEX":     {"exchange":"BSE","token":"1",    "symbol":"SENSEX"},
    "NIFTYNXT50": {"exchange":"NSE","token":"26013","symbol":"Nifty Next 50"},
    "INDIA_VIX":  {"exchange":"NSE","token":"26017","symbol":"India VIX"},
    "BANKEX":     {"exchange":"BSE","token":"270",  "symbol":"BANKEX"},
}

def get_live_quote(api_key: str, jwt_token: str, instrument: str) -> dict:
    """Get live LTP for an instrument"""
    info = EXCHANGE_TOKENS.get(instrument, EXCHANGE_TOKENS["NIFTY"])
    url  = f"{ANGEL_BASE}/rest/secure/angelbroking/market/v1/quote/"
    body = {
        "mode": "FULL",
        "exchangeTokens": {info["exchange"]: [info["token"]]}
    }
    result = _http("POST", url, headers=_get_headers(api_key, jwt_token), body=body)
    
    if result.get("status") == True:
        data = result.get("data",{})
        fetched = data.get("fetched",[])
        if fetched:
            q = fetched[0]
            return {
                "symbol":      instrument,
                "ltp":         float(q.get("ltp",0)),
                "open":        float(q.get("open",0)),
                "high":        float(q.get("high",0)),
                "low":         float(q.get("low",0)),
                "close":       float(q.get("close",0)),
                "change":      float(q.get("netChange",0)),
                "pct_change":  float(q.get("percentChange",0)),
                "volume":      int(q.get("tradeVolume",0)),
                "oi":          int(q.get("openInterest",0)),
                "timestamp":   datetime.now(IST).isoformat(),
            }
    return {"error": result.get("message","Quote failed"), "instrument": instrument}

def get_all_live_prices(api_key: str, jwt_token: str) -> dict:
    """Get live prices for ALL major indices with full OHLC data"""
    result = {}
    tokens_by_exchange = {}
    for inst, info in EXCHANGE_TOKENS.items():
        ex = info["exchange"]
        if ex not in tokens_by_exchange:
            tokens_by_exchange[ex] = []
        tokens_by_exchange[ex].append((inst, info["token"]))
    
    url  = f"{ANGEL_BASE}/rest/secure/angelbroking/market/v1/quote/"
    # Use FULL mode to get OHLC + change data
    body = {"mode": "FULL", "exchangeTokens": {
        ex: [t for _,t in pairs]
        for ex, pairs in tokens_by_exchange.items()
    }}
    resp = _http("POST", url, headers=_get_headers(api_key, jwt_token), body=body)
    
    if resp.get("status") == True:
        fetched = resp.get("data", {}).get("fetched", [])
        token_map = {info["token"]: inst for inst, info in EXCHANGE_TOKENS.items()}
        for q in fetched:
            inst = token_map.get(q.get("symbolToken",""), "UNKNOWN")
            if inst == "UNKNOWN": continue
            ltp    = float(q.get("ltp", 0) or 0)
            close  = float(q.get("close", ltp) or ltp)
            change = round(ltp - close, 2)
            pct    = round(change / max(close, 1) * 100, 2)
            result[inst] = {
                "price":  ltp,
                "ltp":    ltp,
                "open":   float(q.get("open",  0) or 0),
                "high":   float(q.get("high",  0) or 0),
                "low":    float(q.get("low",   0) or 0),
                "close":  close,
                "change": change,
                "pct":    pct,
                "volume": int(q.get("tradeVolume", 0) or 0),
            }
    return result

# ── OPTION CHAIN ─────────────────────────────────────────────────
def get_option_chain(api_key: str, jwt_token: str, instrument: str, expiry: str) -> dict:
    """Get live option chain from Angel One"""
    url  = f"{ANGEL_BASE}/rest/secure/angelbroking/market/v1/optionChain"
    info = EXCHANGE_TOKENS.get(instrument, EXCHANGE_TOKENS["NIFTY"])
    body = {
        "name":      info["symbol"],
        "expirydate":expiry  # "22MAY2025" format
    }
    result = _http("GET", url + f"?name={info['symbol']}&expirydate={expiry}",
                   headers=_get_headers(api_key, jwt_token))
    return result

# ── PLACE ORDER ──────────────────────────────────────────────────
def place_order(api_key: str, jwt_token: str, 
                instrument: str, strike: int, option_type: str,
                action: str, lots: int, order_type: str = "MARKET",
                price: float = 0, sl: float = 0, target: float = 0) -> dict:
    """Place a real order via Angel One"""
    
    LOT_SIZES = {"NIFTY":75,"BANKNIFTY":30,"FINNIFTY":40,"MIDCPNIFTY":75,"SENSEX":10}
    # Note: Using SmartAPI lot sizes (may differ from NSE)
    lot_size = LOT_SIZES.get(instrument, 75)
    qty = lots * lot_size
    
    # Build trading symbol (e.g., "NIFTY22MAY25C24000")
    now  = datetime.now(IST)
    # Get nearest weekly expiry
    days_to_thu = (3 - now.weekday()) % 7
    if days_to_thu == 0 and now.hour >= 15: days_to_thu = 7
    expiry_dt   = now + timedelta(days=days_to_thu)
    exp_str     = expiry_dt.strftime("%d%b%y").upper()
    
    tradingsymbol = f"{instrument}{exp_str}{'C' if option_type=='CE' else 'P'}{strike}"
    
    url  = f"{ANGEL_BASE}/rest/secure/angelbroking/order/v1/placeOrder"
    body = {
        "variety":         "NORMAL",
        "tradingsymbol":   tradingsymbol,
        "symboltoken":     "0",  # Will be resolved by API
        "transactiontype": action,  # "BUY" or "SELL"
        "exchange":        "NFO",
        "ordertype":       order_type,  # "MARKET" or "LIMIT"
        "producttype":     "CARRYFORWARD",
        "duration":        "DAY",
        "price":           str(price) if order_type=="LIMIT" else "0",
        "squareoff":       str(target) if target else "0",
        "stoploss":        str(sl) if sl else "0",
        "quantity":        str(qty),
    }
    
    result = _http("POST", url, headers=_get_headers(api_key, jwt_token), body=body)
    
    if result.get("status") == True:
        return {
            "success":      True,
            "order_id":     result.get("data",{}).get("orderid",""),
            "symbol":       tradingsymbol,
            "qty":          qty,
            "lots":         lots,
            "action":       action,
            "order_type":   order_type,
            "message":      f"Order placed: {action} {lots} lot {instrument} {strike} {option_type}"
        }
    else:
        return {
            "success": False,
            "error":   result.get("message") or result.get("errorMessage") or "Order failed",
            "code":    result.get("errorcode",""),
        }

# ── PORTFOLIO ────────────────────────────────────────────────────
def get_portfolio(api_key: str, jwt_token: str) -> dict:
    """Get live positions from Angel One"""
    url    = f"{ANGEL_BASE}/rest/secure/angelbroking/order/v1/getPosition"
    result = _http("GET", url, headers=_get_headers(api_key, jwt_token))
    
    if result.get("status") == True:
        positions = result.get("data",[]) or []
        return {
            "positions": [
                {
                    "symbol":       p.get("tradingsymbol",""),
                    "qty":          int(p.get("netqty",0)),
                    "avg_price":    float(p.get("avgnetprice",0)),
                    "ltp":          float(p.get("ltp",0)),
                    "pnl":          float(p.get("unrealised",0)),
                    "day_pnl":      float(p.get("pnl",0)),
                    "product":      p.get("producttype",""),
                    "exchange":     p.get("exchange",""),
                }
                for p in positions if int(p.get("netqty",0)) != 0
            ]
        }
    return {"positions": [], "error": result.get("message","")}

# ── ORDER BOOK ───────────────────────────────────────────────────
def get_order_book(api_key: str, jwt_token: str) -> dict:
    url    = f"{ANGEL_BASE}/rest/secure/angelbroking/order/v1/getOrderBook"
    result = _http("GET", url, headers=_get_headers(api_key, jwt_token))
    orders = result.get("data",[]) or [] if result.get("status") else []
    return {"orders": orders}

print("✅ angel_one.py created")
