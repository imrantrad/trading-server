"""Order Management System v12.3"""
import time, uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class OrderStatus(str, Enum):
    PENDING="PENDING"; SENT="SENT"; FILLED="FILLED"
    PARTIAL="PARTIAL"; REJECTED="REJECTED"; CANCELLED="CANCELLED"

class OrderType(str, Enum):
    MARKET="MARKET"; LIMIT="LIMIT"; SL="SL"; SL_M="SL-M"


@dataclass
class Order:
    id: str = field(default_factory=lambda: f"ORD{int(time.time()*1000)%1000000:06d}")
    instrument: str = "NIFTY"; action: str = "BUY"
    option_type: str = "CE"; strike: int = 0; expiry: str = "WEEKLY"
    quantity: int = 1; lot_size: int = 50
    order_type: OrderType = OrderType.MARKET
    price: float = 0; trigger_price: float = 0
    stoploss: Optional[float] = None; target: Optional[float] = None
    trailing_sl: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    fill_price: float = 0; fill_time: str = ""
    broker: str = "PAPER"; mode: str = "PAPER"
    strategy: str = ""; is_hedge: bool = False
    parent_order_id: str = ""; tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: time.strftime("%H:%M:%S"))
    notes: str = ""


class OrderManager:
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.pending: List[str] = []
        self.filled: List[str] = []

    def create(self, **kwargs) -> Order:
        order = Order(**kwargs)
        self.orders[order.id] = order
        self.pending.append(order.id)
        return order

    def submit(self, order_id: str, broker=None) -> dict:
        order = self.orders.get(order_id)
        if not order: return {"status":"ERROR","reason":"Order not found"}
        order.status = OrderStatus.SENT
        # Paper: instant fill
        order.fill_price = order.price or 100.0
        order.fill_time = time.strftime("%H:%M:%S")
        order.status = OrderStatus.FILLED
        self.pending.remove(order_id) if order_id in self.pending else None
        self.filled.append(order_id)
        return {"status":"FILLED","order_id":order_id,"fill_price":order.fill_price}

    def cancel(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            self.pending.remove(order_id) if order_id in self.pending else None
            return True
        return False

    def cancel_all(self) -> int:
        count = 0
        for oid in list(self.pending):
            if self.cancel(oid): count+=1
        return count

    def modify(self, order_id: str, price: float=None, sl: float=None, tgt: float=None) -> bool:
        order = self.orders.get(order_id)
        if not order: return False
        if price: order.price = price
        if sl: order.stoploss = sl
        if tgt: order.target = tgt
        return True

    def get_order(self, order_id: str) -> Optional[dict]:
        order = self.orders.get(order_id)
        return self._to_dict(order) if order else None

    def get_all(self, status: str = None) -> List[dict]:
        orders = list(self.orders.values())
        if status: orders = [o for o in orders if o.status == status]
        return [self._to_dict(o) for o in orders]

    def get_pending(self) -> List[dict]:
        return [self._to_dict(self.orders[oid]) for oid in self.pending if oid in self.orders]

    def get_stats(self) -> dict:
        all_orders = list(self.orders.values())
        return {
            "total": len(all_orders),
            "filled": len([o for o in all_orders if o.status==OrderStatus.FILLED]),
            "pending": len(self.pending),
            "rejected": len([o for o in all_orders if o.status==OrderStatus.REJECTED]),
            "cancelled": len([o for o in all_orders if o.status==OrderStatus.CANCELLED]),
        }

    def _to_dict(self, o: Order) -> dict:
        return {"id":o.id,"instrument":o.instrument,"action":o.action,
                "option_type":o.option_type,"strike":o.strike,"expiry":o.expiry,
                "quantity":o.quantity,"lot_size":o.lot_size,
                "order_type":o.order_type,"price":o.price,"fill_price":o.fill_price,
                "stoploss":o.stoploss,"target":o.target,"trailing_sl":o.trailing_sl,
                "status":o.status,"broker":o.broker,"mode":o.mode,
                "strategy":o.strategy,"is_hedge":o.is_hedge,
                "created_at":o.created_at,"fill_time":o.fill_time,"notes":o.notes}


oms = OrderManager()
