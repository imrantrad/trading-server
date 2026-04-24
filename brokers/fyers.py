"""Fyers Broker"""
from .base_broker import BaseBroker, BrokerOrder, BrokerPosition
from typing import List


class FyersBroker(BaseBroker):
    def __init__(self, client_id: str = "", access_token: str = ""):
        super().__init__(client_id)
        self.client_id = client_id; self.access_token = access_token
        self.base_url = "https://api.fyers.in/api/v2"

    def login(self) -> bool:
        if not self.client_id: return False
        self.is_connected = True
        return True

    def place_order(self, order: BrokerOrder) -> dict:
        if not self.is_connected:
            return {"status": "ERROR", "reason": "Not connected"}
        return {"status": "SIMULATED", "broker": "FYERS",
                "instrument": order.instrument, "action": order.action}

    def cancel_order(self, order_id: str) -> bool: return True
    def get_positions(self) -> List[BrokerPosition]: return []
    def get_ltp(self, instrument: str) -> float: return 0.0
    def get_order_status(self, order_id: str) -> dict: return {"status": "COMPLETE"}
