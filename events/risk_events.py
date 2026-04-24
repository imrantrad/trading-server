"""Risk & Position Events"""
from .event_bus import bus, Event, EventType


class RiskEventHandler:
    def __init__(self):
        self.positions = {}
        self.daily_pnl = 0
        self.total_pnl = 0
        self.drawdown = 0
        self.peak = 500000
        bus.subscribe(EventType.POSITION_OPEN, self.on_position_open, priority=1)
        bus.subscribe(EventType.POSITION_CLOSE, self.on_position_close)
        bus.subscribe(EventType.POSITION_UPDATE, self.on_position_update)
        bus.subscribe(EventType.SL_HIT, self.on_sl_hit, priority=1)
        bus.subscribe(EventType.TARGET_HIT, self.on_target_hit, priority=1)
        bus.subscribe(EventType.PNL_UPDATE, self.on_pnl_update)
        bus.subscribe(EventType.RISK_BREACH, self.on_risk_breach, priority=1)
        bus.subscribe(EventType.KILL_SWITCH, self.on_kill_switch, priority=1)

    def on_position_open(self, event: Event):
        pos = event.data
        pos_id = pos.get("order_id") or pos.get("position_id")
        if pos_id:
            self.positions[pos_id] = {**pos, "status": "OPEN", "pnl": 0}
        bus.emit(EventType.LOG, {"type":"INFO", "msg": f"Position opened: {pos.get('instrument')} {pos.get('action')}"})

    def on_position_close(self, event: Event):
        pos = event.data
        pos_id = pos.get("position_id")
        pnl = pos.get("net_pnl", 0)
        self.daily_pnl += pnl
        self.total_pnl += pnl
        if pos_id in self.positions:
            del self.positions[pos_id]
        bus.emit(EventType.PNL_UPDATE, {"daily_pnl": self.daily_pnl, "total_pnl": self.total_pnl})
        bus.emit(EventType.LOG, {"type":"SUCCESS" if pnl>=0 else "ERROR",
            "msg": f"Position closed P&L: ₹{pnl:+.0f}"})

    def on_position_update(self, event: Event):
        pos_id = event.data.get("position_id")
        if pos_id in self.positions:
            self.positions[pos_id].update(event.data)

    def on_sl_hit(self, event: Event):
        bus.emit(EventType.LOG, {"type":"WARN",
            "msg": f"SL HIT: {event.data.get('instrument')} @ {event.data.get('price')}"})
        bus.emit(EventType.POSITION_CLOSE, event.data, source="SL_ENGINE")

    def on_target_hit(self, event: Event):
        bus.emit(EventType.LOG, {"type":"SUCCESS",
            "msg": f"TARGET HIT: {event.data.get('instrument')} @ {event.data.get('price')}"})
        bus.emit(EventType.POSITION_CLOSE, event.data, source="TARGET_ENGINE")

    def on_pnl_update(self, event: Event):
        daily = event.data.get("daily_pnl", 0)
        total = event.data.get("total_pnl", 0)
        capital = 500000 + total
        if capital > self.peak:
            self.peak = capital
        self.drawdown = (self.peak - capital) / self.peak * 100

        # Risk breach checks
        if abs(daily) > 500000 * 0.03:
            bus.emit(EventType.DAILY_LOSS_LIM, {"daily_pnl": daily}, source="RISK")
        if self.drawdown > 10:
            bus.emit(EventType.DRAWDOWN_ALERT, {"drawdown": self.drawdown}, source="RISK")

    def on_risk_breach(self, event: Event):
        breach = event.data.get("type", "UNKNOWN")
        bus.emit(EventType.LOG, {"type":"ERROR", "msg": f"RISK BREACH: {breach}"})
        # Auto-trigger kill switch on severe breach
        if event.data.get("severity") == "CRITICAL":
            bus.emit(EventType.KILL_SWITCH, {"reason": breach}, source="RISK_MANAGER")

    def on_kill_switch(self, event: Event):
        reason = event.data.get("reason", "Manual")
        bus.emit(EventType.LOG, {"type":"ERROR", "msg": f"KILL SWITCH: {reason} — All trading halted"})
        # Cancel all pending orders
        bus.emit(EventType.ALERT, {"level":"CRITICAL", "msg": f"Trading halted: {reason}"})


risk_event_handler = RiskEventHandler()
