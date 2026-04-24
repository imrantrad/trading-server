"""Signal Events — NLP/Strategy signals flow through here"""
from .event_bus import bus, Event, EventType


class SignalHandler:
    def __init__(self):
        self.signals = []
        self.pending_signals = []
        bus.subscribe(EventType.NLP_PARSED, self.on_nlp_parsed)
        bus.subscribe(EventType.SIGNAL_BUY, self.on_signal)
        bus.subscribe(EventType.SIGNAL_SELL, self.on_signal)
        bus.subscribe(EventType.SIGNAL_HEDGE, self.on_hedge_signal)

    def on_nlp_parsed(self, event: Event):
        parsed = event.data
        action = parsed.get("action", "BUY")
        signal_type = EventType.SIGNAL_BUY if action == "BUY" else EventType.SIGNAL_SELL
        # Emit as trade signal
        bus.emit(signal_type, {
            **parsed,
            "source": "NLP",
            "confirmed": parsed.get("confidence", 0) >= 0.75
        }, source="NLP_ENGINE")

    def on_signal(self, event: Event):
        signal = event.data
        self.signals.append(signal)
        if signal.get("confirmed"):
            # Forward to order handler
            bus.emit(EventType.ORDER_CREATED, signal, source="SIGNAL_HANDLER")
        bus.emit(EventType.LOG, {
            "type": "SIGNAL",
            "msg": f"Signal: {event.type} {signal.get('instrument')} conf:{signal.get('confidence',0)}"
        })

    def on_hedge_signal(self, event: Event):
        hedge = event.data
        self.signals.append({**hedge, "is_hedge": True})
        bus.emit(EventType.ORDER_CREATED, {**hedge, "is_hedge": True}, source="HEDGE_ENGINE")


signal_handler = SignalHandler()
