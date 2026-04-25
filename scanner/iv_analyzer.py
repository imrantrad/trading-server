"""IV Rank, Percentile, OI Analysis, Market Regime"""
import random, math, time
from typing import List, Dict


class IVAnalyzer:
    def __init__(self):
        self.iv_history: Dict[str, List[float]] = {}
        self.oi_history: Dict[str, List[dict]] = {}

    def add_iv(self, inst: str, iv: float):
        if inst not in self.iv_history: self.iv_history[inst] = []
        self.iv_history[inst].append(iv)
        if len(self.iv_history[inst]) > 252: self.iv_history[inst].pop(0)

    def get_iv_rank(self, inst: str, current_iv: float) -> dict:
        hist = self.iv_history.get(inst, [current_iv]*52)
        if len(hist) < 2: return {"iv":current_iv,"iv_rank":50,"iv_percentile":50}
        min_iv = min(hist); max_iv = max(hist)
        rank = (current_iv-min_iv)/(max_iv-min_iv)*100 if max_iv>min_iv else 50
        pct = len([x for x in hist if x<=current_iv])/len(hist)*100
        avg = sum(hist)/len(hist)
        return {
            "instrument": inst, "current_iv": round(current_iv,2),
            "iv_rank": round(rank,1), "iv_percentile": round(pct,1),
            "iv_52w_high": round(max_iv,2), "iv_52w_low": round(min_iv,2),
            "iv_avg": round(avg,2),
            "regime": "HIGH" if rank>70 else "LOW" if rank<30 else "NORMAL",
            "recommendation": "SELL_PREMIUM" if rank>70 else "BUY_OPTIONS" if rank<30 else "NEUTRAL",
            "signal": "SHORT_STRADDLE" if rank>70 else "LONG_STRADDLE" if rank<30 else "WAIT",
        }

    def analyze_oi(self, chain_data: List[dict]) -> dict:
        """Analyze options chain OI data"""
        ce_oi = sum(s["CE"]["oi"] for s in chain_data)
        pe_oi = sum(s["PE"]["oi"] for s in chain_data)
        pcr = pe_oi/ce_oi if ce_oi>0 else 1
        max_ce_oi = max(chain_data, key=lambda x: x["CE"]["oi"])
        max_pe_oi = max(chain_data, key=lambda x: x["PE"]["oi"])
        resistance = max_ce_oi["strike"]  # Max call OI = resistance
        support = max_pe_oi["strike"]     # Max put OI = support
        max_pain = min(chain_data, key=lambda x:
            sum(max(0,(x["strike"]-s["strike"]))*s["CE"]["oi"]+
                max(0,(s["strike"]-x["strike"]))*s["PE"]["oi"] for s in chain_data))["strike"]
        return {
            "total_ce_oi": ce_oi, "total_pe_oi": pe_oi, "pcr": round(pcr,2),
            "pcr_signal": "BULLISH" if pcr>1.2 else "BEARISH" if pcr<0.8 else "NEUTRAL",
            "max_pain": max_pain,
            "key_resistance": resistance, "key_support": support,
            "analysis": f"Resistance @ {resistance}, Support @ {support}, Max Pain @ {max_pain}",
        }


class MarketRegimeDetector:
    """Detect market regime: Trending/Sideways/Volatile"""
    def __init__(self): self.regimes: Dict[str,str] = {}

    def detect(self, prices: List[float], vix: float = 15) -> dict:
        if len(prices) < 20: return {"regime":"UNKNOWN"}
        recent = prices[-20:]; returns = [(recent[i]-recent[i-1])/recent[i-1] for i in range(1,20)]
        vol = math.sqrt(sum(r**2 for r in returns)/len(returns))*math.sqrt(252)*100
        trend_strength = abs(recent[-1]-recent[0])/recent[0]*100
        avg = sum(recent)/len(recent)
        rng = (max(recent)-min(recent))/avg*100
        if trend_strength > 3 and vol < 20: regime = "TRENDING"
        elif rng < 2 and vol < 15: regime = "SIDEWAYS"
        elif vix > 18 or vol > 25: regime = "VOLATILE"
        elif trend_strength > 1.5: regime = "MILD_TREND"
        else: regime = "RANGEBOUND"
        strategy = {
            "TRENDING":"EMA_CROSS or MOMENTUM",
            "SIDEWAYS":"IRON_CONDOR or SHORT_STRADDLE",
            "VOLATILE":"LONG_STRADDLE or BUY_OPTIONS",
            "MILD_TREND":"EMA_RSI_COMBO",
            "RANGEBOUND":"CREDIT_SPREADS",
        }.get(regime,"WAIT")
        return {
            "regime": regime, "volatility_annualized": round(vol,1),
            "trend_strength_pct": round(trend_strength,2),
            "range_pct": round(rng,2), "vix": vix,
            "recommended_strategy": strategy,
            "avoid": "NAKED_OPTIONS" if vix>18 else "STRADDLES" if regime=="TRENDING" else "NONE",
        }


class CorrelationTracker:
    def __init__(self): self.price_history: Dict[str,List[float]] = {}

    def add_price(self, inst: str, price: float):
        if inst not in self.price_history: self.price_history[inst] = []
        self.price_history[inst].append(price)
        if len(self.price_history[inst]) > 100: self.price_history[inst].pop(0)

    def correlate(self, inst1: str, inst2: str) -> float:
        p1 = self.price_history.get(inst1,[]); p2 = self.price_history.get(inst2,[])
        n = min(len(p1),len(p2))
        if n < 10: return 0
        p1,p2 = p1[-n:],p2[-n:]
        r1 = [(p1[i]-p1[i-1])/p1[i-1] for i in range(1,n)]
        r2 = [(p2[i]-p2[i-1])/p2[i-1] for i in range(1,n)]
        m1,m2 = sum(r1)/len(r1),sum(r2)/len(r2)
        cov = sum((r1[i]-m1)*(r2[i]-m2) for i in range(len(r1)))/len(r1)
        s1 = math.sqrt(sum((r-m1)**2 for r in r1)/len(r1))
        s2 = math.sqrt(sum((r-m2)**2 for r in r2)/len(r2))
        return round(cov/(s1*s2+1e-10),3)

    def get_matrix(self) -> dict:
        insts = list(self.price_history.keys())
        matrix = {}
        for i in insts:
            matrix[i] = {j: self.correlate(i,j) for j in insts}
        return matrix


iv_analyzer = IVAnalyzer()
regime_detector = MarketRegimeDetector()
correlation_tracker = CorrelationTracker()
