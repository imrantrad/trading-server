"""Portfolio Tracker v12.3"""
from dataclasses import dataclass, field
from typing import Dict, List
import time


@dataclass
class PortfolioPosition:
    instrument: str; action: str; quantity: int; lot_size: int
    avg_price: float; current_price: float
    strategy: str = ""; option_type: str = ""
    strike: int = 0; expiry: str = ""
    is_hedge: bool = False; delta: float = 0
    pnl: float = 0; pnl_pct: float = 0
    added_time: str = ""

    def update(self, price):
        self.current_price = price
        m = 1 if self.action == "BUY" else -1
        self.pnl = m * (price - self.avg_price) * self.quantity * self.lot_size
        base = self.avg_price * self.quantity * self.lot_size
        self.pnl_pct = round(self.pnl / base * 100, 2) if base else 0


class PortfolioTracker:
    def __init__(self, capital: float = 500000):
        self.capital = capital
        self.initial_capital = capital
        self.positions: Dict[str, PortfolioPosition] = {}
        self.closed_trades: List[dict] = []
        self.daily_pnl = 0; self.total_pnl = 0

    def add_position(self, pos: PortfolioPosition) -> str:
        pid = f"{pos.instrument}_{pos.option_type}_{pos.strike}_{int(time.time())}"
        pos.added_time = time.strftime("%H:%M:%S")
        self.positions[pid] = pos
        return pid

    def close_position(self, pid: str, exit_price: float, reason: str = "MANUAL") -> dict:
        if pid not in self.positions: return {}
        pos = self.positions[pid]
        pos.update(exit_price)
        result = {"instrument":pos.instrument,"action":pos.action,
                  "pnl":round(pos.pnl,0),"exit_price":exit_price,
                  "reason":reason,"time":time.strftime("%H:%M:%S")}
        self.total_pnl += pos.pnl; self.daily_pnl += pos.pnl
        self.closed_trades.append(result)
        del self.positions[pid]
        return result

    def update_all(self, prices: Dict[str, float]):
        for pos in self.positions.values():
            if pos.instrument in prices:
                pos.update(prices[pos.instrument])

    def get_summary(self) -> dict:
        unrealized = sum(p.pnl for p in self.positions.values())
        net_delta = sum(p.delta * p.quantity for p in self.positions.values())
        hedge_pnl = sum(p.pnl for p in self.positions.values() if p.is_hedge)
        return {
            "total_positions": len(self.positions),
            "unrealized_pnl": round(unrealized, 0),
            "realized_pnl": round(self.total_pnl, 0),
            "total_pnl": round(unrealized + self.total_pnl, 0),
            "net_delta": round(net_delta, 2),
            "hedge_positions": sum(1 for p in self.positions.values() if p.is_hedge),
            "hedge_pnl": round(hedge_pnl, 0),
            "capital": round(self.capital + self.total_pnl, 0),
        }


portfolio = PortfolioTracker()
