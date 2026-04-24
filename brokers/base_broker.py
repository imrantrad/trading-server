"""Base Broker Interface"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class BrokerOrder:
    instrument: str; action: str; quantity: int
    order_type: str = "MARKET"  # MARKET/LIMIT/SL/SL-M
    price: float = 0; trigger_price: float = 0
    product: str = "MIS"  # MIS/NRML/CNC
    validity: str = "DAY"
    exchange: str = "NFO"
    order_id: Optional[str] = None
    status: Optional[str] = None


@dataclass
class BrokerPosition:
    instrument: str; action: str; quantity: int
    avg_price: float; ltp: float; pnl: float
    product: str; exchange: str


class BaseBroker(ABC):
    def __init__(self, api_key: str = "", secret: str = ""):
        self.api_key = api_key; self.secret = secret
        self.is_connected = False; self.access_token = ""

    @abstractmethod
    def login(self) -> bool: pass

    @abstractmethod
    def place_order(self, order: BrokerOrder) -> dict: pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool: pass

    @abstractmethod
    def get_positions(self) -> List[BrokerPosition]: pass

    @abstractmethod
    def get_ltp(self, instrument: str) -> float: pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> dict: pass

    def place_bracket_order(self, order: BrokerOrder, sl: float, target: float) -> dict:
        """Place order with SL and Target"""
        result = self.place_order(order)
        return {**result, "sl": sl, "target": target, "type": "BRACKET"}
