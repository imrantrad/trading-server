# Trading System v12.3 - Configuration

# Mode: PAPER | LIVE | BACKTEST
MODE = "PAPER"

# Active Broker
BROKER = "ZERODHA"

# Risk Settings
MAX_RISK_PER_TRADE = 0.01      # 1% of capital per trade
MAX_DAILY_LOSS = 0.03          # 3% daily loss limit
MAX_DRAWDOWN = 0.10            # 10% max drawdown
MAX_TRADES_PER_DAY = 10
MAX_OPEN_POSITIONS = 5
CAPITAL = 500000               # Starting capital

# Lot Sizes
LOT_SIZES = {
    "NIFTY": 50, "BANKNIFTY": 15, "FINNIFTY": 40,
    "MIDCPNIFTY": 75, "SENSEX": 10,
}

# Broker APIs (fill before live trading)
ZERODHA_API_KEY = ""
ZERODHA_ACCESS_TOKEN = ""
ANGEL_API_KEY = ""
ANGEL_CLIENT_ID = ""
FYERS_CLIENT_ID = ""
FYERS_ACCESS_TOKEN = ""

# Paper Trading
PAPER_CAPITAL = 500000
PAPER_SLIPPAGE = 2             # points
PAPER_BROKERAGE = 20           # per order

# Notifications
TELEGRAM_TOKEN = ""
TELEGRAM_CHAT_ID = ""
