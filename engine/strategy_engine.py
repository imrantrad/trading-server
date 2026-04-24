"""
Strategy Automation Engine v12.3
Auto-trading based on signals and conditions
"""
import time, threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum


class StrategyState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


@dataclass
class StrategyConfig:
    name: str
    instrument: str = "NIFTY"
    timeframe: str = "5MIN"
    max_positions: int = 1
    quantity: int = 1
    sl_pct: float = 1.0
    target_pct: float = 2.0
    entry_conditions: List[str] = field(default_factory=list)
    exit_conditions: List[str] = field(default_factory=list)
    active_hours: str = "09:20-15:00"
    auto_execute: bool = False
    mode: str = "PAPER"


@dataclass
class StrategyPerformance:
    trades: int = 0
    wins: int = 0
    losses: int = 0
    pnl: float = 0
    win_rate: float = 0
    last_signal: str = ""
    last_signal_time: str = ""
    state: str = "IDLE"


class StrategyEngine:
    def __init__(self):
        self.strategies: Dict[str, StrategyConfig] = {}
        self.performance: Dict[str, StrategyPerformance] = {}
        self.signals: List[dict] = []
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []
        self._market_data: Dict[str, float] = {}
        self._indicators: Dict[str, dict] = {}

    def add_strategy(self, config: StrategyConfig) -> str:
        sid = f"STR_{config.name.upper().replace(' ','_')}"
        self.strategies[sid] = config
        self.performance[sid] = StrategyPerformance()
        return sid

    def remove_strategy(self, sid: str):
        self.strategies.pop(sid, None)
        self.performance.pop(sid, None)

    def pause_strategy(self, sid: str):
        if sid in self.performance:
            self.performance[sid].state = "PAUSED"

    def resume_strategy(self, sid: str):
        if sid in self.performance:
            self.performance[sid].state = "RUNNING"

    def on_signal(self, callback: Callable):
        self._callbacks.append(callback)

    def update_market_data(self, prices: dict, indicators: dict = None):
        self._market_data.update(prices)
        if indicators:
            self._indicators.update(indicators)
        self._evaluate_all()

    def _evaluate_all(self):
        for sid, config in self.strategies.items():
            perf = self.performance[sid]
            if perf.state == "PAUSED": continue
            signal = self._evaluate_strategy(sid, config)
            if signal:
                perf.last_signal = signal["action"]
                perf.last_signal_time = time.strftime("%H:%M:%S")
                self.signals.append(signal)
                for cb in self._callbacks:
                    try: cb(signal)
                    except: pass

    def _evaluate_strategy(self, sid: str, config: StrategyConfig) -> Optional[dict]:
        price = self._market_data.get(config.instrument, 0)
        if not price: return None
        indicators = self._indicators.get(config.instrument, {})
        rsi = indicators.get("rsi", 50)
        ema9 = indicators.get("ema9", price)
        ema21 = indicators.get("ema21", price)
        vix = self._market_data.get("VIX", 15)

        signal = None
        # Default strategy: EMA cross + RSI filter
        if config.name == "EMA_CROSS_RSI":
            if ema9 > ema21 and rsi < 60: signal = "BUY"
            elif ema9 < ema21 and rsi > 40: signal = "SELL"
        elif config.name == "RSI_OVERSOLD":
            if rsi < 30: signal = "BUY"
            elif rsi > 70: signal = "SELL"
        elif config.name == "STRADDLE_ON_VIX":
            if vix > 15: signal = "STRADDLE"
        elif config.name == "MEAN_REVERSION":
            if rsi < 25: signal = "BUY"
            elif rsi > 75: signal = "SELL"

        if signal:
            return {
                "strategy_id": sid,
                "strategy_name": config.name,
                "instrument": config.instrument,
                "action": signal,
                "price": price,
                "quantity": config.quantity,
                "mode": config.mode,
                "auto_execute": config.auto_execute,
                "timestamp": time.strftime("%H:%M:%S"),
                "conditions_met": {"rsi": rsi, "ema9": ema9, "ema21": ema21},
            }
        return None

    def get_all_status(self) -> List[dict]:
        result = []
        for sid, config in self.strategies.items():
            perf = self.performance[sid]
            result.append({
                "id": sid, "name": config.name,
                "instrument": config.instrument,
                "state": perf.state,
                "trades": perf.trades, "pnl": perf.pnl,
                "wins": perf.wins, "losses": perf.losses,
                "last_signal": perf.last_signal,
                "last_signal_time": perf.last_signal_time,
                "auto_execute": config.auto_execute,
                "mode": config.mode,
            })
        return result

    def get_recent_signals(self, limit: int = 20) -> List[dict]:
        return self.signals[-limit:]


# Built-in strategies
BUILTIN_STRATEGIES = [
    {"name":"EMA_CROSS_RSI","desc":"EMA 9/21 crossover with RSI filter",
     "conditions":["ema9 > ema21","rsi < 60"],"timeframe":"15MIN"},
    {"name":"RSI_OVERSOLD","desc":"RSI mean reversion",
     "conditions":["rsi < 30"],"timeframe":"5MIN"},
    {"name":"VWAP_BOUNCE","desc":"Buy at VWAP support",
     "conditions":["price > vwap","rsi < 50"],"timeframe":"5MIN"},
    {"name":"STRADDLE_ON_VIX","desc":"Buy straddle when VIX spikes",
     "conditions":["vix > 15","iv_rank > 50"],"timeframe":"1DAY"},
    {"name":"IRON_CONDOR_RANGE","desc":"Sell IC when market sideways",
     "conditions":["rangebound","iv_rank > 40"],"timeframe":"1DAY"},
    {"name":"BREAKOUT_MOMENTUM","desc":"Buy breakout with volume",
     "conditions":["breakout","volume_surge","rsi > 50"],"timeframe":"15MIN"},
    {"name":"MEAN_REVERSION","desc":"Extreme RSI reversal",
     "conditions":["rsi < 25 or rsi > 75"],"timeframe":"1HOUR"},
    {"name":"SUPERTREND","desc":"Supertrend trend following",
     "conditions":["supertrend_buy"],"timeframe":"15MIN"},
    {"name":"OPENING_RANGE","desc":"First 15 min breakout",
     "conditions":["orb_breakout","volume > avg"],"timeframe":"15MIN"},
    {"name":"GAP_FADE","desc":"Fade gap up/down",
     "conditions":["gap > 0.5%","vwap_rejection"],"timeframe":"5MIN"},
]

strategy_engine = StrategyEngine()
