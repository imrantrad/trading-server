"""Options Chain Engine v12.3"""
import math, random
from typing import List, Dict


def norm_cdf(x):
    t = 1/(1+0.2316419*abs(x))
    d = 0.3989423*math.exp(-x*x/2)
    p = d*t*(0.3193815+t*(-0.3565638+t*(1.7814779+t*(-1.8212560+t*1.3302744))))
    return 1-p if x>0 else p

def black_scholes(S, K, T, r, sigma, opt_type="CE"):
    if T <= 0: return max(0, S-K) if opt_type=="CE" else max(0, K-S)
    t = T/365; d1 = (math.log(S/K)+(r+sigma**2/2)*t)/(sigma*math.sqrt(t))
    d2 = d1 - sigma*math.sqrt(t)
    if opt_type == "CE":
        price = S*norm_cdf(d1) - K*math.exp(-r*t)*norm_cdf(d2)
        delta = norm_cdf(d1)
    else:
        price = K*math.exp(-r*t)*norm_cdf(-d2) - S*norm_cdf(-d1)
        delta = norm_cdf(d1) - 1
    gamma = math.exp(-d1**2/2)/(S*sigma*math.sqrt(2*math.pi*t))
    theta = (-(S*sigma*math.exp(-d1**2/2))/(2*math.sqrt(2*math.pi*t))
             - r*K*math.exp(-r*t)*(norm_cdf(d2) if opt_type=="CE" else norm_cdf(-d2)))/365
    vega = S*math.sqrt(t)*math.exp(-d1**2/2)/math.sqrt(2*math.pi)/100
    return {"price":round(price,2),"delta":round(delta,4),"gamma":round(gamma,6),
            "theta":round(theta,2),"vega":round(vega,2)}


def generate_chain(spot: float, dte: int = 7, iv: float = 0.15,
                   num_strikes: int = 10) -> Dict:
    step = 50 if spot > 20000 else 100
    atm = round(spot/step)*step
    strikes = [atm + (i-num_strikes//2)*step for i in range(num_strikes)]
    chain = []
    for K in strikes:
        ce = black_scholes(spot, K, dte, 0.065, iv, "CE")
        pe = black_scholes(spot, K, dte, 0.065, iv, "PE")
        oi_ce = random.randint(1000, 100000)
        oi_pe = random.randint(1000, 100000)
        chain.append({
            "strike": K,
            "moneyness": "ATM" if K==atm else ("ITM" if K<atm else "OTM"),
            "CE": {**ce, "oi": oi_ce, "volume": random.randint(100,10000),
                   "iv": round(iv*100 + random.uniform(-2,2), 1)},
            "PE": {**pe, "oi": oi_pe, "volume": random.randint(100,10000),
                   "iv": round(iv*100 + random.uniform(-2,2), 1)},
            "pcr": round(oi_pe/oi_ce, 2),
        })
    total_ce_oi = sum(s["CE"]["oi"] for s in chain)
    total_pe_oi = sum(s["PE"]["oi"] for s in chain)
    max_pain = min(strikes, key=lambda k: sum(
        max(0,(k-s["strike"]))*s["CE"]["oi"] +
        max(0,(s["strike"]-k))*s["PE"]["oi"] for s in chain))
    return {
        "spot": spot, "atm": atm, "dte": dte, "iv_pct": round(iv*100,1),
        "chain": chain, "max_pain": max_pain,
        "total_ce_oi": total_ce_oi, "total_pe_oi": total_pe_oi,
        "pcr": round(total_pe_oi/total_ce_oi, 2),
    }
