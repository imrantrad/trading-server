"""
Real Market Data Feed v12.3
NSE + Yahoo Finance — No API key needed
"""
import urllib.request, json, time, re
from typing import Dict, Optional


def fetch_nse_quote(symbol: str) -> Optional[dict]:
    """Fetch live quote from NSE India"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/",
        }
        # NSE Index quote
        if symbol in ["NIFTY","NIFTY50","^NSEI"]:
            url = "https://www.nseindia.com/api/allIndices"
        else:
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())

        if symbol in ["NIFTY","NIFTY50"]:
            for idx in data.get("data",[]):
                if "NIFTY 50" in idx.get("index",""):
                    return {
                        "symbol":"NIFTY","name":"NIFTY 50",
                        "last":idx.get("last",0),
                        "open":idx.get("open",0),
                        "high":idx.get("high",0),
                        "low":idx.get("low",0),
                        "previousClose":idx.get("previousClose",0),
                        "change":idx.get("change",0),
                        "pChange":idx.get("percentChange",0),
                        "source":"NSE_LIVE",
                    }
        return None
    except Exception as e:
        return None


def fetch_yahoo_quote(symbol: str) -> Optional[dict]:
    """Fetch from Yahoo Finance — works globally"""
    yahoo_map = {
        "NIFTY":"^NSEI","BANKNIFTY":"^NSEBANK","SENSEX":"^BSESN",
        "FINNIFTY":"NIFTY_FIN_SERVICE.NS","MIDCPNIFTY":"NIFTY_MID_SELECT.NS",
        "USDINR":"USDINR=X","GOLD":"GC=F","CRUDE":"CL=F","VIX":"^INDIAVIX",
        "RELIANCE":"RELIANCE.NS","TCS":"TCS.NS","HDFC":"HDFCBANK.NS",
        "INFOSYS":"INFY.NS","ICICI":"ICICIBANK.NS","SBI":"SBIN.NS",
        "NIFTYIT":"^CNXIT","NIFTYAUTO":"^CNXAUTO","NIFTYBANK":"^NSEBANK",
    }
    ticker = yahoo_map.get(symbol.upper(), symbol+".NS")
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
        headers = {"User-Agent":"Mozilla/5.0","Accept":"application/json"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        meta = data["chart"]["result"][0]["meta"]
        prev = meta.get("previousClose", meta.get("chartPreviousClose",0))
        curr = meta.get("regularMarketPrice", meta.get("price",0))
        chng = curr - prev if prev else 0
        pchng = (chng/prev*100) if prev else 0
        return {
            "symbol": symbol,
            "last": round(curr, 2),
            "open": round(meta.get("regularMarketOpen", curr), 2),
            "high": round(meta.get("regularMarketDayHigh", curr), 2),
            "low": round(meta.get("regularMarketDayLow", curr), 2),
            "previousClose": round(prev, 2),
            "change": round(chng, 2),
            "pChange": round(pchng, 2),
            "volume": meta.get("regularMarketVolume", 0),
            "marketCap": meta.get("marketCap", 0),
            "52wHigh": meta.get("fiftyTwoWeekHigh", 0),
            "52wLow": meta.get("fiftyTwoWeekLow", 0),
            "source": "YAHOO_FINANCE",
            "timestamp": time.strftime("%H:%M:%S"),
        }
    except Exception as e:
        return None


def fetch_all_indices() -> Dict[str, dict]:
    """Fetch all major indices"""
    symbols = ["NIFTY","BANKNIFTY","SENSEX","FINNIFTY","VIX","USDINR","GOLD","CRUDE"]
    results = {}
    for sym in symbols:
        data = fetch_yahoo_quote(sym)
        if data:
            results[sym] = data
        time.sleep(0.1)  # Rate limit
    return results


def fetch_historical(symbol: str, period: str = "1mo", interval: str = "1d") -> list:
    """Fetch historical OHLCV data"""
    yahoo_map = {
        "NIFTY":"^NSEI","BANKNIFTY":"^NSEBANK","SENSEX":"^BSESN",
        "FINNIFTY":"NIFTY_FIN_SERVICE.NS","VIX":"^INDIAVIX",
    }
    ticker = yahoo_map.get(symbol.upper(), symbol+".NS")
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range={period}"
        headers = {"User-Agent":"Mozilla/5.0","Accept":"application/json"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        ohlcv = result["indicators"]["quote"][0]
        candles = []
        for i, ts in enumerate(timestamps):
            if ohlcv["close"][i] is None: continue
            candles.append({
                "timestamp": time.strftime("%Y-%m-%d", time.localtime(ts)),
                "open": round(ohlcv["open"][i] or 0, 2),
                "high": round(ohlcv["high"][i] or 0, 2),
                "low": round(ohlcv["low"][i] or 0, 2),
                "close": round(ohlcv["close"][i] or 0, 2),
                "volume": int(ohlcv["volume"][i] or 0),
            })
        return candles
    except Exception as e:
        return []


# Cache to avoid too many requests
_cache: Dict[str, dict] = {}
_cache_time: Dict[str, float] = {}
CACHE_TTL = 60  # 60 seconds

def get_quote_cached(symbol: str) -> Optional[dict]:
    now = time.time()
    if symbol in _cache and (now - _cache_time.get(symbol,0)) < CACHE_TTL:
        return {**_cache[symbol], "cached": True}
    data = fetch_yahoo_quote(symbol)
    if data:
        _cache[symbol] = data
        _cache_time[symbol] = now
    return data
