from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re, time, math

app = FastAPI(title="Institutional Trading System v12.3")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ═══════════════════════════════════════
# INSTRUMENTS
# ═══════════════════════════════════════
INSTRUMENTS = {
    "nifty 50":"NIFTY","nifty50":"NIFTY","nifty":"NIFTY","nifti":"NIFTY","nf":"NIFTY","निफ्टी":"NIFTY",
    "bank nifty":"BANKNIFTY","banknifty":"BANKNIFTY","bnf":"BANKNIFTY","बैंकनिफ्टी":"BANKNIFTY",
    "fin nifty":"FINNIFTY","finnifty":"FINNIFTY","fn":"FINNIFTY",
    "midcap nifty":"MIDCPNIFTY","midcap":"MIDCPNIFTY",
    "sensex":"SENSEX","सेंसेक्स":"SENSEX",
    "reliance":"RELIANCE","tcs":"TCS","hdfc":"HDFCBANK","infosys":"INFY","icici":"ICICIBANK","sbi":"SBIN",
    "usdinr":"USDINR","crude":"CRUDEOIL","gold":"GOLD","silver":"SILVER",
}

BUY_WORDS=["buy","long","bullish","call buy","entry","enter","accumulate","kharido","le lo","lelo","lo","खरीदो","खरीद","badhega","upar"]
SELL_WORDS=["sell","short","bearish","put buy","exit","close","square off","squareoff","book profit","becho","bech","niklo","nikal","बेचो","बेच","girega","neeche"]
OPTION_TYPES={"call":"CE","ce":"CE","कॉल":"CE","put":"PE","pe":"PE","पुट":"PE"}

STRATEGIES={
    "short straddle":"SHORT_STRADDLE","long straddle":"LONG_STRADDLE","atm straddle":"ATM_STRADDLE","straddle":"STRADDLE",
    "short strangle":"SHORT_STRANGLE","long strangle":"LONG_STRANGLE","otm strangle":"OTM_STRANGLE","strangle":"STRANGLE",
    "covered call":"COVERED_CALL","protective put":"PROTECTIVE_PUT","cash secured put":"CSP",
    "naked call":"NAKED_CALL","naked put":"NAKED_PUT",
    "bull call spread":"BULL_CALL_SPREAD","bear call spread":"BEAR_CALL_SPREAD",
    "bull put spread":"BULL_PUT_SPREAD","bear put spread":"BEAR_PUT_SPREAD",
    "calendar spread":"CALENDAR_SPREAD","diagonal spread":"DIAGONAL_SPREAD",
    "ratio spread":"RATIO_SPREAD","back spread":"BACK_SPREAD",
    "debit spread":"DEBIT_SPREAD","credit spread":"CREDIT_SPREAD",
    "iron condor":"IRON_CONDOR","iron butterfly":"IRON_BUTTERFLY",
    "broken wing butterfly":"BWB","bwb":"BWB","butterfly":"BUTTERFLY","condor":"CONDOR",
    "jade lizard":"JADE_LIZARD","double diagonal":"DOUBLE_DIAGONAL",
    "collar":"COLLAR","risk reversal":"RISK_REVERSAL",
    "synthetic long":"SYNTH_LONG","synthetic short":"SYNTH_SHORT",
    "delta hedge":"DELTA_HEDGE","gamma scalp":"GAMMA_SCALP",
    "volatility arbitrage":"VOL_ARB","dispersion trade":"DISPERSION",
}

# ═══════════════════════════════════════
# ALL TRADING CONDITIONS (500+)
# ═══════════════════════════════════════
ALL_CONDITIONS = {
    # MOMENTUM
    "rsi oversold":"RSI_OS","rsi overbought":"RSI_OB","rsi divergence":"RSI_DIV",
    "rsi crossover":"RSI_CROSS","rsi":"RSI",
    "macd crossover":"MACD_CROSS","macd bullish":"MACD_BULL","macd bearish":"MACD_BEAR",
    "macd divergence":"MACD_DIV","macd histogram":"MACD_HIST","macd":"MACD",
    "stoch crossover":"STOCH_CROSS","stoch oversold":"STOCH_OS","stoch overbought":"STOCH_OB","stochastic":"STOCH",
    "cci":"CCI","williams r":"WILLIAMS_R","roc":"ROC","mfi":"MFI","awesome oscillator":"AO","tsi":"TSI",
    # TREND
    "ema crossover":"EMA_CROSS","ema200":"EMA200","ema50":"EMA50","ema20":"EMA20","ema9":"EMA9","ema":"EMA",
    "sma crossover":"SMA_CROSS","sma200":"SMA200","sma50":"SMA50","sma":"SMA",
    "hull moving average":"HMA","hma":"HMA","dema":"DEMA","tema":"TEMA","wma":"WMA",
    "golden cross":"GOLDEN_CROSS","death cross":"DEATH_CROSS",
    "supertrend buy":"ST_BUY","supertrend sell":"ST_SELL","supertrend":"SUPERTREND",
    "adx trending":"ADX_TREND","adx strong":"ADX_STRONG","adx":"ADX","dmi":"DMI",
    "parabolic sar":"PSAR","psar":"PSAR",
    "ichimoku cloud":"ICHI_CLOUD","kumo breakout":"KUMO_BO","tenkan kijun cross":"TK_CROSS","ichimoku":"ICHIMOKU",
    "linear regression":"LIN_REG","zigzag":"ZIGZAG","fractal":"FRACTAL",
    # VOLATILITY
    "bb squeeze":"BB_SQUEEZE","bb breakout":"BB_BO","bb upper":"BB_UPPER","bb lower":"BB_LOWER","bb width":"BB_WIDTH","bollinger":"BB",
    "atr breakout":"ATR_BO","atr":"ATR","keltner breakout":"KELT_BO","keltner channel":"KELTNER","donchian channel":"DONCHIAN",
    "vix spike":"VIX_SPIKE","vix crush":"VIX_CRUSH","vix high":"VIX_HIGH","vix low":"VIX_LOW","india vix":"VIX","vix":"VIX",
    "iv rank":"IV_RANK","iv percentile":"IV_PERC","iv crush":"IV_CRUSH","iv expansion":"IV_EXP","implied volatility":"IV","iv":"IV",
    "volatility smile":"VOL_SMILE","volatility skew":"VOL_SKEW","volatility surface":"VOL_SURF",
    "term structure":"TERM_STRUC","contango":"CONTANGO","backwardation":"BACKWDTN",
    "realized volatility":"REAL_VOL","historical volatility":"HV","hv":"HV","vol of vol":"VOL_VOL",
    # VOLUME
    "vwap breakout":"VWAP_BO","vwap bounce":"VWAP_BNC","vwap rejection":"VWAP_REJ","vwap reclaim":"VWAP_RCL","vwap":"VWAP",
    "obv divergence":"OBV_DIV","obv":"OBV",
    "volume climax":"VOL_CLIMAX","volume breakout":"VOL_BO","volume surge":"VOL_SURGE",
    "high volume node":"HVN","low volume node":"LVN","point of control":"POC","poc":"POC",
    "value area high":"VAH","value area low":"VAL","value area":"VA","volume profile":"VOL_PROF",
    "cumulative volume delta":"CVD","cvd":"CVD","buy volume":"BUY_VOL","sell volume":"SELL_VOL","volume delta":"VOL_DELTA",
    "accumulation":"ACCUM","distribution":"DISTRIB",
    # PRICE ACTION
    "key level":"KEY_LVL","support":"SUPPORT","resistance":"RESISTANCE",
    "breakout":"BREAKOUT","breakdown":"BREAKDOWN","fakeout":"FAKEOUT",
    "reversal":"REVERSAL","bounce":"BOUNCE","rejection":"REJECTION",
    "higher high":"HH","lower low":"LL","higher low":"HL","lower high":"LH",
    "swing high":"SWING_H","swing low":"SWING_L",
    "double top":"DOUBLE_TOP","double bottom":"DOUBLE_BOTTOM",
    "triple top":"TRIPLE_TOP","triple bottom":"TRIPLE_BOTTOM",
    "head and shoulder":"HEAD_SHOULDER","inverse head shoulder":"INV_HS",
    "cup and handle":"CUP_HANDLE","rounding bottom":"ROUND_BTM",
    "bull flag":"BULL_FLAG","bear flag":"BEAR_FLAG","flag":"FLAG",
    "pennant":"PENNANT","rising wedge":"RISE_WEDGE","falling wedge":"FALL_WEDGE","wedge":"WEDGE",
    "ascending triangle":"ASC_TRI","descending triangle":"DESC_TRI","symmetrical triangle":"SYM_TRI",
    "gap up":"GAP_UP","gap down":"GAP_DOWN","gap fill":"GAP_FILL",
    "island reversal":"ISLAND_REV","measured move":"MEAS_MOVE",
    # CANDLESTICK
    "dragonfly doji":"DRAG_DOJI","gravestone doji":"GRAVE_DOJI","doji":"DOJI",
    "inverted hammer":"INV_HAMMER","hammer":"HAMMER",
    "shooting star":"SHOOT_STAR","hanging man":"HANG_MAN",
    "bullish engulfing":"BULL_ENGULF","bearish engulfing":"BEAR_ENGULF","engulfing":"ENGULF",
    "morning star":"MORN_STAR","evening star":"EVE_STAR","harami":"HARAMI",
    "three white soldiers":"THREE_WS","three black crows":"THREE_BC",
    "dark cloud cover":"DARK_CLOUD","piercing line":"PIERC_LINE",
    "inside bar":"INSIDE_BAR","outside bar":"OUT_BAR","nr7":"NR7","nr4":"NR4","pin bar":"PIN_BAR",
    "tweezer top":"TWEEZ_TOP","tweezer bottom":"TWEEZ_BTM","marubozu":"MARUBOZU",
    # FIBONACCI
    "fib retracement":"FIB_RET","fib extension":"FIB_EXT","fib 38":"FIB_38","fib 50":"FIB_50",
    "fib 61":"FIB_61","fib 78":"FIB_78","fib 127":"FIB_127","fib 161":"FIB_161","fibonacci":"FIB",
    "golden ratio":"GOLDEN_RATIO","fib cluster":"FIB_CLUSTER","fib fan":"FIB_FAN",
    # SMART MONEY CONCEPTS
    "bullish order block":"BULL_OB","bearish order block":"BEAR_OB","order block":"ORDER_BLOCK",
    "breaker block":"BREAKER","mitigation block":"MITIG_BLK","rejection block":"REJ_BLK",
    "fair value gap":"FVG","fvg":"FVG","imbalance":"IMBALANCE",
    "buy side liquidity":"BSL","sell side liquidity":"SSL",
    "liquidity sweep":"LIQ_SWEEP","liquidity grab":"LIQ_GRAB","stop hunt":"STOP_HUNT",
    "inducement":"INDUCEMENT","change of character":"CHOCH","choch":"CHOCH",
    "break of structure":"BOS","bos":"BOS","market structure shift":"MSS",
    "premium zone":"PREMIUM","discount zone":"DISCOUNT","equilibrium":"EQ",
    "institutional buying":"INST_BUY","institutional selling":"INST_SELL","smart money":"SMART_MONEY",
    # WYCKOFF
    "accumulation phase":"ACCUM_PHASE","distribution phase":"DISTRIB_PHASE",
    "reaccumulation":"REACCUM","redistribution":"REDISTRIB",
    "spring":"SPRING","upthrust":"UPTHRUST",
    "selling climax":"SC","buying climax":"BC","automatic rally":"AR",
    "last point of support":"LPS","last point of supply":"LPSY",
    "sign of strength":"SOS","sign of weakness":"SOW","wyckoff":"WYCKOFF",
    # ELLIOTT WAVE
    "wave 1":"WAVE1","wave 2":"WAVE2","wave 3":"WAVE3","wave 4":"WAVE4","wave 5":"WAVE5",
    "wave a":"WAVE_A","wave b":"WAVE_B","wave c":"WAVE_C",
    "impulse wave":"IMPULSE","corrective wave":"CORRECTIVE",
    "zigzag correction":"ZZ_CORR","flat correction":"FLAT_CORR","elliott wave":"ELLIOTT",
    # OPTIONS SPECIFIC
    "long buildup":"LONG_BUILD","short buildup":"SHORT_BUILD",
    "long unwinding":"LONG_UNWIND","short covering":"SHORT_COV","oi buildup":"OI_BUILD","oi unwinding":"OI_UNWIND","open interest":"OI",
    "pcr high":"PCR_HIGH","pcr low":"PCR_LOW","pcr rising":"PCR_RISE","pcr falling":"PCR_FALL","put call ratio":"PCR","pcr":"PCR",
    "max pain":"MAX_PAIN","gamma flip":"GAMMA_FLIP","positive gex":"POS_GEX","negative gex":"NEG_GEX","gamma exposure":"GEX",
    "theta decay":"THETA_DECAY","theta positive":"THETA_POS","delta neutral":"DELTA_NEUT",
    "vanna":"VANNA","charm":"CHARM","gamma scalping":"GAMMA_SCALP","pin risk":"PIN_RISK",
    "dark pool":"DARK_POOL","block trade":"BLOCK_TRADE","sweep":"SWEEP","unusual activity":"UNUSUAL_ACT",
    "call writing":"CALL_WRITE","put writing":"PUT_WRITE","rollover":"ROLLOVER",
    # MICROSTRUCTURE
    "aggressive buyer":"AGG_BUY","aggressive seller":"AGG_SELL",
    "tape reading":"TAPE_READ","order flow":"ORDER_FLOW",
    "market depth":"MKT_DEPTH","depth of market":"DOM","dom":"DOM",
    "absorption":"ABSORPTION","exhaustion":"EXHAUSTION",
    "footprint chart":"FOOTPRINT","delta divergence":"DELTA_DIV",
    "iceberg order":"ICEBERG","hidden order":"HIDDEN_ORD","spoofing":"SPOOFING",
    # INTERMARKET & MACRO
    "fii buying":"FII_BUY","fii selling":"FII_SELL","fii data":"FII_DATA",
    "dii buying":"DII_BUY","dii selling":"DII_SELL","dii data":"DII_DATA",
    "foreign inflow":"FOR_INFLOW","foreign outflow":"FOR_OUTFLOW",
    "dollar index":"DXY","dollar strong":"DXY_STRONG","dollar weak":"DXY_WEAK","dxy":"DXY",
    "sgx nifty":"SGX_NIFTY","gift nifty":"GIFT_NIFTY","global cues":"GLOBAL_CUE",
    "us market":"US_MKT","dow jones":"DOW","nasdaq":"NASDAQ","sp500":"SP500","s&p":"SP500",
    "asian market":"ASIAN_MKT","european market":"EUR_MKT",
    "crude oil":"CRUDE","brent":"BRENT","gold price":"GOLD_PRICE",
    "bond yield":"BOND_YIELD","10 year yield":"YIELD_10Y","us yield":"US_YIELD",
    "rbi policy":"RBI","fed meeting":"FED","ecb":"ECB",
    "inflation":"INFLATION","cpi":"CPI","gdp":"GDP","nonfarm payroll":"NFP",
    "earnings":"EARNINGS","results season":"RESULTS","budget":"BUDGET","elections":"ELECTION",
    "geopolitical":"GEO_POL","risk on":"RISK_ON","risk off":"RISK_OFF",
    "sector rotation":"SECT_ROT","correlation":"CORREL",
    # STATISTICAL
    "mean reversion":"MEAN_REV","momentum factor":"MOM_FACTOR",
    "z score":"ZSCORE","standard deviation":"STD_DEV",
    "cointegration":"COINTEG","pairs trade":"PAIRS","spread trade":"SPREAD_TRD",
    "statistical arbitrage":"STAT_ARB","market neutral":"MKT_NEUTRAL",
    # REGIME
    "trending market":"TRENDING","sideways market":"SIDEWAYS","rangebound":"RANGEBOUND","range bound":"RANGEBOUND",
    "consolidating":"CONSOLIDATING","volatile market":"VOLATILE",
    "low volatility regime":"LOW_VOL_REG","high volatility":"HIGH_VOL",
    "bull market":"BULL_MKT","bear market":"BEAR_MKT",
    "overbought":"OVERBOUGHT","oversold":"OVERSOLD",
    "euphoria":"EUPHORIA","panic":"PANIC","capitulation":"CAPITULATION",
}

# ═══════════════════════════════════════
# RISK MANAGEMENT ENGINE (Complete)
# ═══════════════════════════════════════
RISK_CONDITIONS = {
    # Position Sizing Methods
    "fixed lot":"FIXED_LOT","fixed quantity":"FIXED_QTY",
    "1% risk":"RISK_1PCT","2% risk":"RISK_2PCT","percent risk":"PCT_RISK",
    "kelly criterion":"KELLY","half kelly":"HALF_KELLY",
    "optimal f":"OPTIMAL_F","fixed fractional":"FIXED_FRAC",
    "volatility sizing":"VOL_SIZE","atr sizing":"ATR_SIZE",
    "equal weight":"EQUAL_WT",
    # Stop Loss Types
    "fixed stop":"FIXED_SL","percentage stop":"PCT_SL",
    "atr stop":"ATR_SL","volatility stop":"VOL_SL",
    "swing stop":"SWING_SL","structure stop":"STRUCT_SL",
    "chandelier stop":"CHAND_SL","parabolic stop":"PARA_SL",
    "time stop":"TIME_SL","profit stop":"PROFIT_SL",
    "break even stop":"BE_SL","trailing stop":"TRAIL_SL",
    "hard stop":"HARD_SL","guaranteed stop":"GUAR_SL",
    "catastrophic stop":"CAT_SL",
    # Target / Exit Types
    "1r":"R1","2r":"R2","3r":"R3","5r":"R5","r multiple":"R_MULT",
    "fibonacci target":"FIB_TGT","measured move target":"MM_TGT",
    "partial target":"PART_TGT","trailing target":"TRAIL_TGT",
    "vwap target":"VWAP_TGT","time target":"TIME_TGT",
    # Risk Ratios
    "1:1":"RR_1_1","1:2":"RR_1_2","1:3":"RR_1_3","1:5":"RR_1_5","2:1":"RR_2_1",
    "positive expectancy":"POS_EXP","negative expectancy":"NEG_EXP",
    # Portfolio Risk
    "max drawdown":"MAX_DD","daily drawdown":"DAILY_DD",
    "weekly drawdown":"WEEK_DD","monthly drawdown":"MONTH_DD",
    "portfolio heat":"PORT_HEAT","correlation risk":"CORR_RISK",
    "concentration risk":"CONC_RISK","sector exposure":"SECT_EXP",
    "beta exposure":"BETA_EXP","net delta":"NET_DELTA",
    "gross exposure":"GROSS_EXP","delta exposure":"DELTA_EXP",
    # Trade Limits
    "max trades per day":"MAX_TRADES","daily trade limit":"DAILY_LIM",
    "3 loss stop":"LOSS_3_STOP","consecutive loss limit":"CONSEC_LOSS",
    "daily loss limit":"DAILY_LOSS","weekly loss limit":"WEEK_LOSS",
    "monthly loss limit":"MONTH_LOSS","drawdown pause":"DD_PAUSE",
    # Options Risk
    "max premium risk":"MAX_PREM","premium stop":"PREM_SL",
    "delta limit":"DELTA_LIM","gamma risk":"GAMMA_RISK",
    "theta budget":"THETA_BDG","vega exposure":"VEGA_EXP",
    "assignment risk":"ASSIGN_RISK","margin risk":"MARGIN_RISK",
    "leverage risk":"LEV_RISK","pin risk":"PIN_RISK",
    # Hedging
    "hedge ratio":"HEDGE_RATIO","delta hedge":"DELTA_HDG",
    "portfolio hedge":"PORT_HDG","tail hedge":"TAIL_HDG",
    "vix hedge":"VIX_HDG","put hedge":"PUT_HDG",
    "collar hedge":"COLLAR_HDG","correlation hedge":"CORR_HDG",
    # Performance Metrics
    "sharpe ratio":"SHARPE","sortino ratio":"SORTINO",
    "calmar ratio":"CALMAR","win rate":"WIN_RATE",
    "profit factor":"PROFIT_FACTOR","average win":"AVG_WIN",
    "average loss":"AVG_LOSS","expectancy":"EXPECTANCY",
    "recovery factor":"RECOV_FACTOR",
    # Psychology/Discipline
    "revenge trade":"REVENGE","fomo":"FOMO","overtrading":"OVERTRADE",
    "tilt":"TILT","trading plan":"TRADE_PLAN",
    "journal":"JOURNAL","review":"REVIEW","discipline":"DISCIPLINE",
    # Hinglish
    "max loss lagao":"MAX_LOSS_SET","stop loss mandatory":"SL_MANDATORY",
    "risk kam karo":"REDUCE_RISK","hedge karo":"HEDGE_NOW",
    "position chota karo":"REDUCE_POS","profit lock karo":"LOCK_PROFIT",
}

EXIT_CONDITIONS = {
    "stop loss":"STOPLOSS","sl":"STOPLOSS","stoploss":"STOPLOSS",
    "target":"TARGET","tp":"TARGET","take profit":"TARGET",
    "trailing stop":"TRAIL_SL","trailing sl":"TRAIL_SL",
    "break even":"BREAKEVEN","partial exit":"PART_EXIT",
    "50% exit":"HALF_EXIT","half exit":"HALF_EXIT","scale out":"SCALE_OUT",
    "eod exit":"EOD_EXIT","time stop":"TIME_SL","reverse signal":"REV_SIG",
    "50% premium":"HALF_PREM","premium stop":"PREM_SL",
    "theta exit":"THETA_EXIT","delta exit":"DELTA_EXIT",
    "daily stop":"DAILY_STOP","loss limit":"LOSS_LIM",
    "nikal lo":"EXIT_NOW","bahar niklo":"EXIT_NOW","profit book karo":"BOOK_PROFIT",
    "बाहर":"EXIT_NOW","निकलो":"EXIT_NOW",
}

STRIKE_SELECTION = {
    "deep itm":"DEEP_ITM","slight itm":"SLIGHT_ITM",
    "at the money":"ATM","atm":"ATM",
    "deep otm":"DEEP_OTM","slight otm":"SLIGHT_OTM","out of the money":"OTM","otm":"OTM",
    "in the money":"ITM","itm":"ITM",
    "3 strike otm":"OTM_3","2 strike otm":"OTM_2","1 strike otm":"OTM_1",
    "2 strike itm":"ITM_2","1 strike itm":"ITM_1",
    "50 delta":"D50","delta 50":"D50","25 delta":"D25","delta 25":"D25",
    "16 delta":"D16","delta 16":"D16","10 delta":"D10","delta 10":"D10",
    "500 premium":"P500","200 premium":"P200","100 premium":"P100",
    "equidistant":"EQUIDIST","symmetric":"SYMMETRIC","same strike":"SAME",
}

TIME_MAP = {
    "pre market":"09:00","market open":"09:15","opening":"09:15",
    "first 15 minutes":"09:30","orb":"09:30",
    "morning":"09:20","subah":"09:20","सुबह":"09:20",
    "mid day":"12:00","noon":"12:00","dopahar":"12:00","दोपहर":"12:00",
    "afternoon":"14:00","power hour":"14:00",
    "last hour":"14:30","last 30 min":"15:00",
    "closing":"15:15","market close":"15:15","shaam":"15:00","शाम":"15:00",
    "eod":"15:20","expiry time":"15:25","end of day":"15:20",
}

EXPIRY_MAP = {
    "next week":"NEXT_WEEKLY","this week":"WEEKLY","weekly expiry":"WEEKLY","week":"WEEKLY","weekly":"WEEKLY",
    "next month":"NEXT_MONTHLY","this month":"MONTHLY","monthly expiry":"MONTHLY","month":"MONTHLY","monthly":"MONTHLY",
    "current expiry":"CURRENT","near month":"NEAR_MONTH","quarterly":"QUARTERLY",
    "is hafte":"WEEKLY","agle hafte":"NEXT_WEEKLY","mahina":"MONTHLY",
}

# ═══════════════════════════════════════
# RISK CALCULATOR
# ═══════════════════════════════════════
def calculate_risk(text, quantity=1):
    """Calculate risk metrics from input"""
    risk = {}

    # Extract SL points
    sl_match = re.search(r'(?:sl|stop loss|stoploss)\s*[=:@]?\s*(\d+)', text)
    tgt_match = re.search(r'(?:target|tp|take profit)\s*[=:@]?\s*(\d+)', text)
    trail_match = re.search(r'trailing\s*(?:sl|stop)?\s*[=:@]?\s*(\d+)', text)
    rr_match = re.search(r'(?:rr|risk reward)\s*[=:@]?\s*(\d+)[:/](\d+)', text)
    pct_match = re.search(r'(\d+\.?\d*)\s*%\s*(?:risk|capital)', text)

    if sl_match:
        sl_pts = int(sl_match.group(1))
        risk["stoploss_points"] = sl_pts
        risk["stoploss_rupees"] = sl_pts * quantity * 50  # NIFTY lot size

    if tgt_match:
        tgt_pts = int(tgt_match.group(1))
        risk["target_points"] = tgt_pts
        risk["target_rupees"] = tgt_pts * quantity * 50

    if sl_match and tgt_match:
        sl_pts = int(sl_match.group(1))
        tgt_pts = int(tgt_match.group(1))
        risk["risk_reward"] = f"1:{round(tgt_pts/sl_pts, 1)}"
        risk["expectancy"] = round((0.5 * tgt_pts) - (0.5 * sl_pts), 2)

    if trail_match:
        risk["trailing_sl"] = int(trail_match.group(1))

    if rr_match:
        risk["risk_reward"] = f"{rr_match.group(1)}:{rr_match.group(2)}"

    if pct_match:
        risk["risk_percent"] = float(pct_match.group(1))

    # Max loss per day default
    if "daily loss limit" in text or "max loss" in text:
        ml = re.search(r'(?:daily loss|max loss)\s*[=:@]?\s*(\d+)', text)
        if ml: risk["daily_max_loss"] = int(ml.group(1))

    return risk if risk else None

# ═══════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════
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

def extract_conditions(t):
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

def extract_risk_conditions(t):
    found={}
    for k,v in sorted(RISK_CONDITIONS.items(),key=lambda x:-len(x[0])):
        if k in t:
            m=re.search(rf'{re.escape(k)}\s*[=:@]?\s*(\d+\.?\d*)?',t)
            found[v]=float(m.group(1)) if m and m.group(1) else True
    return found if found else None

def extract_exit(t):
    found={}
    for k,v in sorted(EXIT_CONDITIONS.items(),key=lambda x:-len(x[0])):
        if k in t:
            m=re.search(rf'{re.escape(k)}\s*[=:@]?\s*(\d+\.?\d*)?',t)
            found[v]=float(m.group(1)) if m and m.group(1) else True
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
    if any(w in t for w in ["kharido","becho","lo","niklo","subah","shaam","lagao","karo"]): return "HINGLISH"
    return "ENGLISH"

def calc_confidence(r):
    s=0.65
    s+=0.05 if r.get("instrument") else 0
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
# API ENDPOINTS
# ═══════════════════════════════════════
@app.get("/")
def root():
    return {
        "status":"running","version":"12.3","nlp":"institutional_complete",
        "total_conditions":len(ALL_CONDITIONS)+len(RISK_CONDITIONS),
        "modules":["momentum","trend","volatility","volume","price_action",
                   "candlestick","fibonacci","smart_money","wyckoff","elliott_wave",
                   "options_flow","microstructure","intermarket","macro",
                   "statistical","regime","risk_management","position_sizing",
                   "stop_loss","targets","portfolio_risk","hedging","psychology"]
    }

@app.post("/strategy")
def parse(payload: dict):
    raw=payload.get("text","")
    t=raw.lower().strip()
    qty=extract_qty(t)

    instrument=extract_instrument(t)
    action=extract_action(t)
    strike=extract_strike(t)
    option_type=extract_option_type(t)
    strategy=extract_strategy(t)
    conditions=extract_conditions(t)
    exit_cond=extract_exit(t)
    risk_cond=extract_risk_conditions(t)
    risk_metrics=calculate_risk(t, qty)
    strike_sel=extract_strike_sel(t)
    exec_time=extract_time(t)
    expiry=extract_expiry(t)
    lang=detect_lang(t)

    r={
        "instrument":instrument,
        "action":action,
        "language":lang,
        "expiry":expiry,
        "quantity":qty,
    }
    if option_type: r["option_type"]=option_type
    if strike: r["strike"]=strike
    if strike_sel: r["strike_selection"]=strike_sel
    if strategy: r["strategy"]=strategy
    if conditions: r["conditions"]=conditions
    if exit_cond: r["exit"]=exit_cond
    if risk_cond: r["risk_management"]=risk_cond
    if risk_metrics: r["risk_metrics"]=risk_metrics
    if exec_time: r["time"]=exec_time
    r["confidence"]=calc_confidence(r)
    r["parsed_at"]=time.strftime("%H:%M:%S")
    return r

@app.post("/trade")
def trade(s: dict):
    c=s.get("confidence",0)
    # Check risk rules
    risk=s.get("risk_metrics",{})
    if risk.get("daily_max_loss") and risk.get("stoploss_rupees",0)>risk.get("daily_max_loss",999999):
        return {"status":"REJECTED","reason":"Trade exceeds daily loss limit"}
    if c<0.50: return {"status":"REJECTED","reason":"Low confidence","confidence":c}
    if c<0.70: return {"status":"REVIEW","reason":"Manual review needed","confidence":c}
    return {
        "status":"EXECUTED","result":s,
        "order_id":f"ORD{int(time.time()*1000)%1000000:06d}",
        "executed_at":time.strftime("%H:%M:%S")
    }

@app.get("/risk/calculator")
def risk_calc(sl: float=100, target: float=200, qty: int=1, lot_size: int=50):
    risk_amt=sl*qty*lot_size
    reward_amt=target*qty*lot_size
    rr=round(target/sl,2) if sl>0 else 0
    win_rate_needed=round(1/(1+rr)*100,1)
    return {
        "stoploss_points":sl,"target_points":target,
        "quantity_lots":qty,"lot_size":lot_size,
        "risk_rupees":risk_amt,"reward_rupees":reward_amt,
        "risk_reward":f"1:{rr}",
        "min_win_rate_needed":f"{win_rate_needed}%",
        "expectancy_per_trade":round((0.5*reward_amt)-(0.5*risk_amt),2)
    }

@app.get("/capabilities")
def caps():
    return {
        "total_conditions":len(ALL_CONDITIONS)+len(RISK_CONDITIONS),
        "examples":[
            "buy nifty atm call if rsi < 30 and ema crossover stop loss 100 target 300",
            "sell banknifty iron condor if vix > 15 and rangebound weekly trailing sl 50",
            "buy nifty if wyckoff spring and fii buying and golden cross 2r target",
            "short banknifty if order block resistance and dark pool selling eod exit",
            "iron condor nifty otm 2 strike if iv rank > 50 and sideways max loss 5000",
            "kharido nifty 50 delta call if macd bullish and supertrend buy subah 1% risk",
            "sell nifty straddle if vix crush and theta positive 3 loss stop daily",
            "buy if elliott wave 3 and fibonacci 61 support and volume surge stop loss 150",
        ]
    }
