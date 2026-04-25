"""
Technical Analysis Engine v12.3
Complete indicator library without external dependencies
"""
import math
from typing import List, Optional, Tuple


def ema(prices: List[float], period: int) -> List[Optional[float]]:
    res = [None]*len(prices); k = 2/(period+1)
    for i,p in enumerate(prices):
        if i < period-1: continue
        res[i] = sum(prices[:period])/period if i==period-1 else p*k+res[i-1]*(1-k)
    return res

def sma(prices: List[float], period: int) -> List[Optional[float]]:
    res = [None]*len(prices)
    for i in range(period-1, len(prices)):
        res[i] = round(sum(prices[i-period+1:i+1])/period, 2)
    return res

def rsi(prices: List[float], period=14) -> List[Optional[float]]:
    res = [None]*len(prices)
    for i in range(period, len(prices)):
        gains = [max(0,prices[j]-prices[j-1]) for j in range(i-period+1,i+1)]
        losses = [max(0,prices[j-1]-prices[j]) for j in range(i-period+1,i+1)]
        ag = sum(gains)/period; al = sum(losses)/period
        res[i] = 100 if al==0 else round(100-(100/(1+ag/al)),2)
    return res

def macd(prices: List[float], fast=12, slow=26, signal=9):
    e_fast = ema(prices, fast); e_slow = ema(prices, slow)
    macd_line = [None]*len(prices)
    for i in range(len(prices)):
        if e_fast[i] and e_slow[i]:
            macd_line[i] = round(e_fast[i]-e_slow[i], 2)
    valid = [(i,v) for i,v in enumerate(macd_line) if v is not None]
    sig_vals = ema([v for _,v in valid], signal)
    sig_line = [None]*len(prices)
    hist = [None]*len(prices)
    for j,(i,_) in enumerate(valid):
        if j < len(sig_vals) and sig_vals[j]:
            sig_line[i] = round(sig_vals[j],2)
            hist[i] = round(macd_line[i]-sig_vals[j],2)
    return macd_line, sig_line, hist

def bollinger(prices: List[float], period=20, std_dev=2.0):
    upper=[None]*len(prices); mid=[None]*len(prices); lower=[None]*len(prices)
    for i in range(period-1, len(prices)):
        w = prices[i-period+1:i+1]; m = sum(w)/period
        s = math.sqrt(sum((x-m)**2 for x in w)/period)
        mid[i]=round(m,2); upper[i]=round(m+std_dev*s,2); lower[i]=round(m-std_dev*s,2)
    return upper, mid, lower

def atr(highs, lows, closes, period=14) -> List[Optional[float]]:
    trs = []
    for i in range(len(highs)):
        if i==0: trs.append(highs[i]-lows[i])
        else: trs.append(max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1])))
    res = [None]*len(highs)
    for i in range(period-1, len(highs)):
        res[i] = round(sum(trs[i-period+1:i+1])/period, 2)
    return res

def supertrend(highs, lows, closes, period=7, multiplier=3.0):
    _atr = atr(highs, lows, closes, period)
    trend = [None]*len(closes); direction = [None]*len(closes)
    upper = [None]*len(closes); lower = [None]*len(closes)
    for i in range(period, len(closes)):
        if _atr[i] is None: continue
        hl2 = (highs[i]+lows[i])/2
        basic_upper = hl2 + multiplier*_atr[i]
        basic_lower = hl2 - multiplier*_atr[i]
        if i==period:
            upper[i]=basic_upper; lower[i]=basic_lower
        else:
            upper[i] = min(basic_upper, upper[i-1]) if closes[i-1]<=upper[i-1] else basic_upper
            lower[i] = max(basic_lower, lower[i-1]) if closes[i-1]>=lower[i-1] else basic_lower
        if i==period: direction[i] = 1
        elif closes[i] > upper[i-1]: direction[i] = 1
        elif closes[i] < lower[i-1]: direction[i] = -1
        else: direction[i] = direction[i-1]
        trend[i] = lower[i] if direction[i]==1 else upper[i]
    return trend, direction

def stochastic(highs, lows, closes, k_period=14, d_period=3):
    k = [None]*len(closes); d = [None]*len(closes)
    for i in range(k_period-1, len(closes)):
        hh = max(highs[i-k_period+1:i+1]); ll = min(lows[i-k_period+1:i+1])
        k[i] = round((closes[i]-ll)/(hh-ll)*100,2) if hh!=ll else 50
    k_valid = [v for v in k if v is not None]
    d_sma = sma(k_valid, d_period)
    j = 0
    for i in range(len(k)):
        if k[i] is not None:
            d[i] = d_sma[j] if j<len(d_sma) else None; j+=1
    return k, d

def vwap(highs, lows, closes, volumes) -> List[Optional[float]]:
    res = [None]*len(closes)
    cum_pv = 0; cum_v = 0
    for i in range(len(closes)):
        tp = (highs[i]+lows[i]+closes[i])/3
        cum_pv += tp*volumes[i]; cum_v += volumes[i]
        res[i] = round(cum_pv/cum_v,2) if cum_v>0 else closes[i]
    return res

def adx(highs, lows, closes, period=14):
    dx_list = []; adx_list = [None]*len(closes)
    for i in range(1, len(closes)):
        h_diff = highs[i]-highs[i-1]; l_diff = lows[i-1]-lows[i]
        dm_plus = h_diff if h_diff>l_diff and h_diff>0 else 0
        dm_minus = l_diff if l_diff>h_diff and l_diff>0 else 0
        tr = max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1]))
        if i >= period:
            if tr > 0:
                di_plus = dm_plus/tr*100; di_minus = dm_minus/tr*100
                dx = abs(di_plus-di_minus)/(di_plus+di_minus+1)*100
                dx_list.append(dx)
                if len(dx_list) >= period:
                    adx_list[i] = round(sum(dx_list[-period:])/period,2)
    return adx_list

def cci(highs, lows, closes, period=20) -> List[Optional[float]]:
    res = [None]*len(closes)
    for i in range(period-1, len(closes)):
        tp = [(highs[j]+lows[j]+closes[j])/3 for j in range(i-period+1,i+1)]
        m = sum(tp)/period; md = sum(abs(x-m) for x in tp)/period
        res[i] = round((tp[-1]-m)/(0.015*md),2) if md>0 else 0
    return res

def williams_r(highs, lows, closes, period=14) -> List[Optional[float]]:
    res = [None]*len(closes)
    for i in range(period-1, len(closes)):
        hh = max(highs[i-period+1:i+1]); ll = min(lows[i-period+1:i+1])
        res[i] = round((hh-closes[i])/(hh-ll)*-100,2) if hh!=ll else -50
    return res

def roc(prices: List[float], period=12) -> List[Optional[float]]:
    res = [None]*len(prices)
    for i in range(period, len(prices)):
        res[i] = round((prices[i]-prices[i-period])/prices[i-period]*100,2)
    return res

def mfi(highs, lows, closes, volumes, period=14) -> List[Optional[float]]:
    res = [None]*len(closes); tp_list = []
    for i in range(len(closes)):
        tp = (highs[i]+lows[i]+closes[i])/3
        mf = tp*volumes[i]; tp_list.append((tp,mf))
        if i >= period:
            pos = sum(m for j in range(i-period+1,i+1) if tp_list[j][0]>=tp_list[j-1][0] for m in [tp_list[j][1]])
            neg = sum(m for j in range(i-period+1,i+1) if tp_list[j][0]<tp_list[j-1][0] for m in [tp_list[j][1]])
            res[i] = 100 if neg==0 else round(100-(100/(1+pos/neg)),2)
    return res

def pivot_points(high, low, close):
    pp = (high+low+close)/3
    return {
        "PP": round(pp,2), "R1": round(2*pp-low,2), "R2": round(pp+(high-low),2),
        "R3": round(high+2*(pp-low),2), "S1": round(2*pp-high,2),
        "S2": round(pp-(high-low),2), "S3": round(low-2*(high-pp),2),
    }

def detect_patterns(opens, highs, lows, closes) -> List[dict]:
    patterns = []
    for i in range(2, len(closes)):
        o,h,l,c = opens[i],highs[i],lows[i],closes[i]
        po,ph,pl,pc = opens[i-1],highs[i-1],lows[i-1],closes[i-1]
        body = abs(c-o); prev_body = abs(pc-po)
        # Doji
        if body < 0.1*(h-l): patterns.append({"bar":i,"pattern":"DOJI","signal":"NEUTRAL"})
        # Hammer
        if (l < o and (o-l) > 2*body and (h-max(o,c)) < 0.1*body):
            patterns.append({"bar":i,"pattern":"HAMMER","signal":"BULLISH"})
        # Shooting Star
        if (h > o and (h-max(o,c)) > 2*body and (min(o,c)-l) < 0.1*body):
            patterns.append({"bar":i,"pattern":"SHOOTING_STAR","signal":"BEARISH"})
        # Bullish Engulfing
        if pc>po and c>o and c>po and o<pc:
            patterns.append({"bar":i,"pattern":"BULL_ENGULF","signal":"BULLISH"})
        # Bearish Engulfing
        if pc<po and c<o and c<po and o>pc:
            patterns.append({"bar":i,"pattern":"BEAR_ENGULF","signal":"BEARISH"})
        # Pin Bar
        lower_wick = min(o,c)-l; upper_wick = h-max(o,c)
        if lower_wick > 3*body: patterns.append({"bar":i,"pattern":"PIN_BAR_BULL","signal":"BULLISH"})
        if upper_wick > 3*body: patterns.append({"bar":i,"pattern":"PIN_BAR_BEAR","signal":"BEARISH"})
    return patterns[-10:]  # Last 10 patterns

def compute_all(highs, lows, opens, closes, volumes=None, period_close=None) -> dict:
    """Compute all indicators at once for latest bar"""
    if volumes is None: volumes = [1000000]*len(closes)
    if period_close is None: period_close = closes
    i = len(closes)-1
    _ema9 = ema(closes,9); _ema21 = ema(closes,21); _ema50 = ema(closes,50)
    _ema200 = ema(closes,200); _rsi = rsi(closes,14); _atr = atr(highs,lows,closes,14)
    _bb_u,_bb_m,_bb_l = bollinger(closes,20,2); _macd,_sig,_hist = macd(closes)
    _st,_dir = supertrend(highs,lows,closes,7,3)
    _vwap = vwap(highs,lows,closes,volumes); _cci = cci(highs,lows,closes,20)
    _stk,_std = stochastic(highs,lows,closes,14,3)
    _adx = adx(highs,lows,closes,14)
    return {
        "price": closes[i],
        "ema9": _ema9[i], "ema21": _ema21[i], "ema50": _ema50[i], "ema200": _ema200[i],
        "rsi": _rsi[i], "atr": _atr[i],
        "bb_upper": _bb_u[i], "bb_mid": _bb_m[i], "bb_lower": _bb_l[i],
        "macd": _macd[i], "macd_signal": _sig[i], "macd_hist": _hist[i],
        "supertrend": _st[i], "supertrend_dir": _dir[i],
        "vwap": _vwap[i], "cci": _cci[i],
        "stoch_k": _stk[i], "stoch_d": _std[i], "adx": _adx[i],
        "signals": {
            "ema_cross_bull": bool(_ema9[i] and _ema21[i] and _ema9[i] > _ema21[i]),
            "rsi_oversold": bool(_rsi[i] and _rsi[i] < 30),
            "rsi_overbought": bool(_rsi[i] and _rsi[i] > 70),
            "above_vwap": bool(_vwap[i] and closes[i] > _vwap[i]),
            "supertrend_bull": bool(_dir[i] and _dir[i] == 1),
            "macd_bull": bool(_hist[i] and _hist[i] > 0),
            "bb_squeeze": bool(_bb_u[i] and _bb_l[i] and (_bb_u[i]-_bb_l[i]) < _bb_u[i]*0.03),
        },
        "pivot": pivot_points(highs[i], lows[i], closes[i]),
        "patterns": detect_patterns(opens,highs,lows,closes),
    }
