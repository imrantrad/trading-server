"""Market Data Event Handlers"""
from .event_bus import bus, Event, EventType
from datetime import datetime


class MarketDataHandler:
    def __init__(self):
        self.latest_prices = {}
        self.ohlcv = {}
        self.vix = 0
        self.market_open = False
        bus.subscribe(EventType.TICK, self.on_tick)
        bus.subscribe(EventType.MARKET_OPEN, self.on_market_open)
        bus.subscribe(EventType.MARKET_CLOSE, self.on_market_close)

    def on_tick(self, event: Event):
        instrument = event.data.get("instrument")
        price = event.data.get("price")
        if instrument:
            self.latest_prices[instrument] = price
            if instrument == "VIX":
                self.vix = price

    def on_market_open(self, event: Event):
        self.market_open = True
        bus.emit(EventType.LOG, {"msg": "Market opened", "time": event.timestamp})

    def on_market_close(self, event: Event):
        self.market_open = False
        bus.emit(EventType.LOG, {"msg": "Market closed"})

    def publish_tick(self, instrument: str, price: float, volume: int = 0):
        bus.emit(EventType.TICK, {
            "instrument": instrument,
            "price": price,
            "volume": volume,
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3]
        }, source="MARKET")

    def get_price(self, instrument: str) -> float:
        return self.latest_prices.get(instrument, 0)


market_handler = MarketDataHandler()
