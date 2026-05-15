"""
INSTITUTIONAL PAPER TRADING ENGINE — TRD v12.3
================================================
Spec: Points 1-60 — Hedge Fund Grade Live Simulation
- Real-time market price engine
- Execution simulation (spread/slippage/partial fills/latency)
- Risk management (daily loss, drawdown, Kelly, VaR)
- Portfolio Greeks (Delta/Gamma/Theta/Vega)
- AI trade quality scoring
- Regime detection
- Full audit trail
- Deterministic replay
"""

import math, hashlib, json, time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from backtest.historical_price_engine import (
    reconstruct_spot_price, reconstruct_vix,
    black_scholes_greeks as _bs, LOT_SIZES
)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS — NSE Market Structure
# ══════════════════════════════════════════════════════════════════════════════

NSE_OPEN  = (9, 15)   # 09:15 AM
NSE_CLOSE = (15, 30)  # 03:30 PM
RISK_FREE_RATE = 0.065

# NSE Holidays 2024-2025 (key dates)
NSE_HOLIDAYS = {
    "2024-01-26","2024-03-25","2024-04-14","2024-04-17","2024-04-21",
    "2024-05-23","2024-06-17","2024-08-15","2024-10-02","2024-10-14",
    "2024-11-15","2024-11-20","2024-12-25",
    "2025-02-26","2025-03-14","2025-03-31","2025-04-10","2025-04-14",
    "2025-04-18","2025-05-01","2025-06-07","2025-08-15","2025-10-02",
}

INSTRUMENT_PARAMS = {
    "NIFTY":      {"spot": 24000, "strike_step": 50,  "lot": 65,  "spread": 0.5,  "margin_pct": 0.12},
    "BANKNIFTY":  {"spot": 52000, "strike_step": 100, "lot": 30,  "spread": 1.0,  "margin_pct": 0.12},
    "FINNIFTY":   {"spot": 23000, "strike_step": 50,  "lot": 60,  "spread": 0.8,  "margin_pct": 0.12},
    "MIDCPNIFTY": {"spot": 12000, "strike_step": 50,  "lot": 120, "spread": 1.5,  "margin_pct": 0.13},
    "NIFTYNXT50": {"spot": 70000, "strike_step": 100, "lot": 25,  "spread": 2.0,  "margin_pct": 0.14},
    "SENSEX":     {"spot": 78000, "strike_step": 100, "lot": 10,  "spread": 1.0,  "margin_pct": 0.12},
}

# ══════════════════════════════════════════════════════════════════════════════
# LIVE MARKET PRICE ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def get_live_spot(instrument: str) -> float:
    """Get current live spot price — uses price from today's date seed"""
    today = date.today()
    return reconstruct_spot_price(instrument, today)

def get_live_vix() -> float:
    """Get live VIX"""
    return reconstruct_vix(date.today())

def get_live_option_price(instrument: str, strike: int, option_type: str,
                           dte: int, spot: float = None, vix: float = None) -> dict:
    """
    Calculate live option price using Black-Scholes with current market params.
    Returns full option data including Greeks and lot economics.
    """
    if spot is None:
        spot = get_live_spot(instrument)
    if vix is None:
        vix = get_live_vix()

    params = INSTRUMENT_PARAMS.get(instrument, INSTRUMENT_PARAMS["NIFTY"])
    lot_size = params["lot"]
    T = max(0.003, dte / 365)
    sigma = vix / 100

    # IV skew: OTM options have higher IV
    moneyness = (strike - spot) / spot
    if option_type == "CE":
        iv_adj = max(0.05, sigma + moneyness * 0.5)   # higher IV for OTM CE
    else:
        iv_adj = max(0.05, sigma - moneyness * 0.5)   # higher IV for OTM PE

    greeks = _bs(spot, strike, T, RISK_FREE_RATE, iv_adj, option_type)
    price = greeks["price"]

    # Bid-ask spread
    spread = params["spread"]
    bid = round(max(0.05, price - spread/2), 2)
    ask = round(price + spread/2, 2)
    mid = round((bid + ask) / 2, 2)

    # Lot economics
    lot_value = round(mid * lot_size, 2)
    margin    = round(spot * lot_size * params["margin_pct"], 2)

    moneyness_label = "ATM"
    step = params["strike_step"]
    atm  = round(spot / step) * step
    if option_type == "CE":
        moneyness_label = "ATM" if strike == atm else ("OTM" if strike > atm else "ITM")
    else:
        moneyness_label = "ATM" if strike == atm else ("OTM" if strike < atm else "ITM")

    return {
        "instrument": instrument, "strike": strike, "option_type": option_type,
        "dte": dte, "spot": spot, "iv": round(iv_adj * 100, 2),
        "bid": bid, "ask": ask, "mid": mid,
        "delta": greeks["delta"], "gamma": greeks["gamma"],
        "theta": greeks["theta"], "vega": greeks["vega"],
        "lot_size": lot_size, "lot_value": lot_value, "margin": margin,
        "moneyness": moneyness_label,
        "timestamp": datetime.now().isoformat(),
    }

def select_strike(instrument: str, option_type: str, mode: str = "ATM",
                  delta_target: float = 0.5, spot: float = None) -> int:
    """Smart strike selection: ATM / OTM / ITM / Delta-based"""
    if spot is None:
        spot = get_live_spot(instrument)
    params = INSTRUMENT_PARAMS.get(instrument, INSTRUMENT_PARAMS["NIFTY"])
    step = params["strike_step"]
    atm  = round(spot / step) * step

    if mode == "ATM":
        return atm
    elif mode == "OTM1":
        return atm + step if option_type == "CE" else atm - step
    elif mode == "OTM2":
        return atm + 2*step if option_type == "CE" else atm - 2*step
    elif mode == "ITM1":
        return atm - step if option_type == "CE" else atm + step
    elif mode == "DELTA":
        # Find strike closest to target delta
        best_strike = atm
        best_diff   = 999
        for offset in range(-5, 6):
            k = atm + offset * step
            if k <= 0:
                continue
            dte = 7
            data = get_live_option_price(instrument, k, option_type, dte, spot)
            diff = abs(abs(data["delta"]) - delta_target)
            if diff < best_diff:
                best_diff   = diff
                best_strike = k
        return best_strike
    return atm

def get_next_expiry_dte() -> int:
    """Returns DTE to next weekly Thursday expiry"""
    today   = date.today()
    weekday = today.weekday()  # 0=Mon, 3=Thu
    days    = (3 - weekday) % 7
    if days == 0:
        days = 7
    return max(1, days)

# ══════════════════════════════════════════════════════════════════════════════
# EXECUTION SIMULATION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def simulate_paper_execution(price: float, lots: int, instrument: str,
                              action: str, regime: str,
                              vix: float, order_type: str = "MARKET") -> dict:
    """
    Simulate realistic execution: slippage, spread, partial fill, latency.
    Returns actual execution details.
    """
    params = INSTRUMENT_PARAMS.get(instrument, INSTRUMENT_PARAMS["NIFTY"])
    spread = params["spread"]

    # ── Spread impact ────────────────────────────────────────────────
    half_spread = spread / 2
    if action == "BUY":
        spread_impact = half_spread          # Pay ask
    else:
        spread_impact = -half_spread         # Sell at bid

    # ── Slippage (regime-dependent) ──────────────────────────────────
    base_slip = 0.10
    vol_slip  = 0.25 if regime in ("HIGH_VOL","EXPIRY","GAPDAY") else 0.08
    size_slip = (lots / 10) * 0.05          # 5 paise per 10 lots
    total_slip = base_slip + vol_slip + size_slip

    if action == "BUY":
        exec_price = price + half_spread + total_slip
    else:
        exec_price = price - half_spread - total_slip

    exec_price = round(max(0.05, exec_price), 2)

    # ── Partial fill ─────────────────────────────────────────────────
    fill_rate = 1.0
    if lots > 20:
        fill_rate = 0.90
    elif lots > 10:
        fill_rate = 0.95
    filled_lots = max(1, round(lots * fill_rate))

    # ── Latency (ms) ─────────────────────────────────────────────────
    base_lat = 50 if regime == "HIGH_VOL" else 15
    latency_ms = base_lat + int(vix * 2)

    # ── Order rejection probability ──────────────────────────────────
    reject_prob = 0.0
    if regime == "HIGH_VOL" and lots > 15:
        reject_prob = 0.03     # 3% rejection for large orders in high vol
    rejected = reject_prob > 0.02

    lot_size  = INSTRUMENT_PARAMS[instrument]["lot"]
    trade_val = round(exec_price * lot_size * filled_lots, 2)

    return {
        "exec_price":   exec_price,
        "filled_lots":  filled_lots,
        "fill_rate":    fill_rate,
        "spread_cost":  round(abs(spread_impact) * lot_size * filled_lots, 2),
        "slippage_cost":round(total_slip * lot_size * filled_lots, 2),
        "latency_ms":   latency_ms,
        "trade_value":  trade_val,
        "rejected":     rejected,
        "exec_type":    order_type,
        "regime":       regime,
    }

def calculate_all_charges(exec_price: float, lot_size: int, lots: int) -> dict:
    """Accurate Indian market transaction costs"""
    val      = exec_price * lot_size * lots
    brok     = min(20.0, val * 0.0003)
    stt      = val * 0.000625              # 0.0625% on sell
    exch     = val * 0.00053              # 0.053%
    sebi     = val * 0.000001             # ₹10 per crore
    stamp    = val * 0.00003              # 0.003%
    sub      = brok + stt + exch + sebi + stamp
    gst      = sub * 0.18
    total    = round(sub + gst, 2)

    return {"brokerage":round(brok,2),"stt":round(stt,2),
            "exchange":round(exch,2),"sebi":round(sebi,2),
            "stamp":round(stamp,2),"gst":round(gst,2),"total":total}

# ══════════════════════════════════════════════════════════════════════════════
# MARKET REGIME DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def detect_live_regime(vix: float, spot_change_pct: float = 0,
                        is_expiry: bool = False, hour: int = 10) -> dict:
    """Detect current market regime from live conditions"""
    if is_expiry:
        regime = "EXPIRY"
        conf   = 90
    elif vix > 24:
        regime = "HIGH_VOL"
        conf   = 85
    elif vix < 12:
        regime = "LOW_VOL"
        conf   = 80
    elif abs(spot_change_pct) > 0.8:
        regime = "TRENDING"
        conf   = 75
    elif abs(spot_change_pct) < 0.2 and 10 <= hour <= 14:
        regime = "SIDEWAYS"
        conf   = 70
    elif abs(spot_change_pct) > 1.2:
        regime = "GAPDAY"
        conf   = 88
    else:
        regime = "NORMAL"
        conf   = 65

    strategy_bias = {
        "TRENDING":  "Directional — CE/PE momentum",
        "SIDEWAYS":  "Premium Selling — Iron Condor/Strangle",
        "HIGH_VOL":  "Reduce size — avoid OTM buys",
        "LOW_VOL":   "Buy options — IV cheap",
        "EXPIRY":    "Theta plays — Scalping",
        "GAPDAY":    "Gap fade — high caution",
        "NORMAL":    "Standard execution",
    }

    return {
        "regime":        regime,
        "vix":           vix,
        "confidence":    conf,
        "strategy_bias": strategy_bias.get(regime, ""),
        "is_expiry":     is_expiry,
        "hour":          hour,
    }

# ══════════════════════════════════════════════════════════════════════════════
# AI TRADE QUALITY SCORE
# ══════════════════════════════════════════════════════════════════════════════

def ai_trade_quality(instrument: str, option_data: dict, regime: dict,
                     capital: float, allocated: float,
                     consecutive_losses: int = 0) -> dict:
    """
    AI pre-trade quality score 0-100.
    Evaluates: liquidity, Greeks, regime, risk, momentum.
    """
    score   = 50
    reasons = []
    rejects = []

    # ── Regime score ────────────────────────────────────────────────
    rs = {"TRENDING":15,"NORMAL":10,"SIDEWAYS":-5,
          "HIGH_VOL":-10,"LOW_VOL":-5,"EXPIRY":8,"GAPDAY":-15}
    r_score = rs.get(regime["regime"], 0)
    score  += r_score
    if r_score > 0:
        reasons.append(f"Regime {regime['regime']} favourable")
    elif r_score < 0:
        rejects.append(f"Regime {regime['regime']} unfavourable")

    # ── VIX score ───────────────────────────────────────────────────
    vix = regime["vix"]
    if 12 <= vix <= 18:
        score += 12; reasons.append("VIX in ideal range")
    elif vix > 25:
        score -= 15; rejects.append("High VIX — elevated risk")
    elif vix < 10:
        score -= 8;  rejects.append("Very low VIX — low liquidity")

    # ── Delta score (prefer near-ATM) ───────────────────────────────
    delta = abs(option_data.get("delta", 0.5))
    if 0.35 <= delta <= 0.65:
        score += 10; reasons.append("Delta near ATM — ideal")
    elif delta < 0.20:
        score -= 12; rejects.append("Deep OTM — low probability")

    # ── Liquidity (spread relative to premium) ──────────────────────
    mid = option_data.get("mid", 100)
    ask = option_data.get("ask", 100)
    bid = option_data.get("bid", 99)
    spread_pct = (ask - bid) / max(mid, 1) * 100
    if spread_pct < 2:
        score += 8;  reasons.append("Tight spread — good liquidity")
    elif spread_pct > 8:
        score -= 10; rejects.append("Wide spread — poor liquidity")

    # ── Capital exposure check ───────────────────────────────────────
    exposure_pct = allocated / max(capital, 1) * 100
    if exposure_pct > 60:
        score -= 20; rejects.append(f"High exposure {exposure_pct:.0f}% — reduce size")
    elif exposure_pct < 30:
        score += 5;  reasons.append("Conservative exposure")

    # ── Consecutive loss penalty ─────────────────────────────────────
    if consecutive_losses >= 3:
        score -= 25; rejects.append(f"{consecutive_losses} consecutive losses — circuit breaker")
    elif consecutive_losses == 2:
        score -= 10; rejects.append("2 consecutive losses — caution")

    # ── Theta score (time decay) ─────────────────────────────────────
    theta = option_data.get("theta", 0)
    dte   = option_data.get("dte", 7)
    if dte <= 2 and theta < -5:
        score -= 8; rejects.append("Fast theta decay near expiry")
    elif dte >= 5:
        score += 5; reasons.append("Sufficient DTE")

    score = max(5, min(98, score))
    grade = "A+" if score>=85 else "A" if score>=75 else "B" if score>=65 else "C" if score>=50 else "D"

    # Trade decision
    if score >= 55 and consecutive_losses < 4:
        decision = "APPROVE"
    elif score >= 45:
        decision = "REDUCE_SIZE"
    else:
        decision = "REJECT"

    return {
        "score":     score,
        "grade":     grade,
        "decision":  decision,
        "reasons":   reasons,
        "rejects":   rejects,
        "explanation": f"Score {score}/100 ({grade}): " +
                       ("; ".join(reasons[:3]) if reasons else "No positive factors") +
                       (" | CAUTION: " + "; ".join(rejects[:2]) if rejects else ""),
    }

# ══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO GREEKS TRACKER
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PortfolioGreeks:
    net_delta: float = 0.0
    net_gamma: float = 0.0
    net_theta: float = 0.0
    net_vega:  float = 0.0
    total_delta_exposure: float = 0.0

    def add_position(self, delta: float, gamma: float, theta: float,
                     vega: float, lots: int, lot_size: int, spot: float):
        mult = lots * lot_size
        self.net_delta += delta * mult
        self.net_gamma += gamma * mult
        self.net_theta += theta * mult
        self.net_vega  += vega  * mult
        self.total_delta_exposure = abs(self.net_delta) * spot

    def remove_position(self, delta: float, gamma: float, theta: float,
                        vega: float, lots: int, lot_size: int, spot: float):
        mult = lots * lot_size
        self.net_delta -= delta * mult
        self.net_gamma -= gamma * mult
        self.net_theta -= theta * mult
        self.net_vega  -= vega  * mult
        self.total_delta_exposure = abs(self.net_delta) * spot

    def risk_status(self, capital: float) -> dict:
        delta_risk = abs(self.net_delta) * 100   # per 1 point move
        return {
            "net_delta": round(self.net_delta, 4),
            "net_gamma": round(self.net_gamma, 6),
            "net_theta": round(self.net_theta, 2),
            "net_vega":  round(self.net_vega,  2),
            "daily_theta_decay":  round(self.net_theta, 2),
            "delta_risk_per_pt":  round(delta_risk, 2),
            "delta_exposure":     round(self.total_delta_exposure, 2),
            "vega_risk_1pct_iv":  round(self.net_vega, 2),
            "portfolio_risk_pct": round(abs(self.net_theta) / max(capital,1) * 100, 3),
        }

# ══════════════════════════════════════════════════════════════════════════════
# RISK MANAGEMENT ENGINE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class RiskEngine:
    initial_capital: float
    capital:         float
    peak_capital:    float    = 0.0
    daily_pnl:       float    = 0.0
    total_pnl:       float    = 0.0
    max_drawdown:    float    = 0.0
    current_drawdown:float    = 0.0
    consecutive_losses: int   = 0
    trades_today:    int      = 0
    daily_loss_limit:float    = 0.0
    max_exposure_pct:float    = 0.60   # 60% max capital exposure
    emergency_mode:  bool     = False

    def __post_init__(self):
        self.peak_capital    = self.capital
        self.daily_loss_limit= self.capital * 0.02   # 2% daily loss limit

    def update(self, pnl: float):
        self.daily_pnl  += pnl
        self.total_pnl  += pnl
        self.capital    += pnl
        if self.capital > self.peak_capital:
            self.peak_capital = self.capital
        dd = (self.peak_capital - self.capital) / max(self.peak_capital, 1)
        self.current_drawdown = dd
        self.max_drawdown     = max(self.max_drawdown, dd)
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        self.trades_today += 1
        # Emergency mode
        if dd > 0.15 or self.consecutive_losses >= 4:
            self.emergency_mode = True
        elif dd < 0.08 and self.consecutive_losses < 2:
            self.emergency_mode = False

    def can_trade(self) -> Tuple[bool, str]:
        if self.emergency_mode:
            return False, "EMERGENCY MODE — capital protection active"
        if self.consecutive_losses >= 4:
            return False, "4 consecutive losses — circuit breaker triggered"
        if self.current_drawdown > 0.15:
            return False, f"Drawdown {self.current_drawdown*100:.1f}% exceeds 15% limit"
        if self.daily_pnl < -self.daily_loss_limit:
            return False, f"Daily loss limit ₹{self.daily_loss_limit:,.0f} reached"
        if self.trades_today >= 10:
            return False, "Max 10 trades per day reached"
        return True, "OK"

    def position_size_kelly(self, win_rate: float,
                            avg_win: float, avg_loss: float) -> float:
        """Half-Kelly position sizing"""
        if avg_loss == 0:
            return 0.01
        b     = avg_win / avg_loss
        p, q  = win_rate, 1 - win_rate
        kelly = (b * p - q) / b
        return max(0.01, min(0.04, kelly * 0.5))

    def max_lots_for_trade(self, lot_value: float,
                            win_rate: float = 0.65) -> int:
        kelly_frac = self.position_size_kelly(win_rate, 2000, 3000)
        capital_for_trade = self.capital * kelly_frac
        if self.emergency_mode:
            capital_for_trade *= 0.5
        return max(1, int(capital_for_trade / max(lot_value, 1)))

    def portfolio_var(self, positions: list, confidence: float = 0.95) -> float:
        """Simplified VaR: 1-day at 95% confidence"""
        if not positions:
            return 0
        total_exposure = sum(p.get("current_value", 0) for p in positions)
        vix = get_live_vix()
        daily_vol = (vix / 100) / math.sqrt(252)
        var_95 = total_exposure * daily_vol * 1.645
        return round(var_95, 2)

    def reset_daily(self):
        self.daily_pnl   = 0
        self.trades_today= 0

# ══════════════════════════════════════════════════════════════════════════════
# PAPER POSITION
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PaperPosition:
    pos_id:      str
    strategy:    str
    instrument:  str
    strike:      int
    option_type: str
    lots:        int
    lot_size:    int
    entry_price: float          # EXACT execution price
    entry_spot:  float          # Spot at entry
    entry_iv:    float
    entry_dte:   int
    entry_time:  str
    entry_greeks:dict = field(default_factory=dict)
    entry_charges:dict= field(default_factory=dict)
    entry_exec:  dict = field(default_factory=dict)
    quality_score:int = 0
    regime:      str  = "NORMAL"
    status:      str  = "OPEN"
    exit_price:  float= 0.0
    exit_time:   str  = ""
    exit_reason: str  = ""
    realized_pnl:float= 0.0
    slippage_cost:float=0.0
    total_charges:float=0.0
    audit_trail: list = field(default_factory=list)

    @property
    def current_value(self) -> float:
        return self.entry_price * self.lot_size * self.lots

    @property
    def trade_value(self) -> float:
        return self.entry_price * self.lot_size * self.lots

    def unrealized_pnl(self, current_price: float) -> float:
        return (current_price - self.entry_price) * self.lot_size * self.lots

    def log(self, event: str, data: dict = None):
        self.audit_trail.append({
            "time": datetime.now().isoformat(),
            "event": event,
            "data": data or {},
        })

    def to_dict(self) -> dict:
        return asdict(self)

# ══════════════════════════════════════════════════════════════════════════════
# PAPER TRADING EXECUTION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class PaperTradingEngine:
    """
    Institutional Paper Trading Engine
    Manages positions, risk, analytics, and execution simulation.
    """

    def __init__(self, user_id: str, capital: float = 500000):
        self.user_id   = user_id
        self.risk      = RiskEngine(initial_capital=capital, capital=capital)
        self.greeks    = PortfolioGreeks()
        self.positions : List[PaperPosition] = []
        self.closed    : List[PaperPosition] = []
        self.trade_log : List[dict]          = []
        self.session_start = datetime.now().isoformat()

    # ── Execute paper order ────────────────────────────────────────────
    def execute_order(self, instrument: str, strike: int,
                      option_type: str, lots: int,
                      strategy: str = "MANUAL",
                      strike_mode: str = "ATM",
                      dte: int = None) -> dict:
        """Full institutional execution pipeline"""

        # Paper trading works 24/7 (simulation)
        now  = datetime.now()
        hour = now.hour
        is_market_hours = NSE_OPEN[0] <= hour < NSE_CLOSE[0]
        is_holiday = str(date.today()) in NSE_HOLIDAYS
        # Note: Paper trading NOT restricted — simulate any time

        # Live market data
        spot = get_live_spot(instrument)
        vix  = get_live_vix()
        if dte is None:
            dte = get_next_expiry_dte()

        # Auto strike selection
        if strike == 0 or strike_mode != "MANUAL":
            strike = select_strike(instrument, option_type, strike_mode, spot=spot)

        # Live option pricing
        opt  = get_live_option_price(instrument, strike, option_type, dte, spot, vix)

        # Market regime
        is_expiry = (now.weekday() == 3)  # Thursday = expiry
        regime    = detect_live_regime(vix, 0, is_expiry, hour)

        # Allocated capital
        allocated = sum(p.current_value for p in self.positions if p.status == "OPEN")

        # AI quality score
        quality = ai_trade_quality(instrument, opt, regime,
                                   self.risk.capital, allocated,
                                   self.risk.consecutive_losses)

        # Risk check
        can_trade, risk_reason = self.risk.can_trade()
        if not can_trade:
            return {"success": False, "reason": risk_reason,
                    "quality": quality, "regime": regime}

        # AI decision override
        if quality["decision"] == "REJECT":
            return {"success": False, "reason": "AI rejected: " + quality["explanation"],
                    "quality": quality, "regime": regime}

        # Size reduction
        if quality["decision"] == "REDUCE_SIZE":
            lots = max(1, lots // 2)

        # Kelly-based lot cap
        max_lots = self.risk.max_lots_for_trade(opt["lot_value"])
        lots     = min(lots, max_lots, 50)  # Hard cap 50 lots

        # Execute
        exec_result = simulate_paper_execution(
            opt["mid"], lots, instrument, "BUY",
            regime["regime"], vix
        )

        if exec_result["rejected"]:
            return {"success": False, "reason": "Order rejected by exchange simulator",
                    "exec": exec_result}

        actual_lots = exec_result["filled_lots"]
        exec_price  = exec_result["exec_price"]

        # Charges
        charges = calculate_all_charges(exec_price, opt["lot_size"], actual_lots)

        # Build position
        pos = PaperPosition(
            pos_id       = f"PP_{self.user_id}_{int(time.time()*1000)}",
            strategy     = strategy,
            instrument   = instrument,
            strike       = strike,
            option_type  = option_type,
            lots         = actual_lots,
            lot_size     = opt["lot_size"],
            entry_price  = exec_price,
            entry_spot   = spot,
            entry_iv     = opt["iv"],
            entry_dte    = dte,
            entry_time   = now.isoformat(),
            entry_greeks = {k: opt[k] for k in ["delta","gamma","theta","vega"]},
            entry_charges= charges,
            entry_exec   = exec_result,
            quality_score= quality["score"],
            regime       = regime["regime"],
        )
        pos.slippage_cost  = exec_result["slippage_cost"]
        pos.total_charges  = charges["total"]
        pos.log("ENTRY", {"exec_price": exec_price, "lots": actual_lots,
                           "quality": quality["score"], "regime": regime["regime"]})

        self.positions.append(pos)

        # Update portfolio Greeks
        self.greeks.add_position(
            opt["delta"], opt["gamma"], opt["theta"], opt["vega"],
            actual_lots, opt["lot_size"], spot
        )

        # Charge capital
        self.risk.capital -= charges["total"] + exec_result["slippage_cost"]

        result = {
            "success": True,
            "pos_id":  pos.pos_id,
            "instrument": instrument,
            "strike":  strike,
            "option_type": option_type,
            "lots":    actual_lots,
            "exec_price": exec_price,
            "bid": opt["bid"], "ask": opt["ask"],
            "lot_value": round(exec_price * opt["lot_size"] * actual_lots, 2),
            "charges": charges["total"],
            "slippage": exec_result["slippage_cost"],
            "total_cost": round(charges["total"] + exec_result["slippage_cost"], 2),
            "greeks": {k: opt[k] for k in ["delta","gamma","theta","vega","iv"]},
            "quality": quality,
            "regime":  regime,
            "latency_ms": exec_result["latency_ms"],
            "fill_rate": exec_result["fill_rate"],
            "moneyness": opt["moneyness"],
            "dte": dte, "spot": spot,
            "capital_remaining": round(self.risk.capital, 2),
            "portfolio_greeks": self.greeks.risk_status(self.risk.capital),
        }

        self.trade_log.append({**result, "direction": "ENTRY",
                               "timestamp": now.isoformat()})
        return result

    # ── Close position ─────────────────────────────────────────────────
    def close_position(self, pos_id: str, exit_reason: str = "MANUAL") -> dict:
        pos = next((p for p in self.positions
                    if p.pos_id == pos_id and p.status == "OPEN"), None)
        if not pos:
            return {"success": False, "reason": "Position not found"}

        spot = get_live_spot(pos.instrument)
        vix  = get_live_vix()
        dte_remaining = max(1, pos.entry_dte - 1)
        opt  = get_live_option_price(pos.instrument, pos.strike,
                                     pos.option_type, dte_remaining, spot, vix)

        regime  = detect_live_regime(vix)
        ex_exec = simulate_paper_execution(
            opt["mid"], pos.lots, pos.instrument, "SELL",
            regime["regime"], vix
        )
        exit_price = ex_exec["exec_price"]

        charges = calculate_all_charges(exit_price, pos.lot_size, pos.lots)

        # P&L
        gross_pnl = (exit_price - pos.entry_price) * pos.lot_size * pos.lots
        total_cost= charges["total"] + ex_exec["slippage_cost"] + pos.total_charges
        net_pnl   = gross_pnl - total_cost

        pos.exit_price   = exit_price
        pos.exit_time    = datetime.now().isoformat()
        pos.exit_reason  = exit_reason
        pos.realized_pnl = round(net_pnl, 2)
        pos.total_charges += charges["total"]
        pos.slippage_cost += ex_exec["slippage_cost"]
        pos.status       = "CLOSED"
        pos.log("EXIT", {"exit_price": exit_price, "net_pnl": net_pnl,
                          "reason": exit_reason})

        # Update portfolio
        self.greeks.remove_position(
            pos.entry_greeks.get("delta",0),
            pos.entry_greeks.get("gamma",0),
            pos.entry_greeks.get("theta",0),
            pos.entry_greeks.get("vega",0),
            pos.lots, pos.lot_size, spot
        )
        self.risk.update(net_pnl)
        self.closed.append(pos)
        self.positions = [p for p in self.positions if p.pos_id != pos_id]

        return {
            "success":     True,
            "pos_id":      pos_id,
            "exit_price":  exit_price,
            "gross_pnl":   round(gross_pnl, 2),
            "net_pnl":     round(net_pnl, 2),
            "total_charges": round(total_cost, 2),
            "exit_reason": exit_reason,
            "capital":     round(self.risk.capital, 2),
        }

    # ── Get portfolio snapshot ─────────────────────────────────────────
    def get_portfolio(self) -> dict:
        spot_cache = {}
        open_pnl   = 0
        positions_data = []

        for pos in self.positions:
            if pos.status != "OPEN":
                continue
            if pos.instrument not in spot_cache:
                spot_cache[pos.instrument] = get_live_spot(pos.instrument)
            spot = spot_cache[pos.instrument]
            vix  = get_live_vix()
            dte  = max(1, pos.entry_dte - 1)
            opt  = get_live_option_price(pos.instrument, pos.strike,
                                          pos.option_type, dte, spot, vix)
            curr_price = opt["mid"]
            unreal     = pos.unrealized_pnl(curr_price)
            open_pnl  += unreal

            positions_data.append({
                "pos_id":      pos.pos_id,
                "strategy":    pos.strategy,
                "instrument":  pos.instrument,
                "strike":      pos.strike,
                "option_type": pos.option_type,
                "lots":        pos.lots,
                "entry_price": pos.entry_price,
                "current_price":curr_price,
                "unrealized_pnl": round(unreal, 2),
                "current_value":  round(curr_price * pos.lot_size * pos.lots, 2),
                "entry_time":  pos.entry_time,
                "regime":      pos.regime,
                "quality_score": pos.quality_score,
                "greeks":      opt,
                "status":      pos.status,
            })

        # Analytics from closed trades
        closed_pnls = [p.realized_pnl for p in self.closed]
        wins        = [p for p in closed_pnls if p > 0]
        losses      = [p for p in closed_pnls if p < 0]
        win_rate    = len(wins) / max(len(closed_pnls), 1) * 100

        return {
            "user_id":           self.user_id,
            "capital":           round(self.risk.capital, 2),
            "initial_capital":   self.risk.initial_capital,
            "total_pnl":         round(self.risk.total_pnl, 2),
            "open_unrealized":   round(open_pnl, 2),
            "daily_pnl":         round(self.risk.daily_pnl, 2),
            "open_positions":    positions_data,
            "total_trades":      len(self.closed),
            "win_rate":          round(win_rate, 2),
            "max_drawdown":      round(self.risk.max_drawdown * 100, 2),
            "consecutive_losses":self.risk.consecutive_losses,
            "emergency_mode":    self.risk.emergency_mode,
            "portfolio_greeks":  self.greeks.risk_status(self.risk.capital),
            "portfolio_var":     self.risk.portfolio_var(positions_data),
            "session_start":     self.session_start,
            "regime":            detect_live_regime(get_live_vix()),
        }

    # ── Analytics ──────────────────────────────────────────────────────
    def get_analytics(self) -> dict:
        if not self.closed:
            return {"message": "No closed trades yet"}

        pnls  = [p.realized_pnl for p in self.closed]
        wins  = [p for p in pnls if p > 0]
        losses= [p for p in pnls if p < 0]

        returns = [p.realized_pnl / max(self.risk.initial_capital, 1)
                   for p in self.closed]

        mean_r = sum(returns) / len(returns)
        var_r  = sum((r - mean_r)**2 for r in returns) / max(len(returns)-1, 1)
        std_r  = math.sqrt(var_r)
        rf     = 0.065 / 252
        sharpe = ((mean_r - rf) / std_r * math.sqrt(252)) if std_r > 0 else 0

        profit_factor = sum(wins) / max(abs(sum(losses)), 1)
        expectancy    = (sum(wins)/max(len(wins),1)*(len(wins)/len(pnls)) -
                         abs(sum(losses))/max(len(losses),1)*(len(losses)/len(pnls)))

        # Charge impact
        total_charges = sum(p.total_charges for p in self.closed)
        total_slip    = sum(p.slippage_cost for p in self.closed)

        # Quality distribution
        scores = [p.quality_score for p in self.closed]

        return {
            "total_trades":   len(self.closed),
            "winning_trades": len(wins),
            "losing_trades":  len([p for p in pnls if p < 0]),
            "win_rate":       round(len(wins)/len(pnls)*100, 2),
            "total_pnl":      round(sum(pnls), 2),
            "gross_profit":   round(sum(wins), 2),
            "gross_loss":     round(sum(losses), 2),
            "avg_win":        round(sum(wins)/max(len(wins),1), 2),
            "avg_loss":       round(abs(sum(losses))/max(len(losses),1), 2),
            "profit_factor":  round(profit_factor, 3),
            "expectancy":     round(expectancy, 2),
            "sharpe_ratio":   round(sharpe, 3),
            "max_drawdown":   round(self.risk.max_drawdown*100, 2),
            "total_charges":  round(total_charges, 2),
            "total_slippage": round(total_slip, 2),
            "avg_quality_score": round(sum(scores)/max(len(scores),1), 1),
            "charge_drag_pct": round(total_charges/max(abs(sum(pnls)),1)*100, 2),
        }

# ══════════════════════════════════════════════════════════════════════════════
# IN-MEMORY SESSION STORE (per user)
# ══════════════════════════════════════════════════════════════════════════════
_sessions: Dict[str, PaperTradingEngine] = {}

def get_session(user_id: str, capital: float = 500000) -> PaperTradingEngine:
    if user_id not in _sessions:
        _sessions[user_id] = PaperTradingEngine(user_id, capital)
    return _sessions[user_id]

def reset_session(user_id: str, capital: float = 500000):
    _sessions[user_id] = PaperTradingEngine(user_id, capital)
    return _sessions[user_id]

