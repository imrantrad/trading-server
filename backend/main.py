from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re, time

app = FastAPI(title="Institutional Trading NLP v12.3")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ═══════════════════════════════════════════════════════════
# INSTRUMENTS
# ═══════════════════════════════════════════════════════════
INSTRUMENTS = {
    "nifty 50":"NIFTY","nifty50":"NIFTY","nifty":"NIFTY","nifti":"NIFTY","nf":"NIFTY","निफ्टी":"NIFTY",
    "bank nifty":"BANKNIFTY","banknifty":"BANKNIFTY","bnf":"BANKNIFTY","बैंकनिफ्टी":"BANKNIFTY",
    "fin nifty":"FINNIFTY","finnifty":"FINNIFTY","fn":"FINNIFTY","फिन निफ्टी":"FINNIFTY",
    "midcap nifty":"MIDCPNIFTY","midcap":"MIDCPNIFTY","mid":"MIDCPNIFTY",
    "sensex":"SENSEX","सेंसेक्स":"SENSEX",
    "reliance":"RELIANCE","tcs":"TCS","hdfc":"HDFCBANK","infosys":"INFY",
    "icici":"ICICIBANK","sbi":"SBIN","tatasteel":"TATASTEEL",
    "usdinr":"USDINR","dollar":"USDINR","crude":"CRUDEOIL",
    "gold":"GOLD","silver":"SILVER","copper":"COPPER",
}

BUY_WORDS = ["buy","long","bullish","call buy","entry","enter","go long","accumulate",
    "kharido","le lo","lelo","lo","खरीदो","खरीद","लेना","ले लो","badhega","upar"]
SELL_WORDS = ["sell","short","bearish","put buy","exit","close","square off","squareoff",
    "book profit","reduce","becho","bech","niklo","nikal","बेचो","बेच","निकलो","girega","neeche"]

OPTION_TYPES = {"call":"CE","ce":"CE","कॉल":"CE","put":"PE","pe":"PE","पुट":"PE"}

# ═══════════════════════════════════════════════════════════
# STRATEGIES
# ═══════════════════════════════════════════════════════════
STRATEGIES = {
    "straddle":"STRADDLE","atm straddle":"ATM_STRADDLE","short straddle":"SHORT_STRADDLE",
    "long straddle":"LONG_STRADDLE","strangle":"STRANGLE","short strangle":"SHORT_STRANGLE",
    "long strangle":"LONG_STRANGLE","otm strangle":"OTM_STRANGLE",
    "covered call":"COVERED_CALL","protective put":"PROTECTIVE_PUT",
    "naked call":"NAKED_CALL","naked put":"NAKED_PUT","cash secured put":"CSP",
    "bull call spread":"BULL_CALL_SPREAD","bear call spread":"BEAR_CALL_SPREAD",
    "bull put spread":"BULL_PUT_SPREAD","bear put spread":"BEAR_PUT_SPREAD",
    "calendar spread":"CALENDAR_SPREAD","diagonal spread":"DIAGONAL_SPREAD",
    "ratio spread":"RATIO_SPREAD","back spread":"BACK_SPREAD",
    "debit spread":"DEBIT_SPREAD","credit spread":"CREDIT_SPREAD",
    "iron condor":"IRON_CONDOR","iron butterfly":"IRON_BUTTERFLY",
    "broken wing butterfly":"BWB","bwb":"BWB","butterfly":"BUTTERFLY",
    "condor":"CONDOR","jade lizard":"JADE_LIZARD",
    "double diagonal":"DOUBLE_DIAGONAL","christmas tree":"CHRISTMAS_TREE",
    "collar":"COLLAR","risk reversal":"RISK_REVERSAL",
    "ratio write":"RATIO_WRITE","synthetic long":"SYNTH_LONG",
    "synthetic short":"SYNTH_SHORT","synthetic future":"SYNTH_FUT",
    "delta hedge":"DELTA_HEDGE","gamma scalp":"GAMMA_SCALP",
    "vega trade":"VEGA_TRADE","theta harvest":"THETA_HARVEST",
    "dispersion trade":"DISPERSION","volatility arbitrage":"VOL_ARB",
}

# ═══════════════════════════════════════════════════════════
# INSTITUTIONAL CONDITIONS
# ═══════════════════════════════════════════════════════════
ALL_CONDITIONS = {

    # ── MOMENTUM ──────────────────────────────────────────
    "rsi":"RSI","rsi oversold":"RSI_OVERSOLD","rsi overbought":"RSI_OVERBOUGHT",
    "rsi divergence":"RSI_DIV","rsi crossover":"RSI_CROSS","rsi 30":"RSI_30",
    "rsi 70":"RSI_70","rsi 50":"RSI_50","rsi trend":"RSI_TREND",
    "macd":"MACD","macd crossover":"MACD_CROSS","macd bullish":"MACD_BULL",
    "macd bearish":"MACD_BEAR","macd histogram":"MACD_HIST","macd zero cross":"MACD_ZERO",
    "macd divergence":"MACD_DIV","macd signal":"MACD_SIG",
    "stochastic":"STOCH","stoch crossover":"STOCH_CROSS","stoch oversold":"STOCH_OS",
    "stoch overbought":"STOCH_OB","stochastic divergence":"STOCH_DIV",
    "cci":"CCI","williams r":"WILLIAMS_R","roc":"ROC","mfi":"MFI",
    "tsi":"TSI","ultimate oscillator":"ULT_OSC","awesome oscillator":"AO",

    # ── TREND ─────────────────────────────────────────────
    "ema":"EMA","ema crossover":"EMA_CROSS","ema200":"EMA200","ema50":"EMA50",
    "ema20":"EMA20","ema9":"EMA9","ema above":"EMA_ABOVE","ema below":"EMA_BELOW",
    "sma":"SMA","sma crossover":"SMA_CROSS","sma200":"SMA200","sma50":"SMA50",
    "wma":"WMA","hull moving average":"HMA","hma":"HMA","dema":"DEMA","tema":"TEMA",
    "golden cross":"GOLDEN_CROSS","death cross":"DEATH_CROSS",
    "supertrend":"SUPERTREND","supertrend buy":"ST_BUY","supertrend sell":"ST_SELL",
    "adx":"ADX","adx trending":"ADX_TREND","adx strong":"ADX_STRONG","dmi":"DMI",
    "parabolic sar":"PSAR","psar":"PSAR","ichimoku":"ICHIMOKU",
    "ichimoku cloud":"ICHI_CLOUD","kumo breakout":"KUMO_BO",
    "tenkan kijun cross":"TK_CROSS","chikou":"CHIKOU",
    "linear regression":"LIN_REG","least squares":"LSQ",
    "zigzag":"ZIGZAG","fractal":"FRACTAL",

    # ── VOLATILITY ────────────────────────────────────────
    "bollinger band":"BB","bollinger":"BB","bb squeeze":"BB_SQUEEZE",
    "bb breakout":"BB_BO","bb upper":"BB_UPPER","bb lower":"BB_LOWER",
    "bb width":"BB_WIDTH","bb percent":"BB_PCT",
    "atr":"ATR","atr breakout":"ATR_BO","keltner channel":"KELTNER",
    "keltner breakout":"KELT_BO","donchian channel":"DONCHIAN",
    "vix":"VIX","india vix":"VIX","vix spike":"VIX_SPIKE","vix crush":"VIX_CRUSH",
    "vix high":"VIX_HIGH","vix low":"VIX_LOW",
    "iv":"IV","implied volatility":"IV","iv rank":"IV_RANK",
    "iv percentile":"IV_PERC","iv crush":"IV_CRUSH","iv expansion":"IV_EXP",
    "hv":"HV","historical volatility":"HV","iv hv ratio":"IV_HV",
    "volatility smile":"VOL_SMILE","volatility skew":"VOL_SKEW",
    "volatility surface":"VOL_SURF","term structure":"TERM_STRUC",
    "contango":"CONTANGO","backwardation":"BACKWDTN",
    "realized volatility":"REAL_VOL","vol of vol":"VOL_VOL",
    "parkinson volatility":"PARK_VOL","garman klass":"GK_VOL",

    # ── VOLUME ────────────────────────────────────────────
    "vwap":"VWAP","vwap breakout":"VWAP_BO","vwap bounce":"VWAP_BNC",
    "vwap rejection":"VWAP_REJ","vwap reclaim":"VWAP_RCL",
    "obv":"OBV","obv divergence":"OBV_DIV","volume surge":"VOL_SURGE",
    "high volume":"HIGH_VOL","low volume":"LOW_VOL",
    "volume breakout":"VOL_BO","volume climax":"VOL_CLIMAX",
    "accumulation":"ACCUM","distribution":"DISTRIB",
    "volume profile":"VOL_PROFILE","poc":"POC","point of control":"POC",
    "value area high":"VAH","value area low":"VAL","value area":"VA",
    "hvn":"HVN","lvn":"LVN","high volume node":"HVN","low volume node":"LVN",
    "volume delta":"VOL_DELTA","buy volume":"BUY_VOL","sell volume":"SELL_VOL",
    "cvd":"CVD","cumulative volume delta":"CVD",

    # ── PRICE ACTION ──────────────────────────────────────
    "support":"SUPPORT","resistance":"RESISTANCE","key level":"KEY_LVL",
    "breakout":"BREAKOUT","breakdown":"BREAKDOWN","fakeout":"FAKEOUT",
    "reversal":"REVERSAL","bounce":"BOUNCE","rejection":"REJECTION",
    "higher high":"HH","lower low":"LL","higher low":"HL","lower high":"LH",
    "swing high":"SWING_H","swing low":"SWING_L",
    "double top":"DOUBLE_TOP","double bottom":"DOUBLE_BOTTOM",
    "triple top":"TRIPLE_TOP","triple bottom":"TRIPLE_BOTTOM",
    "head and shoulder":"HEAD_SHOULDER","inverse head shoulder":"INV_HS",
    "cup and handle":"CUP_HANDLE","rounding bottom":"ROUND_BTM",
    "flag":"FLAG","bull flag":"BULL_FLAG","bear flag":"BEAR_FLAG",
    "pennant":"PENNANT","wedge":"WEDGE","rising wedge":"RISE_WEDGE",
    "falling wedge":"FALL_WEDGE","ascending triangle":"ASC_TRI",
    "descending triangle":"DESC_TRI","symmetrical triangle":"SYM_TRI",
    "gap up":"GAP_UP","gap down":"GAP_DOWN","gap fill":"GAP_FILL",
    "island reversal":"ISLAND_REV","exhaustion gap":"EXHAUS_GAP",
    "measured move":"MEAS_MOVE","thrust":"THRUST",

    # ── CANDLESTICK ───────────────────────────────────────
    "doji":"DOJI","dragonfly doji":"DRAG_DOJI","gravestone doji":"GRAVE_DOJI",
    "hammer":"HAMMER","inverted hammer":"INV_HAMMER",
    "shooting star":"SHOOT_STAR","hanging man":"HANG_MAN",
    "engulfing":"ENGULF","bullish engulfing":"BULL_ENGULF",
    "bearish engulfing":"BEAR_ENGULF","harami":"HARAMI",
    "morning star":"MORN_STAR","evening star":"EVE_STAR",
    "three white soldiers":"THREE_WS","three black crows":"THREE_BC",
    "spinning top":"SPIN_TOP","marubozu":"MARUBOZU",
    "tweezer top":"TWEEZ_TOP","tweezer bottom":"TWEEZ_BTM",
    "dark cloud cover":"DARK_CLOUD","piercing line":"PIERC_LINE",
    "inside bar":"INSIDE_BAR","outside bar":"OUT_BAR","nr7":"NR7","nr4":"NR4",
    "pin bar":"PIN_BAR","fakey":"FAKEY",

    # ── FIBONACCI ─────────────────────────────────────────
    "fibonacci":"FIB","fib retracement":"FIB_RET","fib extension":"FIB_EXT",
    "fib 38":"FIB_38","fib 50":"FIB_50","fib 61":"FIB_61","fib 78":"FIB_78",
    "fib 127":"FIB_127","fib 161":"FIB_161","fib 261":"FIB_261",
    "golden ratio":"GOLDEN_RATIO","fib fan":"FIB_FAN","fib arc":"FIB_ARC",
    "fib time":"FIB_TIME","fib cluster":"FIB_CLUSTER",

    # ── SMART MONEY CONCEPTS ──────────────────────────────
    "order block":"ORDER_BLOCK","bullish order block":"BULL_OB",
    "bearish order block":"BEAR_OB","breaker block":"BREAKER",
    "mitigation block":"MITIG_BLK","rejection block":"REJ_BLK",
    "fair value gap":"FVG","fvg":"FVG","imbalance":"IMBALANCE",
    "liquidity":"LIQUIDITY","buy side liquidity":"BSL",
    "sell side liquidity":"SSL","liquidity sweep":"LIQ_SWEEP",
    "liquidity grab":"LIQ_GRAB","stop hunt":"STOP_HUNT",
    "inducement":"INDUCEMENT","change of character":"CHOCH",
    "choch":"CHOCH","break of structure":"BOS","bos":"BOS",
    "market structure shift":"MSS","premium zone":"PREMIUM",
    "discount zone":"DISCOUNT","equilibrium":"EQ","50% level":"EQ",
    "smart money":"SMART_MONEY","institutional buying":"INST_BUY",
    "institutional selling":"INST_SELL",

    # ── WYCKOFF ───────────────────────────────────────────
    "wyckoff":"WYCKOFF","accumulation phase":"ACCUM_PHASE",
    "distribution phase":"DISTRIB_PHASE","reaccumulation":"REACCUM",
    "redistribution":"REDISTRIB","spring":"SPRING","upthrust":"UPTHRUST",
    "selling climax":"SC","buying climax":"BC","automatic rally":"AR",
    "secondary test":"ST_WYCK","last point of support":"LPS",
    "last point of supply":"LPSY","sign of strength":"SOS",
    "sign of weakness":"SOW","cause and effect":"CAUSE_EFF",
    "composite man":"COMP_MAN",

    # ── ELLIOTT WAVE ──────────────────────────────────────
    "elliott wave":"ELLIOTT","wave 1":"WAVE1","wave 2":"WAVE2",
    "wave 3":"WAVE3","wave 4":"WAVE4","wave 5":"WAVE5",
    "wave a":"WAVE_A","wave b":"WAVE_B","wave c":"WAVE_C",
    "impulse wave":"IMPULSE","corrective wave":"CORRECTIVE",
    "zigzag correction":"ZZ_CORR","flat correction":"FLAT_CORR",
    "triangle correction":"TRI_CORR","wave count":"WAVE_CNT",
    "extended wave":"EXT_WAVE","truncation":"TRUNC",

    # ── OPTIONS SPECIFIC ──────────────────────────────────
    "open interest":"OI","oi buildup":"OI_BUILD","oi unwinding":"OI_UNWIND",
    "long buildup":"LONG_BUILD","short buildup":"SHORT_BUILD",
    "long unwinding":"LONG_UNWIND","short covering":"SHORT_COV",
    "pcr":"PCR","put call ratio":"PCR","pcr high":"PCR_HIGH",
    "pcr low":"PCR_LOW","pcr rising":"PCR_RISE","pcr falling":"PCR_FALL",
    "max pain":"MAX_PAIN","pain point":"MAX_PAIN",
    "gamma exposure":"GEX","positive gex":"POS_GEX","negative gex":"NEG_GEX",
    "dealer gamma":"DEALER_GAMMA","gamma flip":"GAMMA_FLIP",
    "theta decay":"THETA_DECAY","theta positive":"THETA_POS",
    "vanna":"VANNA","charm":"CHARM","speed":"SPEED","color":"COLOR",
    "delta neutral":"DELTA_NEUT","delta hedge":"DELTA_HDG",
    "gamma scalping":"GAMMA_SCALP","pin risk":"PIN_RISK",
    "options chain":"OPT_CHAIN","unusual activity":"UNUSUAL_ACT",
    "dark pool":"DARK_POOL","block trade":"BLOCK_TRADE",
    "sweep":"SWEEP","large order":"LARGE_ORDER",
    "call writing":"CALL_WRITE","put writing":"PUT_WRITE",
    "roll over":"ROLLOVER","rollover":"ROLLOVER",

    # ── MARKET MICROSTRUCTURE ─────────────────────────────
    "order flow":"ORDER_FLOW","tape reading":"TAPE_READ",
    "bid ask spread":"BID_ASK","market depth":"MKT_DEPTH",
    "level 2":"LEVEL2","dom":"DOM","depth of market":"DOM",
    "time and sales":"T_AND_S","tick data":"TICK_DATA",
    "absorption":"ABSORPTION","exhaustion":"EXHAUSTION",
    "aggressive buyer":"AGG_BUY","aggressive seller":"AGG_SELL",
    "market maker":"MKT_MAKER","spoofing":"SPOOFING",
    "iceberg order":"ICEBERG","hidden order":"HIDDEN_ORD",
    "footprint chart":"FOOTPRINT","delta divergence":"DELTA_DIV",
    "imbalance ratio":"IMBAL_RATIO",

    # ── INTERMARKET & MACRO ───────────────────────────────
    "fii buying":"FII_BUY","fii selling":"FII_SELL",
    "dii buying":"DII_BUY","dii selling":"DII_SELL",
    "fii data":"FII_DATA","dii data":"DII_DATA",
    "foreign inflow":"FOR_INFLOW","foreign outflow":"FOR_OUTFLOW",
    "dollar index":"DXY","dxy":"DXY","dollar strong":"DXY_STRONG",
    "dollar weak":"DXY_WEAK","usd strength":"USD_STR",
    "us market":"US_MKT","dow jones":"DOW","nasdaq":"NASDAQ",
    "sp500":"SP500","s&p":"SP500","sgx nifty":"SGX_NIFTY",
    "gift nifty":"GIFT_NIFTY","global cues":"GLOBAL_CUE",
    "asian market":"ASIAN_MKT","european market":"EUR_MKT",
    "crude oil":"CRUDE","brent":"BRENT","wti":"WTI",
    "gold price":"GOLD_PRICE","bond yield":"BOND_YIELD",
    "10 year yield":"YIELD_10Y","us yield":"US_YIELD",
    "rbi policy":"RBI","fed meeting":"FED","ecb":"ECB",
    "inflation":"INFLATION","cpi":"CPI","gdp":"GDP",
    "employment data":"EMPLOY","nonfarm payroll":"NFP",
    "earnings":"EARNINGS","results season":"RESULTS",
    "budget":"BUDGET","elections":"ELECTION",
    "geopolitical":"GEO_POL","risk on":"RISK_ON","risk off":"RISK_OFF",
    "correlation":"CORREL","beta":"BETA","sector rotation":"SECT_ROT",

    # ── STATISTICAL / QUANTITATIVE ────────────────────────
    "mean reversion":"MEAN_REV","momentum factor":"MOM_FACTOR",
    "z score":"ZSCORE","standard deviation":"STD_DEV",
    "regression":"REGRESSION","cointegration":"COINTEG",
    "pairs trade":"PAIRS","spread trade":"SPREAD_TRD",
    "statistical arbitrage":"STAT_ARB","market neutral":"MKT_NEUTRAL",
    "sharpe ratio":"SHARPE","sortino":"SORTINO","calmar":"CALMAR",
    "drawdown":"DRAWDOWN","max drawdown":"MAX_DD","var":"VAR",
    "value at risk":"VAR","expected shortfall":"ES",
    "monte carlo":"MONTE_CARLO","backtested":"BACKTEST",

    # ── MARKET REGIME ─────────────────────────────────────
    "trending market":"TRENDING","sideways market":"SIDEWAYS",
    "rangebound":"RANGEBOUND","range bound":"RANGEBOUND",
    "consolidating":"CONSOLIDATING","volatile market":"VOLATILE",
    "low volatility regime":"LOW_VOL_REG","high volatility":"HIGH_VOL",
    "bull market":"BULL_MKT","bear market":"BEAR_MKT",
    "accumulation zone":"ACCUM_ZONE","distribution zone":"DISTRIB_ZONE",
    "overbought":"OVERBOUGHT","oversold":"OVERSOLD",
    "euphoria":"EUPHORIA","panic":"PANIC","capitulation":"CAPITULATION",

    # ── RISK MANAGEMENT ───────────────────────────────────
    "stop loss":"STOPLOSS","sl":"STOPLOSS","stoploss":"STOPLOSS",
    "target":"TARGET","tp":"TARGET","take profit":"TARGET",
    "trailing stop":"TRAIL_SL","trailing sl":"TRAIL_SL",
    "break even":"BREAKEVEN","be":"BREAKEVEN",
    "max loss":"MAX_LOSS","max profit":"MAX_PROFIT",
    "daily loss limit":"DAILY_LOSS","weekly loss limit":"WEEK_LOSS",
    "position sizing":"POS_SIZE","kelly criterion":"KELLY",
    "risk reward":"RR","rr":"RR","1:2":"RR_1_2","1:3":"RR_1_3",
    "partial exit":"PART_EXIT","scale out":"SCALE_OUT",
    "scale in":"SCALE_IN","pyramid":"PYRAMID",
    "hedging":"HEDGE","portfolio hedge":"PORT_HEDGE",
    "correlation hedge":"CORR_HEDGE","tail risk":"TAIL_RISK",

    # ── TIME BASED ────────────────────────────────────────
    "first 15 min":"FIRST_15","opening range":"ORB",
    "orb breakout":"ORB_BO","opening range breakout":"ORB_BO",
    "power hour":"POWER_HOUR","last hour":"LAST_HOUR",
    "pre expiry":"PRE_EXPIRY","expiry day":"EXPIRY_DAY",
    "monthly expiry":"MONTH_EXP","weekly expiry":"WEEK_EXP",
    "rollover week":"ROLL_WEEK","settlement":"SETTLEMENT",
    "eod":"EOD","end of day":"EOD","intraday":"INTRADAY",
    "positional":"POSITIONAL","btst":"BTST","stbt":"STBT",
    "swing trade":"SWING","delivery":"DELIVERY",
}

# EXIT CONDITIONS
EXIT_CONDITIONS = {
    "stop loss":"STOPLOSS","sl":"STOPLOSS","target":"TARGET","tp":"TARGET",
    "trailing stop":"TRAIL_SL","trailing sl":"TRAIL_SL",
    "break even":"BREAKEVEN","partial exit":"PART_EXIT",
    "50% exit":"HALF_EXIT","half exit":"HALF_EXIT","scale out":"SCALE_OUT",
    "eod exit":"EOD_EXIT","time stop":"TIME_STOP",
    "reverse signal":"REV_SIG","signal reversal":"REV_SIG",
    "50% premium":"HALF_PREM","premium stop":"PREM_SL",
    "theta exit":"THETA_EXIT","delta exit":"DELTA_EXIT",
    "iv exit":"IV_EXIT","profit target":"PROFIT_TGT",
    "loss limit":"LOSS_LIM","daily stop":"DAILY_STOP",
    "nikal lo":"EXIT_NOW","profit book karo":"BOOK_PROFIT",
    "bahar niklo":"EXIT_NOW","बाहर":"EXIT_NOW","निकलो":"EXIT_NOW",
}

STRIKE_SELECTION = {
    "atm":"ATM","at the money":"ATM","itm":"ITM","in the money":"ITM",
    "otm":"OTM","out of the money":"OTM","deep itm":"DEEP_ITM","deep otm":"DEEP_OTM",
    "1 strike otm":"OTM_1","2 strike otm":"OTM_2","3 strike otm":"OTM_3",
    "1 strike itm":"ITM_1","2 strike itm":"ITM_2",
    "delta 50":"D50","50 delta":"D50","delta 25":"D25","25 delta":"D25",
    "delta 16":"D16","16 delta":"D16","delta 10":"D10","10 delta":"D10",
    "100 premium":"P100","200 premium":"P200","500 premium":"P500",
    "equidistant":"EQUIDIST","symmetric":"SYMMETRIC",
    "same strike":"SAME","next strike":"NEXT","previous strike":"PREV",
}

TIME_MAP = {
    "pre market":"09:00","market open":"09:15","opening":"09:15",
    "morning":"09:20","subah":"09:20","सुबह":"09:20",
    "first 15 minutes":"09:30","orb":"09:30",
    "mid day":"12:00","noon":"12:00","dopahar":"12:00","दोपहर":"12:00",
    "afternoon":"14:00","power hour":"14:00",
    "closing":"15:15","market close":"15:15","shaam":"15:00","शाम":"15:00",
    "eod":"15:20","expiry time":"15:25","last 30 min":"15:00",
}

EXPIRY_MAP = {
    "weekly":"WEEKLY","week":"WEEKLY","this week":"WEEKLY",
    "next week":"NEXT_WEEKLY","monthly":"MONTHLY","month":"MONTHLY",
    "this month":"MONTHLY","next month":"NEXT_MONTHLY",
    "current expiry":"CURRENT","near month":"NEAR_MONTH",
    "quarterly":"QUARTERLY","is hafte":"WEEKLY","mahina":"MONTHLY",
}

def extract_instrument(t):
    for k,v in sorted(INSTRUMENTS.items(),key=lambda x:-len(x[0])):
        if k in t: return v
    return "NIFTY"

def extract_action(t):
    s=sum(1 for w in SELL_WORDS if w in t)
    b=sum(1 for w in BUY_WORDS if w in t)
    return "SELL" if s>b else "BUY"

def extract_strike(t):
    nums=re.findall(r'\b(\d{4,6})\b',t)
    if not nums: return None
    return [int(x) for x in nums] if len(nums)>1 else int(nums[0])

def extract_option_type(t):
    for k,v in OPTION_TYPES.items():
        if re.search(r'\b'+re.escape(k)+r'\b',t): return v
    return None

def extract_strategy(t):
    for k,v in sorted(STRATEGIES.items(),key=lambda x:-len(x[0])):
        if k in t: return v
    return None

def extract_all_conditions(t):
    found={}
    for k,v in sorted(ALL_CONDITIONS.items(),key=lambda x:-len(x[0])):
        if k in t:
            p=rf'{re.escape(k)}\s*([<>=!]+)?\s*(\d+\.?\d*)?'
            m=re.search(p,t)
            if m and m.group(2):
                found[v]={"op":m.group(1) or "=","val":float(m.group(2))}
            else:
                found[v]=True
    return found if found else None

def extract_exit(t):
    found={}
    for k,v in sorted(EXIT_CONDITIONS.items(),key=lambda x:-len(x[0])):
        if k in t:
            m=re.search(rf'{re.escape(k)}\s*[=:@]?\s*(\d+\.?\d*)?',t)
            found[v]=float(m.group(1)) if m and m.group(1) else True
    sl=re.search(r'(?:sl|stop loss|stoploss)\s*[=:@]?\s*(\d+)',t)
    tgt=re.search(r'(?:target|tp)\s*[=:@]?\s*(\d+)',t)
    trail=re.search(r'trailing\s*(?:sl|stop)?\s*[=:@]?\s*(\d+)',t)
    rr=re.search(r'(?:rr|risk reward)\s*[=:@]?\s*(\d+)[:/](\d+)',t)
    if sl: found["STOPLOSS"]=int(sl.group(1))
    if tgt: found["TARGET"]=int(tgt.group(1))
    if trail: found["TRAIL_SL"]=int(trail.group(1))
    if rr: found["RR"]=f"{rr.group(1)}:{rr.group(2)}"
    return found if found else None

def extract_strike_sel(t):
    for k,v in sorted(STRIKE_SELECTION.items(),key=lambda x:-len(x[0])):
        if k in t: return v
    return None

def extract_time(t):
    for k,v in sorted(TIME_MAP.items(),key=lambda x:-len(x[0])):
        if k in t: return v
    m=re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b',t)
    if m:
        h,mn=int(m.group(1)),int(m.group(2))
        if m.group(3)=='pm' and h!=12: h+=12
        return f"{h:02d}:{mn:02d}"
    return None

def extract_qty(t):
    m=re.search(r'(\d+)\s*(?:lot|lots|लॉट)',t)
    return int(m.group(1)) if m else 1

def extract_expiry(t):
    for k,v in sorted(EXPIRY_MAP.items(),key=lambda x:-len(x[0])):
        if k in t: return v
    return "WEEKLY"

def detect_lang(t):
    if len(re.findall(r'[\u0900-\u097F]',t))>3: return "HINDI"
    if any(w in t for w in ["kharido","becho","lo","niklo","subah","shaam","lagao"]): return "HINGLISH"
    return "ENGLISH"

def calc_confidence(r):
    s=0.65
    s+=0.05 if r.get("instrument") else 0
    s+=0.05 if r.get("option_type") else 0
    s+=0.05 if r.get("strategy") else 0
    s+=0.04 if r.get("strike") else 0
    s+=0.03 if r.get("strike_selection") else 0
    s+=0.05 if r.get("conditions") else 0
    s+=0.04 if r.get("exit") else 0
    s+=0.02 if r.get("time") else 0
    return min(round(s,2),0.99)

@app.get("/")
def root():
    return {
        "status":"running","version":"12.3","nlp":"institutional_v4",
        "total_conditions":len(ALL_CONDITIONS),
        "categories":["momentum","trend","volatility","volume","price_action",
                      "candlestick","fibonacci","smart_money","wyckoff",
                      "elliott_wave","options","microstructure","intermarket",
                      "macro","statistical","regime","risk","time_based"]
    }

@app.post("/strategy")
def parse(payload: dict):
    raw=payload.get("text","")
    t=raw.lower().strip()
    instrument=extract_instrument(t)
    action=extract_action(t)
    strike=extract_strike(t)
    option_type=extract_option_type(t)
    strategy=extract_strategy(t)
    conditions=extract_all_conditions(t)
    exit=extract_exit(t)
    strike_sel=extract_strike_sel(t)
    exec_time=extract_time(t)
    qty=extract_qty(t)
    expiry=extract_expiry(t)
    lang=detect_lang(t)

    r={"instrument":instrument,"action":action,"language":lang,
       "expiry":expiry,"quantity":qty}
    if option_type: r["option_type"]=option_type
    if strike: r["strike"]=strike
    if strike_sel: r["strike_selection"]=strike_sel
    if strategy: r["strategy"]=strategy
    if conditions: r["conditions"]=conditions
    if exit: r["exit"]=exit
    if exec_time: r["time"]=exec_time
    r["confidence"]=calc_confidence(r)
    r["parsed_at"]=time.strftime("%H:%M:%S")
    return r

@app.post("/trade")
def trade(s: dict):
    c=s.get("confidence",0)
    if c<0.50: return {"status":"REJECTED","reason":"Low confidence","confidence":c}
    if c<0.70: return {"status":"REVIEW","reason":"Manual review needed","confidence":c}
    return {"status":"EXECUTED","result":s,
            "order_id":f"ORD{int(time.time()*1000)%1000000:06d}",
            "executed_at":time.strftime("%H:%M:%S")}

@app.get("/capabilities")
def caps():
    return {
        "total_conditions":len(ALL_CONDITIONS),
        "total_strategies":len(STRATEGIES),
        "categories":{
            "momentum":["RSI","MACD","Stochastic","CCI","Williams_R","MFI","AO"],
            "trend":["EMA","SMA","Supertrend","ADX","Ichimoku","Golden_Cross"],
            "volatility":["Bollinger","ATR","VIX","IV_Rank","Vol_Skew","Term_Structure"],
            "volume":["VWAP","OBV","Volume_Profile","POC","CVD","Footprint"],
            "price_action":["Support","Resistance","Breakout","SMC","Order_Block","FVG"],
            "candlestick":["Doji","Hammer","Engulfing","Morning_Star","Pin_Bar"],
            "fibonacci":["Retracement","Extension","FIB_61","FIB_161"],
            "smart_money":["Order_Block","FVG","BOS","CHOCH","Liquidity_Sweep"],
            "wyckoff":["Accumulation","Distribution","Spring","Upthrust"],
            "elliott_wave":["Wave_1_5","Impulse","Corrective","ABC"],
            "options":["OI","PCR","GEX","IV_Crush","Dark_Pool","Unusual_Activity"],
            "microstructure":["Order_Flow","Tape_Reading","DOM","CVD","Absorption"],
            "intermarket":["FII_DII","DXY","SGX_Nifty","Crude","Bond_Yield"],
            "macro":["RBI","Fed","Earnings","Budget","Geopolitical"],
            "statistical":["Mean_Reversion","Z_Score","Cointegration","Pairs_Trade"],
            "regime":["Trending","Sideways","Bull_Market","Bear_Market","Volatile"],
        },
        "examples":[
            "buy nifty atm straddle if vix > 15 and iv rank > 50",
            "sell banknifty iron condor if rangebound and theta positive",
            "buy nifty 22500 call if fii buying and ema crossover breakout",
            "short banknifty if order block resistance and overbought",
            "buy nifty if wyckoff spring and volume surge stop loss 100",
            "sell nifty if dark pool activity and unusual put buying",
            "buy if golden cross and fii inflow and gift nifty positive",
            "iron condor nifty if vix crush and iv rank < 30 weekly",
            "kharido banknifty if oi buildup and pcr bullish subah",
            "बेचो निफ्टी if head and shoulder and volume distribution",
        ]
    }
