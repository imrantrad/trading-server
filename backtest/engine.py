"""
Backtest Engine v12.3
Walk-forward, Monte Carlo, Strategy testing on historical data
"""
import math, random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta


@dataclass
class Candle:
    timestamp: str
    open: float; high: float; low: float; close: float
    volume: int = 0

    @property
    def body(self): return abs(self.close - self.open)
    @property
    def upper_wick(self): return self.high - max(self.open, self.close)
    @property
    def lower_wick(self): return min(self.open, self.close) - self.low
    @property
    def is_bullish(self): return self.close > self.open


@dataclass
class BacktestTrade:
    id: int
    instrument: str
    action: str
    entry_price: float
    exit_price: float
    entry_bar: int
    exit_bar: int
    quantity: int
    lot_size: int
    pnl: float
    pnl_pct: float
    exit_reason: str
    strategy: str
    duration_bars: int


@dataclass
class BacktestResult:
    strategy: str
    instrument: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0
    total_pnl: float = 0
    gross_profit: float = 0
    gross_loss: float = 0
    profit_factor: float = 0
    avg_win: float = 0
    avg_loss: float = 0
    max_drawdown: float = 0
    max_drawdown_pct: float = 0
    sharpe_ratio: float = 0
    sortino_ratio: float = 0
    calmar_ratio: float = 0
    expectancy: float = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    avg_trade_duration: float = 0
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    monthly_returns: Dict[str, float] = field(default_factory=dict)


class BacktestEngine:
    def __init__(self):
        self.capital = 500000
        self.lot_size = 50
        self.brokerage = 40

    def generate_sample_data(self, instrument: str = "NIFTY",
                              bars: int = 252, start_price: float = 22000) -> List[Candle]:
        """Generate synthetic OHLCV data"""
        candles = []
        price = start_price
        base_date = datetime(2024, 1, 1, 9, 15)
        for i in range(bars):
            dt = base_date + timedelta(days=i)
            if dt.weekday() >= 5:
                continue
            daily_vol = price * 0.012
            open_p = price * (1 + random.gauss(0, 0.003))
            high_p = open_p + abs(random.gauss(0, daily_vol * 0.5))
            low_p = open_p - abs(random.gauss(0, daily_vol * 0.5))
            close_p = random.gauss((open_p + high_p + low_p) / 3, daily_vol * 0.2)
            close_p = max(low_p, min(high_p, close_p))
            volume = random.randint(100000, 2000000)
            candles.append(Candle(
                timestamp=dt.strftime("%Y-%m-%d"),
                open=round(open_p, 2), high=round(high_p, 2),
                low=round(low_p, 2), close=round(close_p, 2), volume=volume
            ))
            price = close_p
        return candles

    def compute_ema(self, prices: List[float], period: int) -> List[Optional[float]]:
        ema = [None] * len(prices)
        k = 2 / (period + 1)
        for i, p in enumerate(prices):
            if i < period - 1:
                continue
            if i == period - 1:
                ema[i] = sum(prices[:period]) / period
            else:
                ema[i] = p * k + ema[i-1] * (1 - k)
        return ema

    def compute_rsi(self, prices: List[float], period: int = 14) -> List[Optional[float]]:
        rsi = [None] * len(prices)
        if len(prices) < period + 1:
            return rsi
        for i in range(period, len(prices)):
            gains = [max(0, prices[j] - prices[j-1]) for j in range(i-period+1, i+1)]
            losses = [max(0, prices[j-1] - prices[j]) for j in range(i-period+1, i+1)]
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            if avg_loss == 0:
                rsi[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi[i] = round(100 - (100 / (1 + rs)), 2)
        return rsi

    def compute_atr(self, candles: List[Candle], period: int = 14) -> List[Optional[float]]:
        atr = [None] * len(candles)
        trs = []
        for i, c in enumerate(candles):
            if i == 0:
                trs.append(c.high - c.low)
            else:
                prev = candles[i-1].close
                tr = max(c.high - c.low, abs(c.high - prev), abs(c.low - prev))
                trs.append(tr)
        for i in range(period - 1, len(trs)):
            atr[i] = round(sum(trs[i-period+1:i+1]) / period, 2)
        return atr

    def compute_bollinger(self, prices: List[float], period: int = 20, std: float = 2):
        upper = [None] * len(prices)
        lower = [None] * len(prices)
        mid = [None] * len(prices)
        for i in range(period - 1, len(prices)):
            window = prices[i-period+1:i+1]
            m = sum(window) / period
            s = math.sqrt(sum((x - m) ** 2 for x in window) / period)
            mid[i] = round(m, 2)
            upper[i] = round(m + std * s, 2)
            lower[i] = round(m - std * s, 2)
        return upper, mid, lower

    def run_strategy(self, strategy_name: str, candles: List[Candle],
                     quantity: int = 1, sl_pct: float = 1.0,
                     target_pct: float = 2.0) -> BacktestResult:
        result = BacktestResult(strategy=strategy_name, instrument="NIFTY")
        closes = [c.close for c in candles]
        ema9 = self.compute_ema(closes, 9)
        ema21 = self.compute_ema(closes, 21)
        ema50 = self.compute_ema(closes, 50)
        rsi = self.compute_rsi(closes, 14)
        atr = self.compute_atr(candles, 14)
        bb_up, bb_mid, bb_low = self.compute_bollinger(closes, 20, 2)

        capital = self.capital
        equity = [capital]
        peak = capital
        max_dd = 0
        trade_id = 0
        position = None
        consec_wins = consec_losses = 0
        max_consec_w = max_consec_l = 0
        cur_consec_w = cur_consec_l = 0

        for i in range(50, len(candles)):
            c = candles[i]
            price = c.close

            # Check exits first
            if position:
                pnl = 0
                exit_reason = None
                if position["action"] == "BUY":
                    if price <= position["sl"]:
                        pnl = (price - position["entry"]) * quantity * self.lot_size
                        exit_reason = "SL_HIT"
                    elif price >= position["target"]:
                        pnl = (price - position["entry"]) * quantity * self.lot_size
                        exit_reason = "TARGET_HIT"
                else:
                    if price >= position["sl"]:
                        pnl = (position["entry"] - price) * quantity * self.lot_size
                        exit_reason = "SL_HIT"
                    elif price <= position["target"]:
                        pnl = (position["entry"] - price) * quantity * self.lot_size
                        exit_reason = "TARGET_HIT"

                if exit_reason:
                    net_pnl = pnl - self.brokerage
                    capital += net_pnl
                    equity.append(capital)
                    peak = max(peak, capital)
                    dd = (peak - capital) / peak * 100
                    max_dd = max(max_dd, dd)

                    trade = BacktestTrade(
                        id=trade_id, instrument="NIFTY",
                        action=position["action"],
                        entry_price=position["entry"],
                        exit_price=price,
                        entry_bar=position["bar"],
                        exit_bar=i,
                        quantity=quantity,
                        lot_size=self.lot_size,
                        pnl=round(net_pnl, 0),
                        pnl_pct=round(net_pnl/capital*100, 2),
                        exit_reason=exit_reason,
                        strategy=strategy_name,
                        duration_bars=i-position["bar"]
                    )
                    result.trades.append(trade)
                    trade_id += 1
                    result.total_trades += 1

                    if net_pnl > 0:
                        result.winning_trades += 1
                        result.gross_profit += net_pnl
                        cur_consec_w += 1; cur_consec_l = 0
                        max_consec_w = max(max_consec_w, cur_consec_w)
                    else:
                        result.losing_trades += 1
                        result.gross_loss += abs(net_pnl)
                        cur_consec_l += 1; cur_consec_w = 0
                        max_consec_l = max(max_consec_l, cur_consec_l)

                    position = None

            # Entry signals
            if not position:
                signal = None
                sl = 0; tgt = 0

                if strategy_name == "EMA_CROSS":
                    if ema9[i] and ema21[i] and ema9[i-1] and ema21[i-1]:
                        if ema9[i-1] <= ema21[i-1] and ema9[i] > ema21[i]:
                            signal = "BUY"
                        elif ema9[i-1] >= ema21[i-1] and ema9[i] < ema21[i]:
                            signal = "SELL"

                elif strategy_name == "RSI_MEAN_REVERSION":
                    if rsi[i]:
                        if rsi[i] < 30: signal = "BUY"
                        elif rsi[i] > 70: signal = "SELL"

                elif strategy_name == "BOLLINGER_BREAKOUT":
                    if bb_up[i] and bb_low[i]:
                        if price > bb_up[i]: signal = "SELL"
                        elif price < bb_low[i]: signal = "BUY"

                elif strategy_name == "EMA_RSI_COMBO":
                    if ema9[i] and ema21[i] and rsi[i]:
                        if ema9[i] > ema21[i] and rsi[i] < 40: signal = "BUY"
                        elif ema9[i] < ema21[i] and rsi[i] > 60: signal = "SELL"

                elif strategy_name == "SUPERTREND_LIKE":
                    if atr[i]:
                        up = c.high - 3 * atr[i]
                        if c.close > up: signal = "BUY"
                        else: signal = "SELL"

                if signal and atr[i]:
                    sl_pts = atr[i] * 2
                    tgt_pts = sl_pts * (target_pct / sl_pct)
                    if signal == "BUY":
                        sl = price - sl_pts
                        tgt = price + tgt_pts
                    else:
                        sl = price + sl_pts
                        tgt = price - tgt_pts
                    position = {"action":signal,"entry":price,"sl":sl,"target":tgt,"bar":i}

        # Final stats
        result.total_pnl = round(capital - self.capital, 0)
        result.win_rate = round(result.winning_trades / max(result.total_trades, 1) * 100, 1)
        result.profit_factor = round(result.gross_profit / max(result.gross_loss, 1), 2)
        result.avg_win = round(result.gross_profit / max(result.winning_trades, 1), 0)
        result.avg_loss = round(-result.gross_loss / max(result.losing_trades, 1), 0)
        result.max_drawdown = round(max_dd, 2)
        result.max_consecutive_wins = max_consec_w
        result.max_consecutive_losses = max_consec_l
        result.equity_curve = [round(e, 0) for e in equity[-50:]]
        result.expectancy = round(
            (result.win_rate/100 * result.avg_win) +
            ((1-result.win_rate/100) * result.avg_loss), 0)

        # Sharpe (simplified)
        if len(equity) > 2:
            returns = [(equity[i]-equity[i-1])/equity[i-1] for i in range(1,len(equity))]
            avg_r = sum(returns)/len(returns)
            std_r = math.sqrt(sum((r-avg_r)**2 for r in returns)/len(returns)) if len(returns)>1 else 1
            result.sharpe_ratio = round(avg_r/std_r*math.sqrt(252), 2) if std_r > 0 else 0

        return result

    def monte_carlo(self, trades: List[float], simulations: int = 1000,
                    capital: float = 500000) -> dict:
        """Monte Carlo simulation on trade results"""
        if not trades:
            return {}
        results = []
        for _ in range(simulations):
            sim_trades = random.choices(trades, k=len(trades))
            cap = capital
            peak = capital
            max_dd = 0
            for pnl in sim_trades:
                cap += pnl
                peak = max(peak, cap)
                dd = (peak - cap) / peak * 100
                max_dd = max(max_dd, dd)
            results.append({"final_capital": cap, "total_pnl": cap-capital, "max_dd": max_dd})
        results.sort(key=lambda x: x["final_capital"])
        pnls = [r["total_pnl"] for r in results]
        dds = [r["max_dd"] for r in results]
        return {
            "simulations": simulations,
            "p10_pnl": round(pnls[int(len(pnls)*0.10)], 0),
            "p25_pnl": round(pnls[int(len(pnls)*0.25)], 0),
            "p50_pnl": round(pnls[int(len(pnls)*0.50)], 0),
            "p75_pnl": round(pnls[int(len(pnls)*0.75)], 0),
            "p90_pnl": round(pnls[int(len(pnls)*0.90)], 0),
            "avg_max_dd": round(sum(dds)/len(dds), 2),
            "worst_dd": round(max(dds), 2),
            "probability_profit": round(len([r for r in results if r["total_pnl"]>0])/simulations*100, 1),
        }

    def walk_forward(self, strategy: str, candles: List[Candle],
                     train_pct: float = 0.7) -> dict:
        """Walk-forward analysis"""
        split = int(len(candles) * train_pct)
        train = candles[:split]
        test = candles[split:]
        train_result = self.run_strategy(strategy, train)
        test_result = self.run_strategy(strategy, test)
        return {
            "strategy": strategy,
            "train_period": f"{train[0].timestamp} to {train[-1].timestamp}",
            "test_period": f"{test[0].timestamp} to {test[-1].timestamp}",
            "train_pnl": train_result.total_pnl,
            "test_pnl": test_result.total_pnl,
            "train_win_rate": train_result.win_rate,
            "test_win_rate": test_result.win_rate,
            "train_trades": train_result.total_trades,
            "test_trades": test_result.total_trades,
            "robustness": round(test_result.total_pnl / max(abs(train_result.total_pnl), 1), 2),
            "verdict": "ROBUST" if test_result.total_pnl > 0 else "OVERFIT",
        }


backtest_engine = BacktestEngine()
