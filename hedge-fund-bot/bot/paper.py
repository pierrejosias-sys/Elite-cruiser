"""Paper trading engine — the demo phase. Fills at live Yahoo prices,
no real orders. 10 closed demo trades are required before live size
(see risk.double_verify)."""
import json
import os

from . import journal, prices, risk

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "..", "paper_state.json")
START_CASH = 1000.0


def _load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return {"cash": START_CASH, "positions": {}}


def _save(state):
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)


def buy(symbol, dollars, setup_result=None):
    state = _load()
    risk.check_limits(len(state["positions"]))
    price = prices.quote(symbol)
    if price is None:
        raise RuntimeError(f"no price for {symbol}")
    if dollars > state["cash"]:
        raise RuntimeError("insufficient paper cash")
    shares = dollars / price
    state["cash"] -= dollars
    state["positions"][symbol] = {"shares": shares, "avg_cost": price}
    _save(state)
    return journal.log({"mode": "paper", "action": "buy", "symbol": symbol,
                        "shares": round(shares, 6), "price": price,
                        "setup": (setup_result or {}).get("symbol")})


def sell(symbol, reason="manual"):
    state = _load()
    pos = state["positions"].pop(symbol, None)
    if pos is None:
        raise RuntimeError(f"no paper position in {symbol}")
    price = prices.quote(symbol)
    if price is None:
        raise RuntimeError(f"no price for {symbol}")
    proceeds = pos["shares"] * price
    pnl = proceeds - pos["shares"] * pos["avg_cost"]
    state["cash"] += proceeds
    _save(state)
    return journal.log({"mode": "paper", "action": "close", "symbol": symbol,
                        "shares": round(pos["shares"], 6), "price": price,
                        "pnl": round(pnl, 2), "reason": reason})


def status():
    state = _load()
    out = {"cash": round(state["cash"], 2), "positions": {}}
    for sym, pos in state["positions"].items():
        p = prices.quote(sym)
        out["positions"][sym] = {
            "shares": round(pos["shares"], 6),
            "avg_cost": round(pos["avg_cost"], 2),
            "price": p,
            "value": round(pos["shares"] * p, 2) if p else None,
        }
    return out
