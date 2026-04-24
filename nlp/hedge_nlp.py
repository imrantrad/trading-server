"""
Complete Hedge NLP Module v12.3
All hedging strategies, instruments, conditions
"""

HEDGE_INSTRUMENTS = {
    # Index Hedges
    "nifty put":"NIFTY_PE","nifty ce hedge":"NIFTY_CE_HEDGE",
    "banknifty put":"BNF_PE","banknifty hedge":"BNF_HEDGE",
    "nifty futures":"NIFTY_FUT","banknifty futures":"BNF_FUT",
    "nifty options":"NIFTY_OPT","index hedge":"IDX_HEDGE",
    # VIX Hedges
    "vix call":"VIX_CALL","buy vix":"LONG_VIX","vix spike hedge":"VIX_HEDGE",
    # Currency Hedges
    "usdinr put":"USDINR_PUT","dollar hedge":"USD_HEDGE","currency hedge":"CURR_HEDGE",
    "eurinr":"EURINR","gbpinr":"GBPINR",
    # Commodity Hedges
    "gold hedge":"GOLD_HEDGE","crude put":"CRUDE_PUT","silver hedge":"SILVER_HEDGE",
    # Stock Hedges
    "stock put":"STOCK_PUT","portfolio hedge":"PORT_HEDGE","basket hedge":"BASKET_HEDGE",
    # ETF Hedges
    "niftybees put":"NBEES_PUT","bankbees":"BANKBEES",
}

HEDGE_STRATEGIES = {
    # Basic Protection
    "protective put":"PROTECTIVE_PUT",
    "married put":"MARRIED_PUT",
    "covered call":"COVERED_CALL",
    "collar":"COLLAR",
    "collar hedge":"COLLAR_HEDGE",
    "zero cost collar":"ZERO_COLLAR",
    "fence":"FENCE",
    # Ratio Hedges
    "ratio hedge":"RATIO_HEDGE",
    "1:2 hedge":"RATIO_1_2",
    "1:3 hedge":"RATIO_1_3",
    "ratio backspread":"RATIO_BS",
    # Spread Hedges
    "debit spread hedge":"DEBIT_HEDGE",
    "put spread hedge":"PUT_SPREAD_HEDGE",
    "bear put spread":"BEAR_PUT_SPR",
    "diagonal hedge":"DIAG_HEDGE",
    "calendar hedge":"CAL_HEDGE",
    # Delta Hedges
    "delta hedge":"DELTA_HEDGE",
    "delta neutral":"DELTA_NEUTRAL",
    "dynamic delta hedge":"DYN_DELTA",
    "delta one hedge":"DELTA_ONE",
    "gamma hedge":"GAMMA_HEDGE",
    "vega hedge":"VEGA_HEDGE",
    "theta hedge":"THETA_HEDGE",
    # Portfolio Hedges
    "portfolio hedge":"PORTFOLIO_HEDGE",
    "tail risk hedge":"TAIL_HEDGE",
    "black swan hedge":"BLACK_SWAN",
    "crash protection":"CRASH_PROT",
    "drawdown protection":"DD_PROT",
    "max loss hedge":"MAX_LOSS_HEDGE",
    # Correlation Hedges
    "correlation hedge":"CORR_HEDGE",
    "sector hedge":"SECTOR_HEDGE",
    "cross hedge":"CROSS_HEDGE",
    "proxy hedge":"PROXY_HEDGE",
    "intermarket hedge":"INTER_HEDGE",
    # Volatility Hedges
    "vix hedge":"VIX_HEDGE",
    "long vix":"LONG_VIX",
    "volatility hedge":"VOL_HEDGE",
    "iv hedge":"IV_HEDGE",
    "long gamma":"LONG_GAMMA",
    "long vega":"LONG_VEGA",
    "variance swap":"VAR_SWAP",
    "vol swap":"VOL_SWAP",
    # Event Hedges
    "event hedge":"EVENT_HEDGE",
    "earnings hedge":"EARN_HEDGE",
    "budget hedge":"BUDGET_HEDGE",
    "expiry hedge":"EXPIRY_HEDGE",
    "news hedge":"NEWS_HEDGE",
    "binary event hedge":"BINARY_HEDGE",
    "election hedge":"ELEC_HEDGE",
    "rbi hedge":"RBI_HEDGE",
    "fed hedge":"FED_HEDGE",
    # Options-Specific
    "short straddle hedge":"SS_HEDGE",
    "iron condor hedge":"IC_HEDGE",
    "strangle hedge":"STNG_HEDGE",
    "butterfly hedge":"BFLY_HEDGE",
    "condor hedge":"COND_HEDGE",
    # Pair/Arb Hedges
    "pairs hedge":"PAIRS_HEDGE",
    "cash futures arbitrage":"CF_ARB",
    "put call parity hedge":"PCP_HEDGE",
    "synthetic hedge":"SYNTH_HEDGE",
    "box spread":"BOX_SPREAD",
    # Institutional
    "index replication hedge":"IDX_REP",
    "beta hedge":"BETA_HEDGE",
    "factor hedge":"FACTOR_HEDGE",
    "statistical hedge":"STAT_HEDGE",
    "dispersion hedge":"DISP_HEDGE",
    "relative value hedge":"REL_VAL",
}

HEDGE_TRIGGERS = {
    # Risk-based
    "if loss exceeds":"LOSS_TRIGGER",
    "if drawdown":"DD_TRIGGER",
    "if portfolio down":"PORT_DOWN",
    "if position against":"POS_AGAINST",
    "if stop loss near":"SL_NEAR",
    "if daily loss limit":"DL_TRIGGER",
    # Market-based
    "if vix rises":"VIX_RISE",
    "if vix above":"VIX_ABOVE",
    "if market falls":"MKT_FALL",
    "if gap down":"GAP_DN_TRIG",
    "if breakdown":"BD_TRIG",
    "if global selloff":"GLOBAL_SO",
    "if circuit breaker":"CIRCUIT",
    # Expiry-based
    "before expiry":"PRE_EXP",
    "on expiry":"ON_EXP",
    "theta decay hedge":"THETA_TRIG",
    "gamma risk hedge":"GAMMA_TRIG",
    # Event-based
    "before earnings":"PRE_EARN",
    "before results":"PRE_RESULTS",
    "before budget":"PRE_BUDGET",
    "before rbi policy":"PRE_RBI",
    "before fed meeting":"PRE_FED",
    "before election":"PRE_ELEC",
    # Delta-based
    "if delta exceeds":"DELTA_TRIG",
    "if net delta high":"NET_DELTA",
    "if gamma risk":"GAMMA_RISK",
    # IV-based
    "if iv rises":"IV_RISE",
    "if iv expansion":"IV_EXP_TRIG",
    "if iv rank high":"IVR_HIGH",
    # Correlation-based
    "if correlation breaks":"CORR_BREAK",
    "if sector rotates":"SECT_ROT",
    "if fii selling":"FII_SELL_TRIG",
    # Hinglish
    "hedge lagao":"HEDGE_NOW",
    "bachao portfolio":"SAVE_PORT",
    "loss se bachao":"LOSS_PROT",
    "risk kam karo":"REDUCE_RISK",
    # Hindi
    "हेज लगाओ":"HEDGE_NOW",
    "सुरक्षा करो":"PROTECT",
    "नुकसान से बचाओ":"LOSS_PROT",
}

HEDGE_SIZING = {
    "full hedge":"FULL_100PCT",
    "50% hedge":"HALF_50PCT",
    "partial hedge":"PARTIAL",
    "25% hedge":"QUARTER",
    "10% hedge":"TEN_PCT",
    "minimum hedge":"MINIMUM",
    "maximum hedge":"MAXIMUM",
    "over hedge":"OVER",
    "under hedge":"UNDER",
    "delta matched":"DELTA_MATCH",
    "beta matched":"BETA_MATCH",
    "dollar matched":"DOLLAR_MATCH",
    "notional matched":"NOTIONAL",
    "1:1 hedge":"ONE_TO_ONE",
    "rolling hedge":"ROLLING",
    "strip hedge":"STRIP",
    "stack hedge":"STACK",
}

HEDGE_EXIT = {
    "remove hedge":"REMOVE_HEDGE",
    "unwind hedge":"UNWIND_HEDGE",
    "close hedge":"CLOSE_HEDGE",
    "roll hedge":"ROLL_HEDGE",
    "adjust hedge":"ADJUST_HEDGE",
    "rebalance hedge":"REBALANCE_HEDGE",
    "hedge expired":"HEDGE_EXPIRED",
    "hedge target hit":"HEDGE_TGT",
    "hedge stop":"HEDGE_SL",
    "when risk resolved":"RISK_RESOLVED",
    "hedge nikal lo":"REMOVE_HEDGE",
    "hedge band karo":"CLOSE_HEDGE",
}


def parse_hedge(text: str) -> dict:
    """Extract all hedge-related information from text"""
    t = text.lower()
    result = {}

    # Detect hedge intent
    hedge_keywords = ["hedge","bachao","protect","suraksha","bachana",
                      "हेज","सुरक्षा","risk kam","loss se","cover karo"]
    if not any(k in t for k in hedge_keywords):
        return {}

    result["is_hedge"] = True

    # Extract hedge strategy
    for k,v in sorted(HEDGE_STRATEGIES.items(), key=lambda x:-len(x[0])):
        if k in t:
            result["hedge_strategy"] = v
            break

    # Extract hedge instrument
    for k,v in sorted(HEDGE_INSTRUMENTS.items(), key=lambda x:-len(x[0])):
        if k in t:
            result["hedge_instrument"] = v
            break

    # Extract trigger
    for k,v in sorted(HEDGE_TRIGGERS.items(), key=lambda x:-len(x[0])):
        if k in t:
            result["hedge_trigger"] = v
            break

    # Extract sizing
    for k,v in sorted(HEDGE_SIZING.items(), key=lambda x:-len(x[0])):
        if k in t:
            result["hedge_size"] = v
            break

    # Extract exit
    for k,v in sorted(HEDGE_EXIT.items(), key=lambda x:-len(x[0])):
        if k in t:
            result["hedge_exit"] = v
            break

    # Extract hedge ratio from numbers
    import re
    ratio = re.search(r'(\d+)\s*%\s*hedge', t)
    if ratio:
        result["hedge_pct"] = int(ratio.group(1))

    # Extract delta target
    delta = re.search(r'delta\s*[=:]?\s*(\d+)', t)
    if delta:
        result["target_delta"] = int(delta.group(1))

    # Detect hedge type
    if "dynamic" in t or "delta" in t:
        result["hedge_type"] = "DYNAMIC"
    elif "static" in t:
        result["hedge_type"] = "STATIC"
    elif "portfolio" in t:
        result["hedge_type"] = "PORTFOLIO"
    elif "tail" in t or "crash" in t or "black swan" in t:
        result["hedge_type"] = "TAIL_RISK"
    else:
        result["hedge_type"] = "STANDARD"

    return result
