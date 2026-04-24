"""Order Lifecycle Events"""
from .event_bus import bus, Event, EventType
import time


class OrderHandler:
    def __init__(self):
        self.orders = {}
        self.filled_orders = []
        bus.subscribe(EventType.ORDER_CREATED, self.on_order_created, priority=1)
        bus.subscribe(EventType.ORDER_SENT, self.on_order_sent)
        bus.subscribe(EventType.ORDER_FILLED, self.on_order_filled)
        bus.subscribe(EventType.ORDER_REJECTED, self.on_order_rejected)

    def on_order_created(self, event: Event):
        order = event.data
        order_id = f"ORD{int(time.time()*1000)%1000000:06d}"
        order["order_id"] = order_id
        order["status"] = "CREATED"
        self.orders[order_id] = order
        bus.emit(EventType.ORDER_SENT, order, source="ORDER_HANDLER")

    def on_order_sent(self, event: Event):
        order = event.data
        order["status"] = "SENT"
        # Paper: immediately fill
        bus.emit(EventType.ORDER_FILLED, {
            **order,
            "fill_price": order.get("entry_price", 0),
            "status": "FILLED"
        }, source="PAPER_BROKER")

    def on_order_filled(self, event: Event):
        order = event.data
        self.filled_orders.append(order)
        bus.emit(EventType.POSITION_OPEN, order, source="ORDER_HANDLER")
        bus.emit(EventType.LOG, {
            "type": "SUCCESS",
            "msg": f"FILLED: {order.get('instrument')} {order.get('action')} @ {order.get('fill_price',0)}"
        })

    def on_order_rejected(self, event: Event):
        order = event.data
        bus.emit(EventType.LOG, {
            "type": "ERROR",
            "msg": f"REJECTED: {order.get('reason','Unknown')}"
        })


order_handler = OrderHandler()
