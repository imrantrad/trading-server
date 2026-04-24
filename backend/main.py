"""
Trading System v12.3 - Complete Backend
FastAPI + Event Bus + Paper Engine + Risk Manager + Full NLP + Hedge NLP
"""
import sys, os, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

try:
    from events.event_bus import bus, Event, EventType
    from events.market_events import market_handler
    from events.signal_events import signal_handler
    from events.order_events import order_handler
    from events.risk_events import risk_event_handler
    from paper.paper_engine import PaperTradingEngine
    from risk.risk_manager import RiskManager, RiskParams
    from nlp.hedge_nlp import parse_hedge
    EVENT_DRIVEN = True
except Exception as e:
    print(f"Event system: {e}")
    EVENT_DRIVEN = False

app = FastAPI(title="Trading System v12.3 - Event-Driven")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

paper_engine = PaperTradingEngine(capital=500000)
risk_manager = RiskManager()

# ── System log (event-driven) ────────────────────────────
system_log = []

def log_handler(event: Event):
    system_log.append({
        "time": event.timestamp,
        "type": event.data.get("type", "INFO"),
        "msg": event.data.get("msg", ""),
        "source": event.source,
    })
    if len(system_log) > 500:
        system_log.pop(0)

if EVENT_DRIVEN:
    bus.subscribe(EventType.LOG, log_handler)
    bus.emit(EventType.SYSTEM_START, {"msg": "Trading System v12.3 started"}, source="MAIN")

# ═══════════════════════════════════════
# NLP DATA
# ═══════════════════════════════════════
INSTRUMENTS={"nifty 50":"NIFTY","nifty50":"NIFTY","nifty":"NIFTY","nf":"NIFTY","निफ्टी":"NIFTY",
    "bank nifty":"BANKNIFTY","banknifty":"BANKNIFTY","bnf":"BANKNIFTY","बैंकनिफ्टी":"BANKNIFTY",
    "fin nifty":"FINNIFTY","finnifty":"FINNIFTY","fn":"FINNIFTY",
    "midcap nifty":"MIDCPNIFTY","midcap":"MIDCPNIFTY",
    "sensex":"SENSEX","सेंसेक्स":"SENSEX",
    "reliance":"RELIANCE","tcs":"TCS","hdfc":"HDFCBANK","infosys":"INFY","icici":"ICICIBANK",
    "usdinr":"USDINR","crude":"CRUDEOIL","gold":"GOLD",
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
    "volatility arbitrage":"VOL_ARB","dispersion trade":"DISPERSION",
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
    "support":"SUPPORT","resistance":"RESISTANCE","gap up":"GAP_UP","gap down":"GAP_DOWN",
    "order block":"ORDER_BLOCK","fair value gap":"FVG","fvg":"FVG",
    "change of character":"CHOCH","choch":"CHOCH","break of structure":"BOS","bos":"BOS",
    "liquidity sweep":"LIQ_SWEEP","stop hunt":"STOP_HUNT",
    "wyckoff spring":"SPRING","wyckoff upthrust":"UPTHRUST","wyckoff":"WYCKOFF",
    "oi buildup":"OI_BUILD","oi unwinding":"OI_UNWIND","open interest":"OI",
    "pcr high":"PCR_HIGH","pcr low":"PCR_LOW","pcr":"PCR",
    "gamma exposure":"GEX","gamma flip":"GAMMA_FLIP","max pain":"MAX_PAIN",
    "dark pool":"DARK_POOL","unusual activity":"UNUSUAL_ACT","block trade":"BLOCK",
    "fii buying":"FII_BUY","fii selling":"FII_SELL","dii buying":"DII_BUY","dii selling":"DII_SELL",
    "sgx nifty":"SGX_NIFTY","gift nifty":"GIFT_NIFTY","global cues":"GLOBAL",
    "dollar index":"DXY","dxy":"DXY","us market":"US_MKT",
    "sideways":"SIDEWAYS","rangebound":"RANGEBOUND","trending":"TRENDING",
    "overbought":"OVERBOUGHT","oversold":"OVERSOLD","volatile":"VOLATILE",
    "fib 61":"FIB_61","fibonacci":"FIB","mean reversion":"MEAN_REV",
    "hammer":"HAMMER","doji":"DOJI","engulfing":"ENGULF","pin bar":"PIN_BAR",
    "earnings":"EARNINGS","budget":"BUDGET","rbi policy":"RBI","fed meeting":"FED",
    "circuit breaker":"CIRCUIT","upper circuit":"UPPER_CKT","lower circuit":"LOWER_CKT",
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
    "at the money":"ATM","atm":"ATM","out of the money":"OTM","otm":"OTM","in the money":"ITM","itm":"ITM",
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
    "eod":"15:20","expiry time":"15:25","orb":"09:30","power hour":"14:00",
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
    "1:2":"RR_1_2","1:3":"RR_1_3","1:1":"RR_1_1","1:5":"RR_1_5",
    "max drawdown":"MAX_DD","daily drawdown":"DAILY_DD","portfolio heat":"PORT_HEAT",
    "daily loss limit":"DAILY_LOSS","3 loss stop":"LOSS_3_STOP","drawdown pause":"DD_PAUSE",
    "delta hedge":"DELTA_HDG","tail hedge":"TAIL_HDG","vix hedge":"VIX_HDG",
    "gamma risk":"GAMMA_RISK","pin risk":"PIN_RISK","sharpe ratio":"SHARPE",
}

# Helpers
def ei(t):
    for k,v in sorted(INSTRUMENTS.items(),key=lambda x:-len(x[0])):
        if k in t: return v
    return "NIFTY"
def ea(t):
    s=sum(1 for w in SELL_WORDS if w in t); b=sum(1 for w in BUY_WORDS if w in t)
    return "SELL" if s>b else "BUY"
def en(t):
    n=re.findall(r'\b(\d{4,6})\b',t)
    return [int(x) for x in n] if len(n)>1 else (int(n[0]) if n else None)
def ef(d,t):
    f={}
    for k,v in sorted(d.items(),key=lambda x:-len(x[0])):
        if k in t:
            m=re.search(rf'{re.escape(k)}\s*([<>=!]+)?\s*(\d+\.?\d*)?',t)
            f[v]={"op":m.group(1) or "=","val":float(m.group(2))} if m and m.group(2) else True
    return f or None
def esl(t):
    r={}
    sl=re.search(r'(?:sl|stop loss|stoploss)\s*[=:@]?\s*(\d+)',t)
    tg=re.search(r'(?:target|tp)\s*[=:@]?\s*(\d+)',t)
    tr=re.search(r'trailing\s*(?:sl|stop)?\s*[=:@]?\s*(\d+)',t)
    rr=re.search(r'(?:rr)\s*[=:@]?\s*(\d+)[:/](\d+)',t)
    if sl: r["stoploss_points"]=int(sl.group(1))
    if tg: r["target_points"]=int(tg.group(1))
    if sl and tg: r["risk_reward"]=f"1:{round(int(tg.group(1))/int(sl.group(1)),1)}"
    if tr: r["trailing_sl"]=int(tr.group(1))
    if rr: r["risk_reward"]=f"{rr.group(1)}:{rr.group(2)}"
    return r or None
def dl(t):
    if len(re.findall(r'[\u0900-\u097F]',t))>3: return "HINDI"
    if any(w in t for w in ["kharido","becho","lo","niklo","subah","shaam","lagao","karo","bachao"]): return "HINGLISH"
    return "ENGLISH"
def cc(r):
    s=0.65
    for k,w in [("option_type",0.05),("strategy",0.05),("strike",0.03),("strike_selection",0.03),
                ("conditions",0.04),("exit",0.03),("risk_management",0.03),
                ("hedge",0.04),("risk_metrics",0.02),("time",0.02)]:
        if r.get(k): s+=w
    return min(round(s,2),0.99)

# ═══════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════
class StrategyPayload(BaseModel):
    text: str

class TradePayload(BaseModel):
    instrument: str="NIFTY"; action: str="BUY"; option_type: Optional[str]="CE"
    strike: Optional[int]=None; expiry: str="WEEKLY"; quantity: int=1
    entry_price: float=100.0; strategy: Optional[str]=None
    confidence: float=0.92; risk_metrics: Optional[dict]=None
    is_hedge: bool=False; hedge_strategy: Optional[str]=None

class ClosePayload(BaseModel):
    position_id: str; exit_price: float; reason: str="MANUAL"

class PriceUpdate(BaseModel):
    prices: Dict[str, float]

class RiskCalcPayload(BaseModel):
    method: str="FIXED_FRACTIONAL"; sl_points: float=100; lot_size: int=50
    win_rate: float=0.5; avg_win: float=200; avg_loss: float=100; atr: float=100

class HedgePayload(BaseModel):
    portfolio_value: float=500000; delta_exposure: float=0
    instrument: str="NIFTY"; hedge_type: str="PROTECTIVE_PUT"
    hedge_pct: float=100; trigger: Optional[str]=None

# ═══════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════
@app.get("/")
def root():
    return {"status":"running","version":"12.3",
            "modules":["nlp","hedge_nlp","paper_engine","risk_manager","event_bus"],
            "event_driven": EVENT_DRIVEN}

@app.post("/strategy")
def parse_strategy(payload: StrategyPayload):
    raw=payload.text; t=raw.lower().strip()
    qty_m=re.search(r'(\d+)\s*(?:lot|lots|लॉट)',t)
    qty=int(qty_m.group(1)) if qty_m else 1
    inst=ei(t); act=ea(t); strike=en(t)
    opt_m={k:v for k,v in OPTION_TYPES.items() if re.search(r'\b'+re.escape(k)+r'\b',t)}
    opt=list(opt_m.values())[0] if opt_m else None
    strat=next((v for k,v in sorted(STRATEGIES.items(),key=lambda x:-len(x[0])) if k in t),None)
    conds=ef(CONDITIONS,t); exit_c=ef(EXIT_CONDS,t)
    risk_c=ef(RISK_CONDS,t); risk_m=esl(t)
    ss=next((v for k,v in sorted(STRIKE_SEL.items(),key=lambda x:-len(x[0])) if k in t),None)
    et=next((v for k,v in sorted(TIME_MAP.items(),key=lambda x:-len(x[0])) if k in t),None)
    expiry=next((v for k,v in sorted(EXPIRY_MAP.items(),key=lambda x:-len(x[0])) if k in t),"WEEKLY")
    lang=dl(t)
    # Hedge detection
    hedge=parse_hedge(t) if "hedge" in t or "bachao" in t or "protect" in t else None

    r={"instrument":inst,"action":act,"language":lang,"expiry":expiry,"quantity":qty}
    if opt: r["option_type"]=opt
    if strike: r["strike"]=strike
    if ss: r["strike_selection"]=ss
    if strat: r["strategy"]=strat
    if conds: r["conditions"]=conds
    if exit_c: r["exit"]=exit_c
    if risk_c: r["risk_management"]=risk_c
    if risk_m: r["risk_metrics"]=risk_m
    if et: r["time"]=et
    if hedge: r["hedge"]=hedge
    r["confidence"]=cc(r)
    r["parsed_at"]=time.strftime("%H:%M:%S")

    if EVENT_DRIVEN:
        bus.emit(EventType.NLP_PARSED, r, source="NLP")
    return r

@app.post("/trade")
def execute_trade(payload: TradePayload):
    order=payload.dict()
    risk_check=risk_manager.check_trade(order)
    if not risk_check["allowed"]:
        if EVENT_DRIVEN:
            bus.emit(EventType.ORDER_REJECTED,{"reason":risk_check.get("reason")},source="RISK")
        return {"status":"REJECTED","reason":risk_check.get("reason","Risk limit")}
    if order.get("confidence",0.92)<0.50:
        return {"status":"REJECTED","reason":"Low confidence"}
    result=paper_engine.open_position(order)
    if result["status"]=="EXECUTED":
        risk_manager.open_positions=len(paper_engine.positions)
        risk_manager.trades_today+=1
        if EVENT_DRIVEN:
            bus.emit(EventType.POSITION_OPEN,{**order,**result},source="PAPER")
    return {**result,"confidence":order.get("confidence",0.92),"mode":"PAPER"}

@app.post("/trade/close")
def close_trade(payload: ClosePayload):
    result=paper_engine.close_position(payload.position_id,payload.exit_price,payload.reason)
    if result["status"]=="CLOSED":
        risk_manager.open_positions=len(paper_engine.positions)
        risk_manager.daily_loss+=min(0,result["net_pnl"])
        if EVENT_DRIVEN:
            bus.emit(EventType.POSITION_CLOSE,result,source="PAPER")
    return result

@app.get("/positions")
def get_positions():
    positions=[{"id":pid,"instrument":p.instrument,"action":p.action,
        "option_type":p.option_type,"strike":p.strike,"quantity":p.quantity,
        "lot_size":p.lot_size,"entry_price":p.entry_price,"current_price":p.current_price,
        "stoploss":p.stoploss,"target":p.target,"pnl":round(p.pnl,0),
        "pnl_pct":p.pnl_pct,"strategy":p.strategy,"entry_time":p.entry_time,"status":p.status}
        for pid,p in paper_engine.positions.items()]
    return {"positions":positions,"count":len(positions)}

@app.get("/trades")
def get_trades():
    return {"trades":[{"id":t.id,"instrument":t.instrument,"action":t.action,
        "strike":t.strike,"quantity":t.quantity,"entry_price":t.entry_price,
        "exit_price":t.exit_price,"entry_time":t.entry_time,"exit_time":t.exit_time,
        "exit_reason":t.exit_reason,"strategy":t.strategy,
        "gross_pnl":round(t.pnl,0),"net_pnl":round(t.net_pnl,0),
        "pnl_pct":round(t.pnl_pct,2),"broker":t.broker}
        for t in paper_engine.trade_log],"count":len(paper_engine.trade_log)}

@app.get("/stats")
def get_stats():
    return {"performance":paper_engine.get_stats(),"risk":risk_manager.get_risk_report()}

@app.post("/prices/update")
def update_prices(payload: PriceUpdate):
    closed=paper_engine.update_prices(payload.prices)
    if EVENT_DRIVEN:
        for inst,price in payload.prices.items():
            market_handler.publish_tick(inst,price)
    return {"updated":True,"auto_closed":len(closed)}

@app.post("/hedge/analyze")
def analyze_hedge(payload: HedgePayload):
    """Calculate hedge requirements"""
    inst=payload.instrument
    lot_size=LOT_SIZES.get(inst,50)
    lots_to_hedge=max(1,round(payload.portfolio_value*payload.hedge_pct/100/(20000*lot_size)))
    delta_hedge_lots=abs(payload.delta_exposure)/lot_size if payload.delta_exposure else 0
    return {
        "instrument":inst,"hedge_type":payload.hedge_type,
        "portfolio_value":payload.portfolio_value,
        "hedge_pct":payload.hedge_pct,
        "lots_required":lots_to_hedge,
        "delta_hedge_lots":round(delta_hedge_lots,1),
        "estimated_hedge_cost":lots_to_hedge*100*lot_size,
        "recommendation":{
            "strategy":"PROTECTIVE_PUT" if payload.delta_exposure>0 else "COVERED_CALL",
            "strike_selection":"OTM_1" if payload.hedge_pct<50 else "ATM",
            "expiry":"MONTHLY",
            "review_trigger":"VIX>15 or portfolio_loss>2%"
        }
    }

@app.post("/risk/calculate")
def calc_risk(payload: RiskCalcPayload):
    return risk_manager.calculate_position_size(
        payload.method.upper(),sl_points=payload.sl_points,lot_size=payload.lot_size,
        win_rate=payload.win_rate,avg_win=payload.avg_win,avg_loss=payload.avg_loss,atr=payload.atr)

@app.get("/risk/calculator")
def risk_calc(sl:float=100,target:float=200,qty:int=1,lot_size:int=50,capital:float=500000):
    ra=sl*qty*lot_size; rw=target*qty*lot_size
    return {"stoploss_points":sl,"target_points":target,"lots":qty,"lot_size":lot_size,
            "risk_rupees":ra,"reward_rupees":rw,"risk_reward":f"1:{round(target/sl,2)}",
            "min_win_rate_needed":f"{round(sl/(sl+target)*100,1)}%",
            "capital_at_risk_pct":f"{round(ra/capital*100,2)}%",
            "expectancy":round((0.5*rw)-(0.5*ra),0)}

@app.get("/risk/report")
def risk_report(): return risk_manager.get_risk_report()

@app.post("/risk/kill_switch")
def kill_switch(active:bool=True):
    risk_manager.kill_switch=active
    if EVENT_DRIVEN: bus.emit(EventType.KILL_SWITCH,{"reason":"Manual","active":active})
    return {"kill_switch":active}

@app.post("/paper/reset")
def reset_paper(capital:float=500000):
    global paper_engine; paper_engine=PaperTradingEngine(capital=capital)
    return {"status":"reset","capital":capital}

@app.get("/events/history")
def event_history(limit:int=50):
    if not EVENT_DRIVEN: return {"events":[],"event_driven":False}
    return {"events":bus.get_history(limit=limit),"stats":bus.get_stats()}

@app.get("/events/log")
def event_log(limit:int=100):
    return {"log":system_log[-limit:],"count":len(system_log)}

@app.post("/events/emit")
def emit_event(event_type:str, data:dict={}):
    if not EVENT_DRIVEN: return {"status":"Event bus not available"}
    bus.emit(getattr(EventType,event_type,EventType.LOG),data,source="API")
    return {"emitted":event_type,"data":data}

@app.get("/nlp/hedge/capabilities")
def hedge_caps():
    from nlp.hedge_nlp import HEDGE_STRATEGIES,HEDGE_TRIGGERS,HEDGE_INSTRUMENTS,HEDGE_SIZING
    return {
        "hedge_strategies":len(HEDGE_STRATEGIES),
        "hedge_triggers":len(HEDGE_TRIGGERS),
        "hedge_instruments":len(HEDGE_INSTRUMENTS),
        "hedge_sizing":len(HEDGE_SIZING),
        "examples":[
            "protective put hedge nifty if portfolio down 2%",
            "delta hedge banknifty if delta exceeds 50",
            "collar hedge nifty before earnings 50% hedge",
            "tail risk hedge if vix above 20 buy otm put",
            "hedge lagao before budget 25% hedge",
            "portfolio hedge nifty futures if fii selling",
            "iron condor hedge if iv rank high and sideways",
            "gamma hedge banknifty before expiry",
            "हेज लगाओ निफ्टी पुट if market falls",
        ]
    }

@app.get("/capabilities")
def caps():
    return {"version":"12.3","architecture":"EVENT_DRIVEN","event_driven":EVENT_DRIVEN,
        "modules":{"nlp":"500+ conditions","hedge_nlp":"100+ hedge strategies",
            "event_bus":"15+ event types","paper_engine":"Full simulation",
            "risk_manager":"Complete risk management"},
        "api_endpoints":["/strategy","/trade","/trade/close","/positions","/trades",
            "/stats","/prices/update","/hedge/analyze","/risk/calculate",
            "/risk/report","/risk/kill_switch","/events/history","/events/log","/paper/reset"]}

# ═══════════════════════════════════════
# NEW MODULES
# ═══════════════════════════════════════
try:
    from backtest.engine import BacktestEngine, backtest_engine
    from engine.strategy_engine import StrategyEngine, strategy_engine, BUILTIN_STRATEGIES, StrategyConfig
    from engine.notifications import NotificationEngine, notifier
    from engine.portfolio import PortfolioTracker, PortfolioPosition, portfolio
    from engine.options_chain import generate_chain
    from brokers import get_broker
    MODULES_LOADED = True
except Exception as e:
    MODULES_LOADED = False
    print(f"Modules: {e}")

# ─── BACKTEST ────────────────────────────────────────
class BacktestPayload(BaseModel):
    strategy: str = "EMA_CROSS"
    instrument: str = "NIFTY"
    bars: int = 252
    quantity: int = 1
    sl_pct: float = 1.0
    target_pct: float = 2.0
    run_monte_carlo: bool = True
    run_walk_forward: bool = True

@app.post("/backtest/run")
def run_backtest(payload: BacktestPayload):
    if not MODULES_LOADED:
        return {"error": "Backtest module not loaded"}
    candles = backtest_engine.generate_sample_data(payload.instrument, payload.bars)
    result = backtest_engine.run_strategy(
        payload.strategy, candles, payload.quantity, payload.sl_pct, payload.target_pct)
    response = {
        "strategy": result.strategy,
        "instrument": payload.instrument,
        "bars_tested": len(candles),
        "total_trades": result.total_trades,
        "winning_trades": result.winning_trades,
        "losing_trades": result.losing_trades,
        "win_rate": result.win_rate,
        "total_pnl": result.total_pnl,
        "profit_factor": result.profit_factor,
        "avg_win": result.avg_win,
        "avg_loss": result.avg_loss,
        "max_drawdown_pct": result.max_drawdown,
        "sharpe_ratio": result.sharpe_ratio,
        "expectancy": result.expectancy,
        "max_consecutive_wins": result.max_consecutive_wins,
        "max_consecutive_losses": result.max_consecutive_losses,
        "equity_curve": result.equity_curve,
        "verdict": "PROFITABLE" if result.total_pnl > 0 else "UNPROFITABLE",
    }
    if payload.run_monte_carlo:
        pnls = [t.pnl for t in result.trades]
        response["monte_carlo"] = backtest_engine.monte_carlo(pnls)
    if payload.run_walk_forward:
        response["walk_forward"] = backtest_engine.walk_forward(payload.strategy, candles)
    return response

@app.get("/backtest/strategies")
def backtest_strategies():
    return {"strategies": ["EMA_CROSS","RSI_MEAN_REVERSION","BOLLINGER_BREAKOUT",
                           "EMA_RSI_COMBO","SUPERTREND_LIKE"]}

# ─── STRATEGY ENGINE ────────────────────────────────
class StrategyPayloadNew(BaseModel):
    name: str; instrument: str = "NIFTY"; quantity: int = 1
    sl_pct: float = 1.0; target_pct: float = 2.0
    auto_execute: bool = False; mode: str = "PAPER"

@app.post("/strategy/add")
def add_strategy(payload: StrategyPayloadNew):
    if not MODULES_LOADED: return {"error": "Module not loaded"}
    config = StrategyConfig(name=payload.name, instrument=payload.instrument,
        quantity=payload.quantity, auto_execute=payload.auto_execute, mode=payload.mode)
    sid = strategy_engine.add_strategy(config)
    return {"status": "added", "strategy_id": sid}

@app.get("/strategy/list")
def list_strategies():
    if not MODULES_LOADED: return {"strategies": [], "builtin": BUILTIN_STRATEGIES}
    return {"active": strategy_engine.get_all_status(),
            "builtin": BUILTIN_STRATEGIES, "count": len(strategy_engine.strategies)}

@app.get("/strategy/signals")
def get_signals(limit: int = 20):
    if not MODULES_LOADED: return {"signals": []}
    return {"signals": strategy_engine.get_recent_signals(limit)}

@app.post("/strategy/{sid}/pause")
def pause_strategy(sid: str):
    if MODULES_LOADED: strategy_engine.pause_strategy(sid)
    return {"status": "paused", "id": sid}

@app.post("/strategy/{sid}/resume")
def resume_strategy(sid: str):
    if MODULES_LOADED: strategy_engine.resume_strategy(sid)
    return {"status": "resumed", "id": sid}

@app.post("/strategy/update_market")
def update_market(prices: dict, indicators: dict = {}):
    if MODULES_LOADED: strategy_engine.update_market_data(prices, indicators)
    return {"updated": True}

# ─── OPTIONS CHAIN ─────────────────────────────────
@app.get("/options/chain")
def options_chain(spot: float = 22450, dte: int = 7, iv: float = 15,
                  instrument: str = "NIFTY"):
    chain = generate_chain(spot, dte, iv/100)
    return chain

@app.get("/options/greeks")
def option_greeks(spot: float, strike: float, dte: int = 7,
                  iv: float = 15, opt_type: str = "CE"):
    from engine.options_chain import black_scholes
    result = black_scholes(spot, strike, dte, 0.065, iv/100, opt_type)
    intrinsic = max(0, spot-strike) if opt_type=="CE" else max(0, strike-spot)
    return {**result, "intrinsic_value": round(intrinsic, 2),
            "time_value": round(result["price"]-intrinsic, 2),
            "moneyness": "ATM" if abs(spot-strike)<25 else ("ITM" if
                (opt_type=="CE" and spot>strike) or (opt_type=="PE" and spot<strike) else "OTM")}

# ─── PORTFOLIO ──────────────────────────────────────
@app.get("/portfolio/summary")
def portfolio_summary():
    if not MODULES_LOADED: return {"error": "Module not loaded"}
    return portfolio.get_summary()

@app.get("/portfolio/positions")
def portfolio_positions():
    if not MODULES_LOADED: return {"positions": []}
    return {"positions": [
        {"id": pid, "instrument": p.instrument, "action": p.action,
         "option_type": p.option_type, "strike": p.strike,
         "quantity": p.quantity, "avg_price": p.avg_price,
         "current_price": p.current_price, "pnl": round(p.pnl, 0),
         "pnl_pct": p.pnl_pct, "is_hedge": p.is_hedge, "delta": p.delta}
        for pid, p in portfolio.positions.items()
    ]}

# ─── NOTIFICATIONS ──────────────────────────────────
class NotifConfig(BaseModel):
    telegram_token: str = ""; telegram_chat_id: str = ""; webhook_url: str = ""

@app.post("/notifications/configure")
def configure_notif(payload: NotifConfig):
    if not MODULES_LOADED: return {"error": "Module not loaded"}
    if payload.telegram_token:
        notifier.configure_telegram(payload.telegram_token, payload.telegram_chat_id)
    if payload.webhook_url:
        notifier.configure_webhook(payload.webhook_url)
    return {"telegram": notifier.enabled["telegram"], "webhook": notifier.enabled["webhook"]}

@app.get("/notifications/history")
def notif_history(limit: int = 20):
    if not MODULES_LOADED: return {"notifications": []}
    return {"notifications": notifier.get_recent(limit)}

@app.post("/notifications/test")
def test_notif():
    if not MODULES_LOADED: return {"error": "Module not loaded"}
    notifier.send(__import__('engine.notifications', fromlist=['Notification']).Notification(
        "SYSTEM","INFO","Test Notification","Trading System v12.3 is running!"))
    return {"sent": True}

# ─── BROKER STATUS ──────────────────────────────────
@app.get("/broker/status")
def broker_status():
    return {"active_broker": "ZERODHA", "mode": "PAPER",
            "brokers": ["ZERODHA","ANGEL","FYERS"],
            "note": "Add API keys in config/settings.py for live trading",
            "live_trading": False}

@app.get("/broker/connect/{broker_name}")
def connect_broker(broker_name: str, api_key: str = "", access_token: str = ""):
    if not MODULES_LOADED: return {"error": "Module not loaded"}
    try:
        broker = get_broker(broker_name, api_key=api_key, access_token=access_token)
        connected = broker.login()
        return {"broker": broker_name, "connected": connected,
                "note": "Add real API keys for live connection"}
    except Exception as e:
        return {"error": str(e)}

# ─── SYSTEM STATUS ──────────────────────────────────
@app.get("/system/status")
def system_status():
    stats = paper_engine.get_stats()
    return {
        "version": "12.3",
        "status": "RUNNING",
        "mode": "PAPER",
        "event_driven": EVENT_DRIVEN,
        "modules_loaded": MODULES_LOADED,
        "uptime": time.strftime("%H:%M:%S"),
        "performance": {
            "capital": stats.get("capital", 500000),
            "total_pnl": stats.get("total_pnl", 0),
            "total_trades": stats.get("total_trades", 0),
            "win_rate": stats.get("win_rate", 0),
        },
        "risk": risk_manager.get_risk_report(),
        "components": {
            "nlp": "ACTIVE", "paper_engine": "ACTIVE",
            "risk_manager": "ACTIVE", "event_bus": "ACTIVE" if EVENT_DRIVEN else "INACTIVE",
            "backtest": "ACTIVE" if MODULES_LOADED else "INACTIVE",
            "strategy_engine": "ACTIVE" if MODULES_LOADED else "INACTIVE",
            "options_chain": "ACTIVE" if MODULES_LOADED else "INACTIVE",
            "notifications": "CONFIGURED" if MODULES_LOADED and notifier.enabled.get("telegram") else "NOT_CONFIGURED",
            "brokers": "ZERODHA/ANGEL/FYERS (Paper Mode)",
        }
    }
