"""Angel One Broker"""
from .base_broker import BaseBroker, BrokerOrder, BrokerPosition
from typing import List


class AngelBroker(BaseBroker):
    def __init__(self, api_key: str = "", client_id: str = "", pin: str = ""):
        super().__init__(api_key)
        self.client_id = client_id; self.pin = pin
        self.base_url = "https://apiconnect.angelbroking.com"

    def login(self) -> bool:
        if not self.api_key: return False
        self.is_connected = True
        return True

    def place_order(self, order: BrokerOrder) -> dict:
        if not self.is_connected:
            return {"status": "ERROR", "reason": "Not connected"}
        return {"status": "SIMULATED", "broker": "ANGEL",
                "instrument": order.instrument, "action": order.action}

    def cancel_order(self, order_id: str) -> bool: return True
    def get_positions(self) -> List[BrokerPosition]: return []
    def get_ltp(self, instrument: str) -> float: return 0.0
    def get_order_status(self, order_id: str) -> dict: return {"status": "COMPLETE"}
