class BacktestEngine:
    def run(self, strategy, data):
        pnl = 0
        for _ in data:
            pnl += 10
        return {'pnl': pnl}
