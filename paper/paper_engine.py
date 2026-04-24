"""
Paper Trading Engine v12.3
Complete simulation with P&L, positions, trade log
"""
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class Position:
    id: str
    instrument: str
    action: str           # BUY/SELL
    option_type: str      # CE/PE/FUT/EQ
    strike: Optional[int]
    expiry: str
    quantity: int
    lot_size: int
    entry_price: float
    current_price: float
    stoploss: Optional[float]
    target: Optional[float]
    trailing_sl: Optional[float]
    strategy: Optional[str]
    entry_time: str
    status: str           # OPEN/CLOSED/SL_HIT/TARGET_HIT
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    exit_reason: Optional[str] = None

    def update_pnl(self, current_price: float):
        self.current_price = current_price
        multiplier = 1 if self.action == "BUY" else -1
        self.pnl = multiplier * (current_price - self.entry_price) * self.quantity * self.lot_size
        if self.entry_price > 0:
            self.pnl_pct = round((self.pnl / (self.entry_price * self.quantity * self.lot_size)) * 100, 2)

    def check_sl_target(self) -> Optional[str]:
        if self.action == "BUY":
            if self.stoploss and self.current_price <= self.stoploss:
                return "SL_HIT"
            if self.target and self.current_price >= self.target:
                return "TARGET_HIT"
        else:
            if self.stoploss and self.current_price >= self.stoploss:
                return "SL_HIT"
            if self.target and self.current_price <= self.target:
                return "TARGET_HIT"
        return None


@dataclass
class Trade:
    id: str
    instrument: str
    action: str
    option_type: str
    strike: Optional[int]
    expiry: str
    quantity: int
    lot_size: int
    entry_price: float
    exit_price: float
    entry_time: str
    exit_time: str
    exit_reason: str
    strategy: Optional[str]
    pnl: float
    pnl_pct: float
    brokerage: float
    net_pnl: float
    broker: str


class PaperTradingEngine:
    def __init__(self, capital: float = 500000, brokerage: float = 20, slippage: float = 2):
        self.capital = capital
        self.initial_capital = capital
        self.brokerage = brokerage
        self.slippage = slippage

        self.positions: Dict[str, Position] = {}
        self.trade_log: List[Trade] = []
        self.daily_pnl: float = 0.0
        self.total_pnl: float = 0.0
        self.peak_capital: float = capital
        self.max_drawdown: float = 0.0

        # Statistics
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.losing_trades: int = 0
        self.consecutive_losses: int = 0
        self.max_consecutive_losses: int = 0

        # Risk limits
        self.daily_loss_limit: float = capital * 0.03
        self.max_trades_per_day: int = 10
        self.trades_today: int = 0
        self.daily_loss: float = 0.0

    def open_position(self, order: dict) -> dict:
        """Open a new paper trade position"""

        # Risk checks
        if self.trades_today >= self.max_trades_per_day:
            return {"status": "REJECTED", "reason": "Daily trade limit reached"}
        if abs(self.daily_loss) >= self.daily_loss_limit:
            return {"status": "REJECTED", "reason": "Daily loss limit breached"}
        if len(self.positions) >= 5:
            return {"status": "REJECTED", "reason": "Max open positions reached"}

        instrument = order.get("instrument", "NIFTY")
        lot_size = {"NIFTY":50,"BANKNIFTY":15,"FINNIFTY":40,"MIDCPNIFTY":75,"SENSEX":10}.get(instrument, 50)
        quantity = order.get("quantity", 1)
        entry_price = order.get("entry_price", 0) + self.slippage

        # Calculate margin required (simplified)
        margin = entry_price * quantity * lot_size * 0.15

        if margin > self.capital * 0.5:
            return {"status": "REJECTED", "reason": "Insufficient margin"}

        pos_id = f"POS{int(time.time()*1000)%1000000:06d}"

        # Calculate SL/Target in price terms
        stoploss = None
        target = None
        risk_metrics = order.get("risk_metrics", {})

        if risk_metrics.get("stoploss_points"):
            sl_pts = risk_metrics["stoploss_points"]
            if order.get("action") == "BUY":
                stoploss = entry_price - sl_pts
                if risk_metrics.get("target_points"):
                    target = entry_price + risk_metrics["target_points"]
            else:
                stoploss = entry_price + sl_pts
                if risk_metrics.get("target_points"):
                    target = entry_price - risk_metrics["target_points"]

        position = Position(
            id=pos_id,
            instrument=instrument,
            action=order.get("action", "BUY"),
            option_type=order.get("option_type", "CE"),
            strike=order.get("strike"),
            expiry=order.get("expiry", "WEEKLY"),
            quantity=quantity,
            lot_size=lot_size,
            entry_price=entry_price,
            current_price=entry_price,
            stoploss=stoploss,
            target=target,
            trailing_sl=risk_metrics.get("trailing_sl"),
            strategy=order.get("strategy"),
            entry_time=datetime.now().strftime("%H:%M:%S"),
            status="OPEN",
        )

        self.positions[pos_id] = position
        self.capital -= margin
        self.trades_today += 1
        self.total_trades += 1

        return {
            "status": "EXECUTED",
            "position_id": pos_id,
            "entry_price": entry_price,
            "quantity": quantity,
            "lot_size": lot_size,
            "margin_used": margin,
            "stoploss": stoploss,
            "target": target,
            "capital_remaining": self.capital,
        }

    def close_position(self, pos_id: str, exit_price: float, reason: str = "MANUAL") -> dict:
        """Close an open position"""
        if pos_id not in self.positions:
            return {"status": "ERROR", "reason": "Position not found"}

        pos = self.positions[pos_id]
        exit_price_adj = exit_price - self.slippage if pos.action == "BUY" else exit_price + self.slippage

        pos.update_pnl(exit_price_adj)
        pos.exit_price = exit_price_adj
        pos.exit_time = datetime.now().strftime("%H:%M:%S")
        pos.exit_reason = reason
        pos.status = reason

        gross_pnl = pos.pnl
        net_pnl = gross_pnl - self.brokerage

        # Update engine stats
        self.daily_pnl += net_pnl
        self.total_pnl += net_pnl
        self.daily_loss += min(0, net_pnl)
        margin_returned = exit_price_adj * pos.quantity * pos.lot_size * 0.15
        self.capital += margin_returned + net_pnl

        if net_pnl > 0:
            self.winning_trades += 1
            self.consecutive_losses = 0
        else:
            self.losing_trades += 1
            self.consecutive_losses += 1
            self.max_consecutive_losses = max(self.max_consecutive_losses, self.consecutive_losses)

        # Update drawdown
        self.peak_capital = max(self.peak_capital, self.capital)
        dd = (self.peak_capital - self.capital) / self.peak_capital * 100
        self.max_drawdown = max(self.max_drawdown, dd)

        # Log trade
        trade = Trade(
            id=f"TRD{len(self.trade_log)+1:04d}",
            instrument=pos.instrument,
            action=pos.action,
            option_type=pos.option_type,
            strike=pos.strike,
            expiry=pos.expiry,
            quantity=pos.quantity,
            lot_size=pos.lot_size,
            entry_price=pos.entry_price,
            exit_price=exit_price_adj,
            entry_time=pos.entry_time,
            exit_time=pos.exit_time,
            exit_reason=reason,
            strategy=pos.strategy,
            pnl=gross_pnl,
            pnl_pct=pos.pnl_pct,
            brokerage=self.brokerage,
            net_pnl=net_pnl,
            broker="PAPER",
        )
        self.trade_log.append(trade)
        del self.positions[pos_id]

        return {
            "status": "CLOSED",
            "position_id": pos_id,
            "exit_price": exit_price_adj,
            "gross_pnl": gross_pnl,
            "brokerage": self.brokerage,
            "net_pnl": net_pnl,
            "exit_reason": reason,
        }

    def get_stats(self) -> dict:
        """Get complete trading statistics"""
        total = self.total_trades
        wins = self.winning_trades
        losses = self.losing_trades
        win_rate = round((wins/total*100) if total>0 else 0, 1)

        trade_pnls = [t.net_pnl for t in self.trade_log]
        avg_win = round(sum(p for p in trade_pnls if p>0)/(wins or 1), 0)
        avg_loss = round(sum(p for p in trade_pnls if p<0)/(losses or 1), 0)
        profit_factor = round(abs(avg_win*wins)/(abs(avg_loss)*losses+1), 2)
        expectancy = round((win_rate/100 * avg_win) + ((1-win_rate/100) * avg_loss), 0)

        return {
            "capital": round(self.capital, 0),
            "initial_capital": self.initial_capital,
            "total_pnl": round(self.total_pnl, 0),
            "daily_pnl": round(self.daily_pnl, 0),
            "total_pnl_pct": round(self.total_pnl/self.initial_capital*100, 2),
            "total_trades": total,
            "winning_trades": wins,
            "losing_trades": losses,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "max_drawdown_pct": round(self.max_drawdown, 2),
            "max_consecutive_losses": self.max_consecutive_losses,
            "open_positions": len(self.positions),
            "trades_today": self.trades_today,
            "daily_loss": round(self.daily_loss, 0),
        }

    def update_prices(self, prices: dict):
        """Update all open position prices and check SL/Target"""
        closed = []
        for pos_id, pos in self.positions.items():
            if pos.instrument in prices:
                current = prices[pos.instrument]
                pos.update_pnl(current)
                # Check trailing SL
                if pos.trailing_sl and pos.action == "BUY":
                    new_sl = current - pos.trailing_sl
                    if pos.stoploss is None or new_sl > pos.stoploss:
                        pos.stoploss = new_sl
                # Check SL/Target
                reason = pos.check_sl_target()
                if reason:
                    closed.append((pos_id, current, reason))

        for pos_id, price, reason in closed:
            self.close_position(pos_id, price, reason)

        return closed

# Global paper engine instance
paper_engine = PaperTradingEngine()
