"""
TRD ML Engine v1.0
Real XGBoost + feature engineering on simulated market data.
In production: replace generate_features() with real NSE tick data.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
import hashlib, math, random

# ── Try importing ML libs ─────────────────────────────────────────────────────
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    HAS_SKL = True
except ImportError:
    HAS_SKL = False

IST = timezone(timedelta(hours=5, minutes=30))

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

def generate_ohlcv(symbol: str, days: int = 365, seed: int = None) -> pd.DataFrame:
    """
    Generate deterministic OHLCV data.
    Production: replace with real NSE data from broker API.
    """
    if seed is None:
        h = hashlib.sha256(f"{symbol}_{days}".encode()).hexdigest()
        seed = int(h[:8], 16) % 100000

    rng = random.Random(seed)
    np_rng = np.random.RandomState(seed)

    base_prices = {"NIFTY": 24000, "BANKNIFTY": 56000, "FINNIFTY": 26000, "SENSEX": 78000, "VIX": 15}
    base = base_prices.get(symbol, 24000)

    dates, opens, highs, lows, closes, vols = [], [], [], [], [], []

    price = base
    today = datetime.now(IST).date()
    start = today - timedelta(days=days)

    for i in range(days):
        d = start + timedelta(days=i)
        if d.weekday() >= 5:  # Skip weekends
            continue

        # Trend + mean reversion + volatility
        trend = 0.0002 * math.sin(i / 30)
        vol = 0.012 + 0.008 * abs(math.sin(i / 7))
        ret = np_rng.normal(trend, vol)

        o = price
        c = price * (1 + ret)
        h_ = max(o, c) * (1 + abs(np_rng.normal(0, 0.003)))
        l_ = min(o, c) * (1 - abs(np_rng.normal(0, 0.003)))
        v = int(np_rng.lognormal(12, 0.5))

        dates.append(d)
        opens.append(round(o, 2))
        highs.append(round(h_, 2))
        lows.append(round(l_, 2))
        closes.append(round(c, 2))
        vols.append(v)
        price = c

    df = pd.DataFrame({
        "date": dates, "open": opens, "high": highs,
        "low": lows, "close": closes, "volume": vols
    })
    df.set_index("date", inplace=True)
    return df


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute 25+ technical indicators as ML features"""
    f = df.copy()
    c = f["close"]
    h = f["high"]
    l = f["low"]
    v = f["volume"]

    # ── Price features ────────────────────────────────────────────────────────
    f["ret_1"] = c.pct_change(1)
    f["ret_5"] = c.pct_change(5)
    f["ret_20"] = c.pct_change(20)
    f["hl_ratio"] = (h - l) / c

    # ── EMAs ─────────────────────────────────────────────────────────────────
    for p in [9, 20, 50, 200]:
        f[f"ema_{p}"] = c.ewm(span=p, adjust=False).mean()

    f["ema20_50"] = f["ema_20"] / f["ema_50"] - 1
    f["ema50_200"] = f["ema_50"] / f["ema_200"] - 1
    f["price_ema20"] = c / f["ema_20"] - 1

    # ── RSI ───────────────────────────────────────────────────────────────────
    def rsi(s, p=14):
        d = s.diff()
        g = d.clip(lower=0).ewm(span=p).mean()
        ls = (-d.clip(upper=0)).ewm(span=p).mean()
        return 100 - 100 / (1 + g / ls.replace(0, 1e-10))

    f["rsi_14"] = rsi(c, 14)
    f["rsi_7"] = rsi(c, 7)
    f["rsi_overbought"] = (f["rsi_14"] > 70).astype(int)
    f["rsi_oversold"] = (f["rsi_14"] < 30).astype(int)

    # ── MACD ─────────────────────────────────────────────────────────────────
    ema12 = c.ewm(span=12).mean()
    ema26 = c.ewm(span=26).mean()
    f["macd"] = ema12 - ema26
    f["macd_signal"] = f["macd"].ewm(span=9).mean()
    f["macd_hist"] = f["macd"] - f["macd_signal"]
    f["macd_cross"] = (f["macd"] > f["macd_signal"]).astype(int)

    # ── Bollinger Bands ───────────────────────────────────────────────────────
    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    f["bb_upper"] = sma20 + 2 * std20
    f["bb_lower"] = sma20 - 2 * std20
    f["bb_width"] = (f["bb_upper"] - f["bb_lower"]) / sma20
    f["bb_pos"] = (c - f["bb_lower"]) / (f["bb_upper"] - f["bb_lower"] + 1e-10)

    # ── ATR ───────────────────────────────────────────────────────────────────
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    f["atr_14"] = tr.ewm(span=14).mean()
    f["atr_ratio"] = f["atr_14"] / c

    # ── ADX ───────────────────────────────────────────────────────────────────
    dm_pos = (h.diff().clip(lower=0))
    dm_neg = (-l.diff().clip(upper=0))
    di_pos = 100 * dm_pos.ewm(span=14).mean() / f["atr_14"].replace(0, 1e-10)
    di_neg = 100 * dm_neg.ewm(span=14).mean() / f["atr_14"].replace(0, 1e-10)
    dx = (100 * (di_pos - di_neg).abs() / (di_pos + di_neg + 1e-10))
    f["adx"] = dx.ewm(span=14).mean()
    f["adx_strong"] = (f["adx"] > 25).astype(int)

    # ── Volume ────────────────────────────────────────────────────────────────
    f["vol_ratio"] = v / v.rolling(20).mean()
    f["vol_surge"] = (f["vol_ratio"] > 1.5).astype(int)

    # ── Candle patterns ───────────────────────────────────────────────────────
    body = (c - df["open"]).abs()
    candle_range = h - l
    f["body_ratio"] = body / (candle_range + 1e-10)
    f["bullish_candle"] = ((c > df["open"]) & (f["body_ratio"] > 0.6)).astype(int)
    f["doji"] = (f["body_ratio"] < 0.1).astype(int)

    # ── Target: 1 if next-day return > 0.5%, 0 otherwise ─────────────────────
    f["target"] = (c.shift(-1) / c - 1 > 0.005).astype(int)

    return f.dropna()


# ─────────────────────────────────────────────────────────────────────────────
# ML MODELS
# ─────────────────────────────────────────────────────────────────────────────

FEATURE_COLS = [
    "ret_1", "ret_5", "ret_20", "hl_ratio",
    "ema20_50", "ema50_200", "price_ema20",
    "rsi_14", "rsi_7", "rsi_overbought", "rsi_oversold",
    "macd", "macd_hist", "macd_cross",
    "bb_width", "bb_pos",
    "atr_ratio",
    "adx", "adx_strong",
    "vol_ratio", "vol_surge",
    "body_ratio", "bullish_candle", "doji",
]


class TRDMLModel:
    """
    Ensemble: XGBoost + RandomForest + GradientBoosting
    Voting classifier for final signal
    """

    def __init__(self, symbol: str = "NIFTY"):
        self.symbol = symbol
        self.models = {}
        self.scaler = StandardScaler() if HAS_SKL else None
        self.trained = False
        self.metrics = {}
        self.feature_importance = {}
        self.last_trained = None

    def train(self, days: int = 365):
        if not HAS_SKL:
            return {"error": "scikit-learn not installed"}

        df = generate_ohlcv(self.symbol, days)
        df = compute_features(df)

        X = df[FEATURE_COLS].values
        y = df["target"].values

        # Time-series split (no lookahead bias)
        tscv = TimeSeriesSplit(n_splits=5)
        X_scaled = self.scaler.fit_transform(X)

        # Train on last split (most recent data)
        splits = list(tscv.split(X))
        train_idx, test_idx = splits[-1]
        X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        results = {}

        # ── XGBoost ───────────────────────────────────────────────────────────
        if HAS_XGB:
            xgb = XGBClassifier(
                n_estimators=200, max_depth=5, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                use_label_encoder=False, eval_metric="logloss",
                random_state=42, verbosity=0
            )
            xgb.fit(X_train, y_train)
            y_pred = xgb.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            results["xgboost"] = {"accuracy": round(acc*100,1), "precision": round(prec*100,1)}
            self.models["xgboost"] = xgb
            # Feature importance
            self.feature_importance = {
                FEATURE_COLS[i]: round(float(xgb.feature_importances_[i])*100, 2)
                for i in range(len(FEATURE_COLS))
            }

        # ── Random Forest ─────────────────────────────────────────────────────
        rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        y_pred_rf = rf.predict(X_test)
        results["random_forest"] = {
            "accuracy": round(accuracy_score(y_test, y_pred_rf)*100,1),
            "precision": round(precision_score(y_test, y_pred_rf, zero_division=0)*100,1)
        }
        self.models["random_forest"] = rf

        # ── Gradient Boosting ─────────────────────────────────────────────────
        gb = GradientBoostingClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
        gb.fit(X_train, y_train)
        y_pred_gb = gb.predict(X_test)
        results["gradient_boost"] = {
            "accuracy": round(accuracy_score(y_test, y_pred_gb)*100,1),
            "precision": round(precision_score(y_test, y_pred_gb, zero_division=0)*100,1)
        }
        self.models["gradient_boost"] = gb

        # Ensemble accuracy
        votes = np.array([m.predict(X_test) for m in self.models.values()])
        ensemble_pred = (votes.mean(axis=0) >= 0.5).astype(int)
        ensemble_acc = accuracy_score(y_test, ensemble_pred)

        self.trained = True
        self.last_trained = datetime.now(IST).isoformat()
        self.metrics = {
            "symbol": self.symbol,
            "training_days": days,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "models": results,
            "ensemble_accuracy": round(ensemble_acc*100, 1),
            "feature_count": len(FEATURE_COLS),
            "top_features": dict(sorted(self.feature_importance.items(), key=lambda x:-x[1])[:5]),
            "note": "Simulated data - replace with real NSE data for production accuracy",
            "last_trained": self.last_trained
        }
        return self.metrics

    def predict(self, days: int = 365) -> dict:
        """Predict next-day signal for the symbol"""
        if not self.trained:
            self.train(days)

        df = generate_ohlcv(self.symbol, days)
        df = compute_features(df)
        X_latest = df[FEATURE_COLS].iloc[-1:].values
        X_scaled = self.scaler.transform(X_latest)

        votes = {}
        proba_sum = 0
        for name, model in self.models.items():
            pred = model.predict(X_scaled)[0]
            try:
                proba = model.predict_proba(X_scaled)[0][1]
            except:
                proba = float(pred)
            votes[name] = {"prediction": int(pred), "probability": round(proba*100, 1)}
            proba_sum += proba

        avg_proba = proba_sum / max(len(self.models), 1)
        signal = "BUY" if avg_proba >= 0.55 else "SELL" if avg_proba <= 0.45 else "WAIT"
        confidence = round(abs(avg_proba - 0.5) * 200, 1)  # 0-100 scale

        # Latest indicators
        row = df.iloc[-1]
        return {
            "symbol": self.symbol,
            "signal": signal,
            "confidence": confidence,
            "probability": round(avg_proba*100, 1),
            "model_votes": votes,
            "ensemble_accuracy": self.metrics.get("ensemble_accuracy", 0),
            "indicators": {
                "RSI": round(row["rsi_14"], 1),
                "ADX": round(row["adx"], 1),
                "MACD_hist": round(row["macd_hist"], 2),
                "BB_pos": round(row["bb_pos"], 2),
                "Vol_ratio": round(row["vol_ratio"], 2),
                "EMA20_50": round(row["ema20_50"]*100, 2),
            },
            "feature_importance": self.metrics.get("top_features", {}),
            "model_type": "XGBoost+RF+GB Ensemble" if HAS_XGB else "RF+GB Ensemble",
            "note": "Based on simulated OHLCV. Production needs real NSE data feed."
        }


# ─────────────────────────────────────────────────────────────────────────────
# MODEL REGISTRY
# ─────────────────────────────────────────────────────────────────────────────
_models = {}

def get_model(symbol: str) -> TRDMLModel:
    if symbol not in _models:
        _models[symbol] = TRDMLModel(symbol)
    return _models[symbol]


def train_all(symbols=None):
    if symbols is None:
        symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
    results = {}
    for s in symbols:
        try:
            model = get_model(s)
            results[s] = model.train(days=365)
        except Exception as e:
            results[s] = {"error": str(e)}
    return results


def predict_signal(symbol: str) -> dict:
    model = get_model(symbol)
    return model.predict()
