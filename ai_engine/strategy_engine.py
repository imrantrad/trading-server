# =========================================
# STRATEGY ENGINE (CANONICAL + VERSIONING)
# =========================================
import datetime, json

def now():
    return datetime.datetime.utcnow().isoformat()

def generate_id():
    return "STRAT_" + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:20]

def create_strategy(text, ast, execution, normalized):
    return {
        "id": generate_id(),
        "original_text": text,
        "versions": [{
            "version": 1,
            "timestamp": now(),
            "original_text": text,
            "ast": ast,
            "execution": execution,
            "normalized": normalized,
            "notes": "Initial version"
        }],
        "current_version": 1
    }

def add_version(strategy, text, ast, execution, normalized, notes=""):
    new_v = strategy["current_version"] + 1
    strategy["versions"].append({
        "version": new_v,
        "timestamp": now(),
        "original_text": text,
        "ast": ast,
        "execution": execution,
        "normalized": normalized,
        "notes": notes or "Updated version"
    })
    strategy["current_version"] = new_v
    return strategy

def get_current(strategy):
    v = strategy["current_version"]
    return next(x for x in strategy["versions"] if x["version"] == v)

def get_version(strategy, version_number):
    return next((x for x in strategy["versions"] if x["version"] == version_number), None)

def rollback(strategy, version_number):
    if not get_version(strategy, version_number):
        return {"error": "VERSION_NOT_FOUND"}
    strategy["current_version"] = version_number
    return strategy

def diff_versions(v1, v2):
    set1 = set(v1.get("normalized", []))
    set2 = set(v2.get("normalized", []))
    return {"added": list(set2 - set1), "removed": list(set1 - set2)}

def copy_strategy(strategy):
    return get_current(strategy)["original_text"]

def render_clean(strategy):
    current = get_current(strategy)
    entry = current.get("normalized", [])
    execution = current.get("execution", {})
    lines = [f"{i}. {c}" for i, c in enumerate(entry, 1)]
    order = execution.get("order", "")
    sl = execution.get("sl", "")
    target = execution.get("target", "")
    tf = execution.get("timeframe", "5m")
    return f"""=== {execution.get('name', 'STRATEGY')} ===

📌 ORDER COMMAND:
{order}
{f'Stop Loss: {sl} pts | Target: {target} pts' if sl else ''}
Timeframe: {tf}

📊 ENTRY CONDITIONS:
{chr(10).join(lines)}

📝 VERSION: {strategy['current_version']} of {len(strategy['versions'])}
"""

def debug_strategy(strategy):
    current = get_current(strategy)
    return {
        "id": strategy["id"],
        "current_version": strategy["current_version"],
        "total_versions": len(strategy["versions"]),
        "current_data": current
    }

# ─── In-memory strategy store (production: use DB) ───────────────────────────
_strategy_store = {}  # {strategy_id: strategy_obj}

def save_strategy(strategy):
    _strategy_store[strategy["id"]] = strategy
    return strategy["id"]

def load_strategy(strategy_id):
    return _strategy_store.get(strategy_id)

def list_strategies(user_id=None):
    return list(_strategy_store.values())
