from brokers.zerodha import ZerodhaBroker
from brokers.angel import AngelBroker
from brokers.fyers import FyersBroker

class ExecutionRouter:
    def __init__(self):
        self.active = 'ZERODHA'
        self.brokers = {
            'ZERODHA': ZerodhaBroker(),
            'ANGEL': AngelBroker(),
            'FYERS': FyersBroker()
        }

    def execute(self, order):
        return self.brokers[self.active].place_order(order)
