"""Market Scanner v12.3 — Find opportunities automatically"""
import random, math, time
from typing import List, Dict
from dataclasses import dataclass, field


@dataclass
class ScanResult:
    instrument: str; signal: str; strength: str
    strategy: str; price: float; conditions_met: List[str]
    action: str; confidence: float; timestamp: str = ""
    def __post_init__(self):
        if not self.timestamp: self.timestamp = time.strftime("%H:%M:%S")


class MarketScanner:
    def __init__(self):
        self.instruments = ["NIFTY","BANKNIFTY","FINNIFTY","MIDCPNIFTY",
                            "RELIANCE","TCS","HDFC","INFOSYS","ICICI","SBI"]
        self.scan_results: List[ScanResult] = []
        self.last_scan: str = ""

    def _simulate_indicators(self, inst: str) -> dict:
        """Simulate indicator values (replace with real data)"""
        base = {"NIFTY":22450,"BANKNIFTY":48300,"FINNIFTY":21100}.get(inst,1000)
        price = base*(1+random.gauss(0,0.005))
        rsi = random.uniform(20,80)
        vix = random.uniform(12,20)
        return {
            "price":round(price,2),"rsi":round(rsi,1),
            "ema9":price*(1+random.gauss(0,0.002)),
            "ema21":price*(1+random.gauss(0,0.003)),
            "ema50":price*(1+random.gauss(0,0.005)),
            "vwap":price*(1+random.gauss(0,0.001)),
            "volume_ratio":random.uniform(0.5,3.0),
            "bb_upper":price*1.02,"bb_lower":price*0.98,
            "macd_hist":random.gauss(0,5),
            "iv":random.uniform(10,25),"iv_rank":random.uniform(0,100),
            "vix":vix,"pcr":random.uniform(0.6,1.4),
            "oi_change":random.uniform(-20,20),
            "atr":price*0.01,
        }

    def scan_all(self) -> List[ScanResult]:
        results = []
        for inst in self.instruments:
            ind = self._simulate_indicators(inst)
            # Run all scan strategies
            r = self._scan_rsi_oversold(inst, ind)
            if r: results.append(r)
            r = self._scan_ema_cross(inst, ind)
            if r: results.append(r)
            r = self._scan_vwap_bounce(inst, ind)
            if r: results.append(r)
            r = self._scan_iv_crush(inst, ind)
            if r: results.append(r)
            r = self._scan_breakout(inst, ind)
            if r: results.append(r)
            r = self._scan_straddle_opportunity(inst, ind)
            if r: results.append(r)
            r = self._scan_volume_surge(inst, ind)
            if r: results.append(r)
            r = self._scan_pcr_extreme(inst, ind)
            if r: results.append(r)
        results.sort(key=lambda x: -x.confidence)
        self.scan_results = results
        self.last_scan = time.strftime("%H:%M:%S")
        return results

    def _scan_rsi_oversold(self, inst, ind) -> ScanResult:
        if ind["rsi"] < 30:
            return ScanResult(inst,"RSI_OVERSOLD","STRONG","RSI_MEAN_REVERSION",
                              ind["price"],["rsi<30","potential_bounce"],"BUY",
                              round(0.7+(30-ind["rsi"])/100,2))
        if ind["rsi"] > 70:
            return ScanResult(inst,"RSI_OVERBOUGHT","STRONG","RSI_MEAN_REVERSION",
                              ind["price"],["rsi>70","potential_reversal"],"SELL",
                              round(0.7+(ind["rsi"]-70)/100,2))
        return None

    def _scan_ema_cross(self, inst, ind) -> ScanResult:
        if ind["ema9"] > ind["ema21"] and ind["rsi"] < 60:
            return ScanResult(inst,"EMA_BULL_CROSS","MODERATE","EMA_CROSS",
                              ind["price"],["ema9>ema21","rsi_ok"],"BUY",0.72)
        if ind["ema9"] < ind["ema21"] and ind["rsi"] > 40:
            return ScanResult(inst,"EMA_BEAR_CROSS","MODERATE","EMA_CROSS",
                              ind["price"],["ema9<ema21","rsi_ok"],"SELL",0.70)
        return None

    def _scan_vwap_bounce(self, inst, ind) -> ScanResult:
        diff_pct = abs(ind["price"]-ind["vwap"])/ind["vwap"]*100
        if diff_pct < 0.1 and ind["rsi"] < 55:
            return ScanResult(inst,"VWAP_BOUNCE","MODERATE","VWAP_STRATEGY",
                              ind["price"],["at_vwap","rsi_neutral"],"BUY",0.68)
        return None

    def _scan_iv_crush(self, inst, ind) -> ScanResult:
        if ind["iv_rank"] > 70:
            return ScanResult(inst,"HIGH_IV_SELL","STRONG","IV_SELL",
                              ind["price"],[f"iv_rank={ind['iv_rank']:.0f}","sell_premium"],"SELL",0.75)
        if ind["iv_rank"] < 20:
            return ScanResult(inst,"LOW_IV_BUY","MODERATE","IV_BUY",
                              ind["price"],["iv_rank_low","buy_options"],"BUY",0.65)
        return None

    def _scan_breakout(self, inst, ind) -> ScanResult:
        if ind["price"] > ind["bb_upper"] and ind["volume_ratio"] > 1.5:
            return ScanResult(inst,"BB_BREAKOUT","STRONG","BREAKOUT",
                              ind["price"],[f"bb_breakout","volume_surge_{ind['volume_ratio']:.1f}x"],"BUY",0.73)
        if ind["price"] < ind["bb_lower"] and ind["volume_ratio"] > 1.5:
            return ScanResult(inst,"BB_BREAKDOWN","STRONG","BREAKDOWN",
                              ind["price"],["bb_breakdown","volume_surge"],"SELL",0.73)
        return None

    def _scan_straddle_opportunity(self, inst, ind) -> ScanResult:
        if ind["vix"] > 16 and ind["iv_rank"] > 50:
            return ScanResult(inst,"STRADDLE_SELL","STRONG","SHORT_STRADDLE",
                              ind["price"],[f"vix={ind['vix']:.1f}","iv_elevated","theta_harvest"],"SELL",0.77)
        return None

    def _scan_volume_surge(self, inst, ind) -> ScanResult:
        if ind["volume_ratio"] > 2.5:
            action = "BUY" if ind["macd_hist"] > 0 else "SELL"
            return ScanResult(inst,"VOLUME_SURGE","STRONG","VOLUME_STRATEGY",
                              ind["price"],[f"volume_{ind['volume_ratio']:.1f}x","unusual_activity"],action,0.71)
        return None

    def _scan_pcr_extreme(self, inst, ind) -> ScanResult:
        if inst in ["NIFTY","BANKNIFTY"]:
            if ind["pcr"] < 0.7:
                return ScanResult(inst,"PCR_EXTREME_BEARISH","MODERATE","PCR_SIGNAL",
                                  ind["price"],[f"pcr={ind['pcr']:.2f}","excess_call_writing"],"SELL",0.67)
            if ind["pcr"] > 1.3:
                return ScanResult(inst,"PCR_EXTREME_BULLISH","MODERATE","PCR_SIGNAL",
                                  ind["price"],[f"pcr={ind['pcr']:.2f}","excess_put_writing"],"BUY",0.67)
        return None

    def scan_custom(self, conditions: dict) -> List[ScanResult]:
        """Custom scan based on user conditions"""
        results = []
        for inst in self.instruments:
            ind = self._simulate_indicators(inst)
            met = []
            if conditions.get("rsi_below") and ind["rsi"] < conditions["rsi_below"]: met.append(f"rsi<{conditions['rsi_below']}")
            if conditions.get("rsi_above") and ind["rsi"] > conditions["rsi_above"]: met.append(f"rsi>{conditions['rsi_above']}")
            if conditions.get("iv_rank_above") and ind["iv_rank"] > conditions["iv_rank_above"]: met.append(f"iv_rank>{conditions['iv_rank_above']}")
            if conditions.get("volume_surge") and ind["volume_ratio"] > conditions["volume_surge"]: met.append(f"volume>{conditions['volume_surge']}x")
            if len(met) == len([k for k in conditions if conditions[k]]):
                results.append(ScanResult(inst,"CUSTOM_SCAN","MODERATE","CUSTOM",
                    ind["price"],met,"BUY",0.65+len(met)*0.05))
        return results

    def get_top_opportunities(self, limit=5) -> List[dict]:
        if not self.scan_results: self.scan_all()
        return [{"instrument":r.instrument,"signal":r.signal,"action":r.action,
                 "strategy":r.strategy,"price":r.price,"confidence":r.confidence,
                 "conditions":r.conditions_met,"strength":r.strength,"time":r.timestamp}
                for r in self.scan_results[:limit]]


scanner = MarketScanner()
