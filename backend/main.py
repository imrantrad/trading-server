"""
Trading System v12.3 - Complete Backend
FastAPI + Paper Engine + Risk Manager + Full NLP
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import re, time, json, random
from datetime import datetime

try:
    from paper.paper_engine import PaperTradingEngine
    from risk.risk_manager import RiskManager, RiskParams
except:
    pass

app = FastAPI(title="Trading System v12.3", version="12.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Global engines
paper_engine = PaperTradingEngine(capital=500000)
risk_manager = RiskManager()

# ═══════════════════════════════════════
# NLP DATA
# ═══════════════════════════════════════
INSTRUMENTS = {
    "nifty 50":"NIFTY","nifty50":"NIFTY","nifty":"NIFTY","nf":"NIFTY","निफ्टी":"NIFTY",
    "bank nifty":"BANKNIFTY","banknifty":"BANKNIFTY","bnf":"BANKNIFTY","बैंकनिफ्टी":"BANKNIFTY",
    "fin nifty":"FINNIFTY","finnifty":"FINNIFTY","fn":"FINNIFTY",
    "midcap nifty":"MIDCPNIFTY","midcap":"MIDCPNIFTY",
    "sensex":"SENSEX","सेंसेक्स":"SENSEX",
}
LOT_SIZES={"NIFTY":50,"BANKNIFTY":15,"FINNIFTY":40,"MIDCPNIFTY":75,"SENSEX":10}
BUY_WORDS=["buy","long","bullish","call buy","entry","enter","accumulate","kharido","le lo","lelo","lo","खरीदो","badhega","upar"]
SELL_WORDS=["sell","short","bearish","put buy","exit","close","square off","becho","bech","niklo","nikal","बेचो","girega","neeche"]
OPTION_TYPES={"call":"CE","ce":"CE","कॉल":"CE","put":"PE","pe":"PE","पुट":"PE"}
STRATEGIES={
    "short straddle":"SHORT_STRADDLE","long straddle":"LONG_STRADDLE","atm straddle":"ATM_STRADDLE","straddle":"STRADDLE",
    "short strangle":"SHORT_STRANGLE","long strangle":"LONG_STRANGLE","otm strangle":"OTM_STRANGLE","strangle":"STRANGLE",
    "covered call":"COVERED_CALL","protective put":"PROTECTIVE_PUT","cash secured put":"CSP",
    "bull call spread":"BULL_CALL_SPREAD","bear call spread":"BEAR_CALL_SPREAD",
    "bull put spread":"BULL_PUT_SPREAD","bear put spread":"BEAR_PUT_SPREAD",
    "iron condor":"IRON_CONDOR","iron butterfly":"IRON_BUTTERFLY",
    "broken wing butterfly":"BWB","butterfly":"BUTTERFLY","condor":"CONDOR",
    "calendar spread":"CALENDAR_SPREAD","diagonal spread":"DIAGONAL_SPREAD",
    "ratio spread":"RATIO_SPREAD","collar":"COLLAR","risk reversal":"RISK_REVERSAL",
    "synthetic long":"SYNTH_LONG","synthetic short":"SYNTH_SHORT",
    "delta hedge":"DELTA_HEDGE","gamma scalp":"GAMMA_SCALP",
}
CONDITIONS={
    "rsi oversold":"RSI_OS","rsi overbought":"RSI_OB","rsi divergence":"RSI_DIV","rsi crossover":"RSI_CROSS","rsi":"RSI",
    "macd crossover":"MACD_CROSS","macd bullish":"MACD_BULL","macd bearish":"MACD_BEAR","macd":"MACD",
    "ema crossover":"EMA_CROSS","ema200":"EMA200","ema50":"EMA50","ema":"EMA",
    "golden cross":"GOLDEN_CROSS","death cross":"DEATH_CROSS",
    "supertrend buy":"ST_BUY","supertrend sell":"ST_SELL","supertrend":"SUPERTREND",
    "bb squeeze":"BB_SQ","bb breakout":"BB_BO","bollinger":"BB",
    "vix spike":"VIX_SPK","vix crush":"VIX_CRUSH","india vix":"VIX","vix":"VIX",
    "iv rank":"IV_RANK","iv percentile":"IV_PERC","iv crush":"IV_CRUSH","iv expansion":"IV_EXP","iv":"IV",
    "vwap breakout":"VWAP_BO","vwap bounce":"VWAP_BNC","vwap":"VWAP",
    "volume surge":"VOL_SURGE","volume breakout":"VOL_BO","obv":"OBV",
    "breakout":"BREAKOUT","breakdown":"BREAKDOWN","reversal":"REVERSAL",
    "support":"SUPPORT","resistance":"RESISTANCE",
    "gap up":"GAP_UP","gap down":"GAP_DOWN",
    "order block":"ORDER_BLOCK","fair value gap":"FVG","fvg":"FVG",
    "change of character":"CHOCH","choch":"CHOCH","break of structure":"BOS","bos":"BOS",
    "liquidity sweep":"LIQ_SWEEP","stop hunt":"STOP_HUNT",
    "wyckoff spring":"SPRING","wyckoff upthrust":"UPTHRUST","wyckoff":"WYCKOFF",
    "oi buildup":"OI_BUILD","oi unwinding":"OI_UNWIND","open interest":"OI",
    "pcr high":"PCR_HIGH","pcr low":"PCR_LOW","pcr":"PCR",
    "gamma exposure":"GEX","gamma flip":"GAMMA_FLIP","max pain":"MAX_PAIN",
    "dark pool":"DARK_POOL","unusual activity":"UNUSUAL_ACT","block trade":"BLOCK",
    "fii buying":"FII_BUY","fii selling":"FII_SELL","fii":"FII",
    "dii buying":"DII_BUY","dii selling":"DII_SELL",
    "sgx nifty":"SGX_NIFTY","gift nifty":"GIFT_NIFTY","global cues":"GLOBAL",
    "dollar index":"DXY","dxy":"DXY","us market":"US_MKT",
    "sideways":"SIDEWAYS","rangebound":"RANGEBOUND","trending":"TRENDING",
    "overbought":"OVERBOUGHT","oversold":"OVERSOLD","volatile":"VOLATILE",
    "fib 61":"FIB_61","fibonacci":"FIB","fib":"FIB",
    "mean reversion":"MEAN_REV","z score":"ZSCORE",
    "hammer":"HAMMER","doji":"DOJI","engulfing":"ENGULF","pin bar":"PIN_BAR",
    "earnings":"EARNINGS","budget":"BUDGET","rbi policy":"RBI","fed meeting":"FED",
}
EXIT_CONDS={
    "stop loss":"STOPLOSS","sl":"STOPLOSS","stoploss":"STOPLOSS",
    "target":"TARGET","tp":"TARGET","take profit":"TARGET",
    "trailing stop":"TRAIL_SL","trailing sl":"TRAIL_SL",
    "break even":"BREAKEVEN","partial exit":"PART_EXIT",
    "eod exit":"EOD_EXIT","time stop":"TIME_SL",
    "50% premium":"HALF_PREM","premium stop":"PREM_SL",
    "daily stop":"DAILY_STOP","3 loss stop":"LOSS_3",
    "nikal lo":"EXIT_NOW","bahar niklo":"EXIT_NOW",
}
STRIKE_SEL={
    "deep itm":"DEEP_ITM","deep otm":"DEEP_OTM",
    "at the money":"ATM","atm":"ATM",
    "out of the money":"OTM","otm":"OTM",
    "in the money":"ITM","itm":"ITM",
    "3 strike otm":"OTM_3","2 strike otm":"OTM_2","1 strike otm":"OTM_1",
    "2 strike itm":"ITM_2","1 strike itm":"ITM_1",
    "50 delta":"D50","25 delta":"D25","16 delta":"D16","10 delta":"D10",
    "equidistant":"EQUIDIST","symmetric":"SYMMETRIC",
}
TIME_MAP={
    "pre market":"09:00","market open":"09:15","opening":"09:15",
    "morning":"09:20","subah":"09:20","सुबह":"09:20",
    "mid day":"12:00","noon":"12:00","dopahar":"12:00",
    "closing":"15:15","market close":"15:15","shaam":"15:00","शाम":"15:00",
    "eod":"15:20","expiry time":"15:25","orb":"09:30",
}
EXPIRY_MAP={
    "next week":"NEXT_WEEKLY","this week":"WEEKLY","weekly expiry":"WEEKLY","weekly":"WEEKLY","week":"WEEKLY",
    "next month":"NEXT_MONTHLY","this month":"MONTHLY","monthly":"MONTHLY","month":"MONTHLY",
    "quarterly":"QUARTERLY","is hafte":"WEEKLY","mahina":"MONTHLY",
}
RISK_CONDS={
    "1% risk":"RISK_1PCT","2% risk":"RISK_2PCT","percent risk":"PCT_RISK",
    "kelly criterion":"KELLY","half kelly":"HALF_KELLY","atr sizing":"ATR_SIZE",
    "fixed fractional":"FIXED_FRAC","volatility sizing":"VOL_SIZE",
    "atr stop":"ATR_SL","swing stop":"SWING_SL","chandelier stop":"CHAND_SL",
    "trailing stop":"TRAIL_SL","structure stop":"STRUCT_SL",
    "1r":"R1","2r":"R2","3r":"R3","5r":"R5",
    "fibonacci target":"FIB_TGT","measured move target":"MM_TGT",
    "1:2":"RR_1_2","1:3":"RR_1_3","1:1":"RR_1_1","1:5":"RR_1_5",
    "max drawdown":"MAX_DD","daily drawdown":"DAILY_DD",
    "portfolio heat":"PORT_HEAT","correlation risk":"CORR_RISK",
    "daily loss limit":"DAILY_LOSS","weekly loss limit":"WEEK_LOSS",
    "3 loss stop":"LOSS_3_STOP","drawdown pause":"DD_PAUSE",
    "delta hedge":"DELTA_HDG","tail hedge":"TAIL_HDG","vix hedge":"VIX_HDG",
    "max premium risk":"MAX_PREM","gamma risk":"GAMMA_RISK","pin risk":"PIN_RISK",
    "sharpe ratio":"SHARPE","profit factor":"PROFIT_FACTOR",
}

def extract_instr(t):
    for k,v in sorted(INSTRUMENTS.items(),key=lambda x:-len(x[0])):
        if k in t: return v
    return "NIFTY"

def extract_action(t):
    s=sum(1 for w in SELL_WORDS if w in t)
    b=sum(1 for w in BUY_WORDS if w in t)
    return "SELL" if s>b else "BUY"

def extract_nums(t):
    nums=re.findall(r'\b(\d{4,6})\b',t)
    if not nums: return None
    return [int(x) for x in nums] if len(nums)>1 else int(nums[0])

def extract_from(d, t):
    found={}
    for k,v in sorted(d.items(),key=lambda x:-len(x[0])):
        if k in t:
            p=rf'{re.escape(k)}\s*([<>=!]+)?\s*(\d+\.?\d*)?'
            m=re.search(p,t)
            if m and m.group(2):
                found[v]={"op":m.group(1) or "=","val":float(m.group(2))}
            else:
                found[v]=True
    return found if found else None

def extract_sl_tgt(t):
    r={}
    sl=re.search(r'(?:sl|stop loss|stoploss)\s*[=:@]?\s*(\d+)',t)
    tgt=re.search(r'(?:target|tp|take profit)\s*[=:@]?\s*(\d+)',t)
    trail=re.search(r'trailing\s*(?:sl|stop)?\s*[=:@]?\s*(\d+)',t)
    rr=re.search(r'(?:rr|risk reward)\s*[=:@]?\s*(\d+)[:/](\d+)',t)
    if sl: r["stoploss_points"]=int(sl.group(1)); r["stoploss_rupees"]=int(sl.group(1))*50
    if tgt: r["target_points"]=int(tgt.group(1)); r["target_rupees"]=int(tgt.group(1))*50
    if sl and tgt:
        sp,tp=int(sl.group(1)),int(tgt.group(1))
        r["risk_reward"]=f"1:{round(tp/sp,1)}"
        r["breakeven_trades_needed"]=round(sp/(sp+tp)*100,1)
    if trail: r["trailing_sl"]=int(trail.group(1))
    if rr: r["risk_reward"]=f"{rr.group(1)}:{rr.group(2)}"
    return r if r else None

def detect_lang(t):
    if len(re.findall(r'[\u0900-\u097F]',t))>3: return "HINDI"
    if any(w in t for w in ["kharido","becho","lo","niklo","subah","shaam","lagao","karo"]): return "HINGLISH"
    return "ENGLISH"

def calc_conf(r):
    s=0.65
    s+=0.05 if r.get("option_type") else 0
    s+=0.05 if r.get("strategy") else 0
    s+=0.03 if r.get("strike") else 0
    s+=0.03 if r.get("strike_selection") else 0
    s+=0.04 if r.get("conditions") else 0
    s+=0.03 if r.get("exit") else 0
    s+=0.03 if r.get("risk_management") else 0
    s+=0.02 if r.get("risk_metrics") else 0
    s+=0.02 if r.get("time") else 0
    return min(round(s,2),0.99)

# ═══════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════
class StrategyPayload(BaseModel):
    text: str

class TradePayload(BaseModel):
    instrument: str = "NIFTY"
    action: str = "BUY"
    option_type: Optional[str] = "CE"
    strike: Optional[int] = None
    expiry: str = "WEEKLY"
    quantity: int = 1
    entry_price: float = 100.0
    strategy: Optional[str] = None
    confidence: float = 0.92
    risk_metrics: Optional[dict] = None

class ClosePayload(BaseModel):
    position_id: str
    exit_price: float
    reason: str = "MANUAL"

class RiskCalcPayload(BaseModel):
    method: str = "FIXED_FRACTIONAL"
    sl_points: float = 100
    lot_size: int = 50
    win_rate: float = 0.5
    avg_win: float = 200
    avg_loss: float = 100
    atr: float = 100

# ═══════════════════════════════════════
# API ROUTES
# ═══════════════════════════════════════
@app.get("/")
def root():
    return {"status":"running","version":"12.3","modules":["nlp","paper_trading","risk_management"]}

@app.post("/strategy")
def parse_strategy(payload: StrategyPayload):
    raw=payload.text
    t=raw.lower().strip()
    qty_m=re.search(r'(\d+)\s*(?:lot|lots|लॉट)',t)
    qty=int(qty_m.group(1)) if qty_m else 1
    instr=extract_instr(t)
    action=extract_action(t)
    strike=extract_nums(t)
    opt_m={k:v for k,v in OPTION_TYPES.items() if re.search(r'\b'+re.escape(k)+r'\b',t)}
    opt=list(opt_m.values())[0] if opt_m else None
    strat=next((v for k,v in sorted(STRATEGIES.items(),key=lambda x:-len(x[0])) if k in t), None)
    conds=extract_from(CONDITIONS,t)
    exit_c=extract_from(EXIT_CONDS,t)
    risk_c=extract_from(RISK_CONDS,t)
    risk_m=extract_sl_tgt(t)
    strike_s=next((v for k,v in sorted(STRIKE_SEL.items(),key=lambda x:-len(x[0])) if k in t),None)
    exec_t=next((v for k,v in sorted(TIME_MAP.items(),key=lambda x:-len(x[0])) if k in t),None)
    expiry=next((v for k,v in sorted(EXPIRY_MAP.items(),key=lambda x:-len(x[0])) if k in t),"WEEKLY")
    lang=detect_lang(t)
    r={"instrument":instr,"action":action,"language":lang,"expiry":expiry,"quantity":qty}
    if opt: r["option_type"]=opt
    if strike: r["strike"]=strike
    if strike_s: r["strike_selection"]=strike_s
    if strat: r["strategy"]=strat
    if conds: r["conditions"]=conds
    if exit_c: r["exit"]=exit_c
    if risk_c: r["risk_management"]=risk_c
    if risk_m: r["risk_metrics"]=risk_m
    if exec_t: r["time"]=exec_t
    r["confidence"]=calc_conf(r)
    r["parsed_at"]=time.strftime("%H:%M:%S")
    return r

@app.post("/trade")
def execute_trade(payload: TradePayload):
    order=payload.dict()
    conf=order.get("confidence",0.92)

    # Risk check
    risk_check=risk_manager.check_trade(order)
    if not risk_check["allowed"]:
        return {"status":"REJECTED","reason":risk_check.get("reason","Risk limit"),"risk":risk_check}

    if conf<0.50:
        return {"status":"REJECTED","reason":"Low confidence","confidence":conf}

    # Execute paper trade
    result=paper_engine.open_position(order)

    if result["status"]=="EXECUTED":
        risk_manager.open_positions=len(paper_engine.positions)
        risk_manager.trades_today+=1

    return {**result, "confidence":conf, "mode":"PAPER"}

@app.post("/trade/close")
def close_trade(payload: ClosePayload):
    result=paper_engine.close_position(payload.position_id, payload.exit_price, payload.reason)
    if result["status"]=="CLOSED":
        risk_manager.open_positions=len(paper_engine.positions)
        risk_manager.daily_loss+=min(0, result["net_pnl"])
    return result

@app.get("/positions")
def get_positions():
    positions=[]
    for pos_id, pos in paper_engine.positions.items():
        p={"id":pos_id,"instrument":pos.instrument,"action":pos.action,
           "option_type":pos.option_type,"strike":pos.strike,
           "quantity":pos.quantity,"lot_size":pos.lot_size,
           "entry_price":pos.entry_price,"current_price":pos.current_price,
           "stoploss":pos.stoploss,"target":pos.target,
           "pnl":round(pos.pnl,0),"pnl_pct":pos.pnl_pct,
           "strategy":pos.strategy,"entry_time":pos.entry_time,"status":pos.status}
        positions.append(p)
    return {"positions":positions,"count":len(positions)}

@app.get("/trades")
def get_trades():
    trades=[{
        "id":t.id,"instrument":t.instrument,"action":t.action,
        "strike":t.strike,"quantity":t.quantity,"entry_price":t.entry_price,
        "exit_price":t.exit_price,"entry_time":t.entry_time,"exit_time":t.exit_time,
        "exit_reason":t.exit_reason,"strategy":t.strategy,
        "gross_pnl":round(t.pnl,0),"net_pnl":round(t.net_pnl,0),
        "pnl_pct":round(t.pnl_pct,2),"broker":t.broker
    } for t in paper_engine.trade_log]
    return {"trades":trades,"count":len(trades)}

@app.get("/stats")
def get_stats():
    stats=paper_engine.get_stats()
    risk=risk_manager.get_risk_report()
    return {"performance":stats,"risk":risk}

@app.post("/prices/update")
def update_prices(prices: dict):
    closed=paper_engine.update_prices(prices)
    return {"updated":True,"auto_closed":len(closed),"closed_positions":closed}

@app.post("/risk/calculate")
def calc_risk(payload: RiskCalcPayload):
    result=risk_manager.calculate_position_size(
        payload.method.upper(),
        sl_points=payload.sl_points, lot_size=payload.lot_size,
        win_rate=payload.win_rate, avg_win=payload.avg_win,
        avg_loss=payload.avg_loss, atr=payload.atr
    )
    return result

@app.get("/risk/calculator")
def risk_calc_get(sl: float=100, target: float=200, qty: int=1, lot_size: int=50, capital: float=500000):
    risk_amt=sl*qty*lot_size
    reward_amt=target*qty*lot_size
    rr=round(target/sl,2) if sl>0 else 0
    win_rate_needed=round(sl/(sl+target)*100,1)
    capital_risk_pct=round(risk_amt/capital*100,2)
    return {
        "stoploss_points":sl,"target_points":target,"lots":qty,"lot_size":lot_size,
        "risk_rupees":risk_amt,"reward_rupees":reward_amt,
        "risk_reward":f"1:{rr}","min_win_rate_needed":f"{win_rate_needed}%",
        "capital_at_risk_pct":f"{capital_risk_pct}%",
        "expectancy":round((0.5*reward_amt)-(0.5*risk_amt),0),
    }

@app.get("/risk/report")
def risk_report():
    return risk_manager.get_risk_report()

@app.post("/risk/kill_switch")
def kill_switch(active: bool = True):
    risk_manager.kill_switch=active
    return {"kill_switch":active,"message":"TRADING HALTED" if active else "TRADING RESUMED"}

@app.post("/paper/reset")
def reset_paper(capital: float=500000):
    global paper_engine
    paper_engine=PaperTradingEngine(capital=capital)
    return {"status":"reset","capital":capital}

@app.get("/capabilities")
def caps():
    return {
        "version":"12.3","nlp_conditions":len(CONDITIONS)+len(RISK_CONDS),
        "strategies":len(STRATEGIES),"modules":["nlp","paper_engine","risk_manager"],
        "examples":[
            "buy nifty atm call if rsi < 30 stop loss 100 target 300",
            "sell banknifty iron condor if vix > 15 and sideways weekly",
            "kharido nifty 50 lots if ema crossover subah trailing sl 50",
            "बेचो बैंकनिफ्टी पुट if order block resistance 1:3 rr",
        ]
    }
