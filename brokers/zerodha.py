"""Zerodha Kite Connect Broker"""
from .base_broker import BaseBroker, BrokerOrder, BrokerPosition
from typing import List


class ZerodhaBroker(BaseBroker):
    def __init__(self, api_key: str = "", access_token: str = ""):
        super().__init__(api_key)
        self.access_token = access_token
        self.base_url = "https://api.kite.trade"

    def login(self) -> bool:
        if not self.api_key or not self.access_token:
            return False
        # kite = KiteConnect(api_key=self.api_key)
        # kite.set_access_token(self.access_token)
        self.is_connected = True
        return True

    def place_order(self, order: BrokerOrder) -> dict:
        if not self.is_connected:
            return {"status": "ERROR", "reason": "Not connected"}
        # Real implementation:
        # order_id = kite.place_order(
        #     tradingsymbol=order.instrument,
        #     exchange=order.exchange,
        #     transaction_type=order.action,
        #     quantity=order.quantity,
        #     product=order.product,
        #     order_type=order.order_type,
        #     price=order.price,
        # )
        return {"status": "SIMULATED", "broker": "ZERODHA",
                "instrument": order.instrument, "action": order.action}

    def cancel_order(self, order_id: str) -> bool:
        return True

    def get_positions(self) -> List[BrokerPosition]:
        return []

    def get_ltp(self, instrument: str) -> float:
        return 0.0

    def get_order_status(self, order_id: str) -> dict:
        return {"order_id": order_id, "status": "COMPLETE"}
