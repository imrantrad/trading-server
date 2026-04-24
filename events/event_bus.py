"""
Event-Driven Architecture Core v12.3
Central Event Bus — all system components communicate through events
"""
import asyncio, time, uuid, json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
from datetime import datetime
from collections import defaultdict, deque


# ═══════════════════════════════════════
# EVENT TYPES
# ═══════════════════════════════════════
class EventType(str, Enum):
    # Market Data
    TICK           = "TICK"
    BAR            = "BAR"
    ORDERBOOK      = "ORDERBOOK"
    MARKET_OPEN    = "MARKET_OPEN"
    MARKET_CLOSE   = "MARKET_CLOSE"
    CIRCUIT_BREAK  = "CIRCUIT_BREAK"

    # Signal
    SIGNAL_BUY     = "SIGNAL_BUY"
    SIGNAL_SELL    = "SIGNAL_SELL"
    SIGNAL_EXIT    = "SIGNAL_EXIT"
    SIGNAL_HEDGE   = "SIGNAL_HEDGE"
    NLP_PARSED     = "NLP_PARSED"

    # Order
    ORDER_CREATED  = "ORDER_CREATED"
    ORDER_SENT     = "ORDER_SENT"
    ORDER_FILLED   = "ORDER_FILLED"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_CANCELLED= "ORDER_CANCELLED"
    ORDER_PARTIAL  = "ORDER_PARTIAL"

    # Position
    POSITION_OPEN  = "POSITION_OPEN"
    POSITION_CLOSE = "POSITION_CLOSE"
    POSITION_UPDATE= "POSITION_UPDATE"
    SL_HIT         = "SL_HIT"
    TARGET_HIT     = "TARGET_HIT"
    TRAIL_SL_UPDATE= "TRAIL_SL_UPDATE"

    # Risk
    RISK_CHECK     = "RISK_CHECK"
    RISK_BREACH    = "RISK_BREACH"
    DAILY_LOSS_LIM = "DAILY_LOSS_LIMIT"
    DRAWDOWN_ALERT = "DRAWDOWN_ALERT"
    KILL_SWITCH    = "KILL_SWITCH"
    MARGIN_CALL    = "MARGIN_CALL"

    # Strategy
    STRATEGY_START = "STRATEGY_START"
    STRATEGY_STOP  = "STRATEGY_STOP"
    STRATEGY_ERROR = "STRATEGY_ERROR"
    BACKTEST_START = "BACKTEST_START"
    BACKTEST_END   = "BACKTEST_END"

    # Portfolio
    PNL_UPDATE     = "PNL_UPDATE"
    REBALANCE      = "REBALANCE"
    HEDGE_REQUIRED = "HEDGE_REQUIRED"

    # System
    SYSTEM_START   = "SYSTEM_START"
    SYSTEM_STOP    = "SYSTEM_STOP"
    ERROR          = "ERROR"
    LOG            = "LOG"
    ALERT          = "ALERT"
    NOTIFICATION   = "NOTIFICATION"


# ═══════════════════════════════════════
# BASE EVENT
# ═══════════════════════════════════════
@dataclass
class Event:
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S.%f")[:-3])
    source: str = "SYSTEM"
    priority: int = 5  # 1=highest, 10=lowest

    def to_dict(self):
        return {"id":self.id,"type":self.type,"data":self.data,
                "timestamp":self.timestamp,"source":self.source,"priority":self.priority}


# ═══════════════════════════════════════
# EVENT BUS
# ═══════════════════════════════════════
class EventBus:
    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._wildcard: List[Callable] = []  # subscribe to ALL events
        self._history: deque = deque(maxlen=max_history)
        self._stats: Dict[str, int] = defaultdict(int)
        self._filters: Dict[EventType, List[Callable]] = defaultdict(list)
        self._middlewares: List[Callable] = []
        self.running = True

    def subscribe(self, event_type: EventType, handler: Callable, priority: int = 5):
        """Subscribe to specific event type"""
        self._subscribers[event_type].append((priority, handler))
        self._subscribers[event_type].sort(key=lambda x: x[0])

    def subscribe_all(self, handler: Callable):
        """Subscribe to ALL events"""
        self._wildcard.append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable):
        self._subscribers[event_type] = [
            (p,h) for p,h in self._subscribers[event_type] if h != handler
        ]

    def add_middleware(self, middleware: Callable):
        """Add middleware for all events (logging, validation, etc.)"""
        self._middlewares.append(middleware)

    def add_filter(self, event_type: EventType, filter_fn: Callable):
        """Add filter — return False to block event"""
        self._filters[event_type].append(filter_fn)

    def publish(self, event: Event) -> bool:
        """Publish event synchronously"""
        if not self.running:
            return False

        # Run through middlewares
        for mw in self._middlewares:
            try:
                result = mw(event)
                if result is False:
                    return False
            except Exception as e:
                print(f"Middleware error: {e}")

        # Check filters
        for f in self._filters.get(event.type, []):
            try:
                if not f(event):
                    return False
            except Exception as e:
                print(f"Filter error: {e}")

        # Record history
        self._history.append(event.to_dict())
        self._stats[event.type] += 1

        # Notify specific subscribers
        for _, handler in self._subscribers.get(event.type, []):
            try:
                handler(event)
            except Exception as e:
                print(f"Handler error [{event.type}]: {e}")

        # Notify wildcard subscribers
        for handler in self._wildcard:
            try:
                handler(event)
            except Exception as e:
                print(f"Wildcard handler error: {e}")

        return True

    def emit(self, event_type: EventType, data: dict = None,
             source: str = "SYSTEM", priority: int = 5) -> bool:
        """Shorthand for publish"""
        return self.publish(Event(
            type=event_type,
            data=data or {},
            source=source,
            priority=priority
        ))

    def get_history(self, event_type: EventType = None, limit: int = 100) -> List[dict]:
        history = list(self._history)
        if event_type:
            history = [e for e in history if e["type"] == event_type]
        return history[-limit:]

    def get_stats(self) -> dict:
        return dict(self._stats)

    def clear_history(self):
        self._history.clear()

    def stop(self):
        self.running = False


# Global event bus instance
bus = EventBus()
