from .zerodha import ZerodhaBroker
from .angel import AngelBroker
from .fyers import FyersBroker
from .base_broker import BaseBroker, BrokerOrder

BROKERS = {"ZERODHA": ZerodhaBroker, "ANGEL": AngelBroker, "FYERS": FyersBroker}

def get_broker(name: str, **kwargs) -> BaseBroker:
    cls = BROKERS.get(name.upper(), ZerodhaBroker)
    return cls(**kwargs)
