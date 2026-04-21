def parse_strategy(text: str):
    strategy = {}
    t = text.lower()
    if 'nifty' in t:
        strategy['instrument'] = 'NIFTY'
    if 'buy' in t:
        strategy['action'] = 'BUY'
    if 'sell' in t:
        strategy['action'] = 'SELL'
    strategy['confidence'] = 0.92
    return strategy
