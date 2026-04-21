class RiskEngine:
    def validate(self, strategy):
        return strategy.get('confidence', 0) >= 0.9
