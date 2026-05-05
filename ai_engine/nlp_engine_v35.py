# =========================================
# NLP ENGINE V3.5 (SEMANTIC + AUTO-CORRECT + AST + SUGGESTIONS)
# =========================================

import re
from typing import Dict, Any, List

SEMANTIC = {
    "overbought": ("rsi > 70", 0.95),
    "oversold": ("rsi < 30", 0.95),
    "sideways": ("adx < 20", 0.90),
    "strong trend": ("adx > 25", 0.92),
    "volume surge": ("volume > 2x", 0.95),
    "bullish": ("price > ema50", 0.85),
    "bearish": ("price < ema50", 0.85),
    "trending": ("adx > 25", 0.90),
    "ranging": ("adx < 20", 0.88),
    "momentum": ("macd increasing", 0.85),
    "reversal": ("rsi < 35", 0.80),
    "breakout": ("price > 20 candle high", 0.90),
}

WEIGHTS = {
    "EMA": 2, "RSI": 1, "MACD": 2, "VWAP": 1,
    "VOLUME": 1, "ADX": 1, "BOLLINGER": 1, "ATR": 1,
    "PRICE": 1, "VIX": 1, "TIME": 2,
}

def split_sections(text):
    sec = {"order": "", "entry": "", "exit": "", "no_trade": ""}
    current = None
    for line in text.split("\n"):
        l = line.lower()
        if any(x in l for x in ["order command", "📌", "buy ", "sell "]):
            current = "order"
        elif any(x in l for x in ["entry condition", "📊", "entry:"]):
            current = "entry"
        elif any(x in l for x in ["exit condition", "🚪", "exit:"]):
            current = "exit"
        elif any(x in l for x in ["no-trade", "no trade", "❌"]):
            current = "no_trade"
        if current:
            sec[current] += line + "\n"
    return sec

def semantic_fix(line):
    fixes = []
    for k, (v, conf) in SEMANTIC.items():
        if k in line:
            fixes.append({"original": k, "fixed": v, "confidence": conf})
            line = line.replace(k, v)
    return line, fixes

def pattern_fix(line):
    fixes = []
    # Fix "ema50 = 2.0" → "price > ema50"
    if re.search(r"ema\d+\s*=\s*[\d.]+", line):
        m = re.search(r"ema(\d+)", line)
        if m:
            fixed = f"price > ema{m.group(1)}"
            fixes.append({"original": line.strip(), "fixed": fixed, "confidence": 0.7})
            return fixed, fixes
    # Fix "ema50 sharply above ema200" → "ema50 > ema200"
    m = re.search(r"ema(\d+)\s+(?:sharply\s+)?above\s+ema(\d+)", line)
    if m:
        fixed = f"ema{m.group(1)} > ema{m.group(2)}"
        fixes.append({"original": line.strip(), "fixed": fixed, "confidence": 0.9})
        return fixed, fixes
    return line, fixes

def incomplete_fix(line):
    fixes = []
    if line.strip().lower() in ["rsi", "rsi indicator"]:
        fixes.append({"original": line.strip(), "fixed": "rsi > 50", "confidence": 0.6})
        return "rsi > 50", fixes
    if line.strip().lower() in ["macd", "macd indicator"]:
        fixes.append({"original": line.strip(), "fixed": "macd > signal", "confidence": 0.65})
        return "macd > signal", fixes
    if "ema50" in line.lower() and ">" not in line and "<" not in line:
        fixes.append({"original": line.strip(), "fixed": "price > ema50", "confidence": 0.7})
        return "price > ema50", fixes
    if "vwap" in line.lower() and "above" not in line and "below" not in line:
        fixes.append({"original": line.strip(), "fixed": "price above vwap", "confidence": 0.7})
        return "price above vwap", fixes
    return line, fixes

def auto_correct(line):
    logs = []
    line, f1 = semantic_fix(line)
    line, f2 = pattern_fix(line)
    line, f3 = incomplete_fix(line)
    logs.extend(f1 + f2 + f3)
    return line, logs

def parse_condition(line):
    line = line.lower().strip()
    # RSI
    m = re.search(r"rsi\s*>\s*(\d+)", line)
    if m: return {"RSI": {">": int(m.group(1))}}
    m = re.search(r"rsi\s*<\s*(\d+)", line)
    if m: return {"RSI": {"<": int(m.group(1))}}
    m = re.search(r"rsi\s+between\s+(\d+)\s+(?:and\s+)?(\d+)", line)
    if m: return {"RSI": {"BETWEEN": [int(m.group(1)), int(m.group(2))]}}
    m = re.search(r"rsi\s+crosses?\s+(?:above\s+)?(\d+)", line)
    if m: return {"RSI": {"CROSSES": int(m.group(1))}}
    # EMA
    m = re.search(r"ema(\d+)\s*>\s*ema(\d+)", line)
    if m: return {"EMA": {"TREND": f"EMA{m.group(1)} > EMA{m.group(2)}"}}
    m = re.search(r"ema(\d+)\s+(?:sharply\s+)?above\s+ema(\d+)", line)
    if m: return {"EMA": {"TREND": f"EMA{m.group(1)} > EMA{m.group(2)}"}}
    m = re.search(r"price\s*>\s*ema(\d+)", line)
    if m: return {"PRICE": {">": f"EMA{m.group(1)}"}}
    m = re.search(r"price\s+above\s+ema(\d+)", line)
    if m: return {"PRICE": {">": f"EMA{m.group(1)}"}}
    # ADX
    m = re.search(r"adx\s*>\s*(\d+)", line)
    if m: return {"ADX": {">": int(m.group(1))}}
    m = re.search(r"adx\s*<\s*(\d+)", line)
    if m: return {"ADX": {"<": int(m.group(1))}}
    # VOLUME
    m = re.search(r"volume\s*>\s*(\d+\.?\d*)x", line)
    if m: return {"VOLUME": {">": f"{m.group(1)}x avg"}}
    m = re.search(r"volume\s+surge\s*>\s*(\d+)", line)
    if m: return {"VOLUME": {"SURGE": f"{m.group(1)}x"}}
    # MACD
    if "macd" in line:
        if "increasing" in line or "rising" in line or "histogram" in line:
            return {"MACD": "HISTOGRAM_INCREASING"}
        if "cross" in line or "signal" in line:
            return {"MACD": "ABOVE_SIGNAL"}
        return {"MACD": "POSITIVE"}
    # VWAP
    if "vwap" in line:
        return {"VWAP": "ABOVE" if "above" in line else "BELOW" if "below" in line else "NEAR"}
    # VIX
    m = re.search(r"vix\s*<\s*(\d+)", line)
    if m: return {"VIX": {"<": int(m.group(1))}}
    # Bollinger
    if "upper band" in line or "bb upper" in line:
        return {"BOLLINGER": "UPPER_TOUCH"}
    if "lower band" in line or "bb lower" in line:
        return {"BOLLINGER": "LOWER_TOUCH"}
    if "bb.*expand" in line or "expand" in line:
        return {"BOLLINGER": "EXPANDING"}
    # ATR
    m = re.search(r"atr.*>\s*(\d+\.?\d*)", line)
    if m: return {"ATR": {">": f"avg_{m.group(1)}"}}
    # Time
    m = re.search(r"time.*(\d{1,2}):?(\d{2})", line)
    if m: return {"TIME": f"{m.group(1)}:{m.group(2)}"}
    # 9:30 / breakout
    if "9:30" in line or "930" in line:
        return {"TIME": "ENTRY_930"}
    if "10:30" in line or "1030" in line:
        return {"TIME": "EXIT_1030"}
    if "breakout" in line:
        return {"PRICE": "BREAKOUT"}
    return {"UNKNOWN": line[:50]}

def build_ast(lines):
    conditions = [parse_condition(l) for l in lines if l.strip()]
    return {"AND": conditions}

def validate(ast):
    unknown_count = str(ast).count("UNKNOWN")
    if unknown_count > len(ast.get("AND", [])) / 2:
        return "PARTIAL"
    return "OK"

def score(ast):
    s = 0
    def walk(node):
        nonlocal s
        if isinstance(node, dict):
            for k, v in node.items():
                if k in WEIGHTS:
                    s += WEIGHTS[k]
                else:
                    walk(v)
        elif isinstance(node, list):
            for i in node: walk(i)
    walk(ast)
    return s

def detect_tf(text):
    m = re.search(r"\b(1m|5m|15m|30m|1h|4h|1d|daily)\b", text.lower())
    return m.group(0) if m else "5m"

def parse_order(text):
    order = {}
    t = text.lower()
    order["side"] = "SELL" if "sell" in t else "BUY"
    for inst in ["banknifty","finnifty","nifty","sensex"]:
        if inst in t:
            order["asset"] = inst.upper()
            break
    if "asset" not in order: order["asset"] = "NIFTY"
    for ot in ["ce","pe","fut"]:
        if f" {ot}" in t or ot+"=" in t:
            order["option_type"] = ot.upper()
            break
    if "option_type" not in order: order["option_type"] = "CE"
    m = re.search(r"(\d+)\s*lot", t)
    if m: order["lots"] = int(m.group(1))
    m = re.search(r"(?:sl|stop.?loss)[:\s]+(\d+)", t)
    if m: order["sl"] = int(m.group(1))
    m = re.search(r"target[:\s]+(\d+)", t)
    if m: order["tp"] = int(m.group(1))
    m = re.search(r"trailing[:\s]+(\d+)", t)
    if m: order["trailing_sl"] = int(m.group(1))
    return order

def suggest(ast):
    suggestions = []
    ast_str = str(ast)
    if "RSI" not in ast_str:
        suggestions.append({"type":"ADD","indicator":"RSI","reason":"Momentum filter improves accuracy by ~15%"})
    if "VOLUME" not in ast_str:
        suggestions.append({"type":"ADD","indicator":"VOLUME","reason":"Volume confirmation reduces false signals"})
    if "ADX" not in ast_str:
        suggestions.append({"type":"ADD","indicator":"ADX","reason":"Trend strength filter reduces whipsaws"})
    if "MACD" not in ast_str and "EMA" not in ast_str:
        suggestions.append({"type":"ADD","indicator":"MACD or EMA","reason":"Trend direction needed for entries"})
    return suggestions

def run_engine(text: str) -> dict:
    sec = split_sections(text)
    order = parse_order(text)  # parse full text for order
    
    # Extract conditions from entry section OR numbered list
    entry_text = sec["entry"] if sec["entry"].strip() else text
    lines = []
    skip_prefixes = ('📌','📝','🚪','📈','✅','💰','===','==','order command',
                     'buy ','sell ','stop loss','target:','timeframe:','r/r:',
                     'description','exit condition','no-trade','indicators:',
                     'win rate','ai score','monthly return','version:')
    for line in entry_text.split("\n"):
        line = line.strip()
        if not line: continue
        # Skip header/order lines
        if any(line.lower().startswith(p.lower()) for p in skip_prefixes): continue
        if len(line) < 4: continue
        # Handle numbered: "1. EMA20 > EMA50" or plain conditions
        if line[0].isdigit():
            line = re.split(r"^\d+[\.\)]\s*", line, maxsplit=1)[-1]
        if line and len(line) > 3:
            lines.append(line.lower())
    
    corrected = []
    all_fixes = []
    for l in lines:
        fixed, logs = auto_correct(l)
        corrected.append(fixed)
        all_fixes.extend(logs)
    
    ast = build_ast(corrected)
    status = validate(ast)
    sc = score(ast)
    tf = detect_tf(text)
    
    # Build human-readable conditions
    readable_conditions = []
    for node in ast.get("AND", []):
        for k, v in node.items():
            if k == "UNKNOWN":
                readable_conditions.append(f"❓ {v}")
            elif k == "RSI":
                if isinstance(v, dict):
                    op = list(v.keys())[0]
                    val = list(v.values())[0]
                    if op == "BETWEEN":
                        readable_conditions.append(f"RSI between {val[0]}-{val[1]}")
                    elif op == "CROSSES":
                        readable_conditions.append(f"RSI crosses {val}")
                    else:
                        readable_conditions.append(f"RSI {op} {val}")
                else:
                    readable_conditions.append(f"RSI: {v}")
            elif k == "EMA":
                readable_conditions.append(f"EMA: {v.get('TREND', v)}")
            elif k == "PRICE":
                readable_conditions.append(f"Price {v if isinstance(v,str) else list(v.items())[0]}")
            elif k == "VOLUME":
                readable_conditions.append(f"Volume: {v}")
            elif k == "MACD":
                readable_conditions.append(f"MACD: {v}")
            elif k == "ADX":
                if isinstance(v, dict):
                    readable_conditions.append(f"ADX {list(v.keys())[0]} {list(v.values())[0]}")
            elif k == "VWAP":
                readable_conditions.append(f"Price {v} VWAP")
            elif k == "VIX":
                readable_conditions.append(f"VIX {list(v.keys())[0]} {list(v.values())[0]}")
            elif k == "TIME":
                readable_conditions.append(f"Time filter: {v}")
            elif k == "BOLLINGER":
                readable_conditions.append(f"BB: {v}")
            else:
                readable_conditions.append(f"{k}: {v}")
    
    return {
        "status": status,
        "order": order,
        "timeframe": tf,
        "ast": ast,
        "score": sc,
        "auto_fixes": all_fixes,
        "execute_ready": sc >= 3 and status == "OK",
        "suggestions": suggest(ast),
        "conditions": readable_conditions,
        "condition_count": len([c for c in readable_conditions if not c.startswith("❓")]),
    }
