"""
Risk Management Engine v12.3
Complete institutional-grade risk management
"""
from dataclasses import dataclass
from typing import Dict, Optional
import math


@dataclass
class RiskParams:
    capital: float = 500000
    risk_per_trade: float = 0.01       # 1%
    max_daily_loss: float = 0.03       # 3%
    max_drawdown: float = 0.10         # 10%
    max_positions: int = 5
    max_trades_per_day: int = 10
    max_correlated_positions: int = 2
    max_sector_exposure: float = 0.30


class RiskManager:
    def __init__(self, params: RiskParams = None):
        self.params = params or RiskParams()
        self.daily_loss = 0.0
        self.current_drawdown = 0.0
        self.open_positions = 0
        self.trades_today = 0
        self.consecutive_losses = 0
        self.is_trading_allowed = True
        self.kill_switch = False

    # ── POSITION SIZING ──────────────────────────
    def fixed_fractional(self, sl_points: float, lot_size: int = 50) -> int:
        risk_amt = self.params.capital * self.params.risk_per_trade
        lot_risk = sl_points * lot_size
        return max(1, int(risk_amt / lot_risk)) if lot_risk > 0 else 1

    def kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        if avg_loss == 0: return 0
        q = 1 - win_rate
        b = avg_win / abs(avg_loss)
        kelly = (b * win_rate - q) / b
        return max(0, min(kelly * 0.5, 0.25))  # Half Kelly, capped at 25%

    def volatility_sizing(self, atr: float, lot_size: int = 50) -> int:
        risk_amt = self.params.capital * self.params.risk_per_trade
        atr_risk = atr * lot_size * 2
        return max(1, int(risk_amt / atr_risk)) if atr_risk > 0 else 1

    def optimal_f(self, losses: list) -> float:
        if not losses: return 0.02
        max_loss = abs(min(losses)) if losses else 1
        f_values = [i/100 for i in range(1, 51)]
        best_f, best_twp = 0.02, 0
        for f in f_values:
            twp = 1.0
            for pnl in losses:
                twp *= (1 + f * pnl / max_loss)
                if twp <= 0:
                    twp = 0
                    break
            if twp > best_twp:
                best_twp = twp
                best_f = f
        return best_f

    # ── STOP LOSS CALCULATORS ─────────────────────
    def atr_stop(self, entry: float, atr: float, multiplier: float = 2.0, action: str = "BUY") -> float:
        if action == "BUY":
            return round(entry - (atr * multiplier), 2)
        return round(entry + (atr * multiplier), 2)

    def swing_stop(self, swing_level: float, buffer: float = 5) -> float:
        return swing_level - buffer

    def chandelier_stop(self, highest_high: float, atr: float, multiplier: float = 3.0) -> float:
        return round(highest_high - (atr * multiplier), 2)

    def volatility_stop(self, entry: float, std_dev: float, multiplier: float = 2.0, action: str = "BUY") -> float:
        if action == "BUY":
            return round(entry - (std_dev * multiplier), 2)
        return round(entry + (std_dev * multiplier), 2)

    def percent_stop(self, entry: float, pct: float = 1.0, action: str = "BUY") -> float:
        if action == "BUY":
            return round(entry * (1 - pct/100), 2)
        return round(entry * (1 + pct/100), 2)

    # ── TARGET CALCULATORS ────────────────────────
    def rr_target(self, entry: float, sl: float, rr: float = 2.0, action: str = "BUY") -> float:
        risk = abs(entry - sl)
        if action == "BUY":
            return round(entry + (risk * rr), 2)
        return round(entry - (risk * rr), 2)

    def fib_target(self, entry: float, sl: float, fib_level: float = 1.618) -> float:
        risk = abs(entry - sl)
        return round(entry + (risk * fib_level), 2)

    def measured_move(self, pattern_size: float, breakout_level: float) -> float:
        return round(breakout_level + pattern_size, 2)

    # ── RISK CHECKS ───────────────────────────────
    def check_trade(self, order: dict) -> dict:
        """Full risk check before trade"""
        violations = []

        if self.kill_switch:
            return {"allowed": False, "reason": "KILL SWITCH ACTIVE"}

        if not self.is_trading_allowed:
            return {"allowed": False, "reason": "Trading paused - risk limit breached"}

        if self.trades_today >= self.params.max_trades_per_day:
            violations.append(f"Daily trade limit: {self.params.max_trades_per_day}")

        if abs(self.daily_loss) >= self.params.capital * self.params.max_daily_loss:
            violations.append(f"Daily loss limit: {self.params.max_daily_loss*100}%")
            self.is_trading_allowed = False

        if self.current_drawdown >= self.params.max_drawdown * 100:
            violations.append(f"Max drawdown: {self.params.max_drawdown*100}%")
            self.is_trading_allowed = False

        if self.open_positions >= self.params.max_positions:
            violations.append(f"Max positions: {self.params.max_positions}")

        if self.consecutive_losses >= 3:
            violations.append("3 consecutive losses - review required")

        if violations:
            return {"allowed": False, "violations": violations}

        return {"allowed": True, "message": "Risk check passed"}

    def calculate_position_size(self, method: str, **kwargs) -> dict:
        """Calculate position size by method"""
        lot_size = kwargs.get("lot_size", 50)
        sl_points = kwargs.get("sl_points", 100)
        atr = kwargs.get("atr", 100)
        win_rate = kwargs.get("win_rate", 0.5)
        avg_win = kwargs.get("avg_win", 200)
        avg_loss = kwargs.get("avg_loss", -100)

        if method == "FIXED_FRACTIONAL":
            lots = self.fixed_fractional(sl_points, lot_size)
        elif method == "KELLY":
            f = self.kelly_criterion(win_rate, avg_win, avg_loss)
            risk_amt = self.params.capital * f
            lots = max(1, int(risk_amt / (sl_points * lot_size)))
        elif method == "VOLATILITY":
            lots = self.volatility_sizing(atr, lot_size)
        else:
            lots = 1

        risk_amt = lots * sl_points * lot_size
        risk_pct = risk_amt / self.params.capital * 100

        return {
            "method": method,
            "lots": lots,
            "risk_amount": risk_amt,
            "risk_percent": round(risk_pct, 2),
            "capital": self.params.capital,
        }

    def get_risk_report(self) -> dict:
        return {
            "capital": self.params.capital,
            "daily_loss": round(self.daily_loss, 0),
            "daily_loss_limit": round(self.params.capital * self.params.max_daily_loss, 0),
            "daily_loss_used_pct": round(abs(self.daily_loss)/(self.params.capital*self.params.max_daily_loss)*100, 1) if self.daily_loss < 0 else 0,
            "current_drawdown_pct": round(self.current_drawdown, 2),
            "max_drawdown_limit_pct": round(self.params.max_drawdown*100, 1),
            "open_positions": self.open_positions,
            "max_positions": self.params.max_positions,
            "trades_today": self.trades_today,
            "max_trades_today": self.params.max_trades_per_day,
            "consecutive_losses": self.consecutive_losses,
            "trading_allowed": self.is_trading_allowed,
            "kill_switch": self.kill_switch,
            "risk_status": "GREEN" if self.is_trading_allowed and not self.kill_switch else "RED",
        }


risk_manager = RiskManager()
