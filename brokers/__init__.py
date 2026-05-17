"""Brokers module — production uses angel_one.py for live trading"""
from .angel_one import (
    login,
    get_live_quote,
    get_all_live_prices,
    get_option_chain,
    place_order,
    get_portfolio,
    get_order_book,
)

# Legacy get_broker stub for backwards compatibility
class _StubBroker:
    """Legacy stub — use angel_one functions directly"""
    def __init__(self, **kwargs):
        self.config = kwargs
        self.is_connected = False
    def login(self): return False
    def place_order(self, order): return {"error": "Use angel_one directly"}

def get_broker(name: str, **kwargs):
    """Legacy compat: returns stub. Use angel_one.* directly in new code."""
    return _StubBroker(**kwargs)

__all__ = ['login', 'get_live_quote', 'get_all_live_prices', 'get_option_chain',
           'place_order', 'get_portfolio', 'get_order_book', 'get_broker']
