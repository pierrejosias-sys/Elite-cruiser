"""Portfolio Monitor role: constant monitoring of held positions.

Same thresholds as the live Muse hook (robinhood-price-watch):
  - IREN vs the $14.95 stop (either direction)
  - any position crossing 10% below avg cost
  - any name moving 5%+ since its last alert
Polls every config.monitor.poll_seconds during market hours (ET).
Alerts print to stdout and append to alerts.jsonl. Read-only.
"""
import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from . import prices

HERE = os.path.dirname(os.path.abspath(__file__))
ALERTS = os.path.join(HERE, "..", "alerts.jsonl")
STATE = os.path.join(HERE, "..", "monitor_state.json")
ET = ZoneInfo("America/New_York")


def _market_open(cfg):
    now = datetime.now(ET)
    if now.weekday() > 4:
        return False
    start, end = cfg["monitor"]["market_hours_et"]
    hm = now.strftime("%H:%M")
    return start <= hm <= end


def _load_state():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return {"seeded": False, "last_alert": {}, "below10": {}, "iren_above_stop": None}


def _positions(cfg):
    snap = cfg["positions_snapshot_2026_11_26"]
    out = []
    for p in snap["MCP"]:
        out.append((p["symbol"], p["avg_cost"], p.get("stop")))
    for p in snap["Individual_watch_only"]:
        out.append((p["symbol"], p["avg_cost"], p.get("stop")))
    return out


def poll_once(cfg):
    state = _load_state()
    alerts = []
    below_pct = cfg["monitor"]["alert_below_avg_cost_pct"] / 100.0
    move_pct = cfg["monitor"]["alert_move_since_last_pct"] / 100.0
    for sym, avg, stop in _positions(cfg):
        price = prices.quote(sym)
        if price is None:
            continue
        is_below = price < avg * (1 - below_pct)
        if not state["seeded"]:
            state["last_alert"][sym] = price
            state["below10"][sym] = is_below
            if sym == "IREN" and stop:
                state["iren_above_stop"] = price >= stop
            continue
        reason = None
        if is_below and not state["below10"].get(sym):
            reason = f"crossed {cfg['monitor']['alert_below_avg_cost_pct']}% below avg cost"
        elif sym in state["last_alert"]:
            last = state["last_alert"][sym]
            if last and abs(price - last) / last >= move_pct:
                reason = "moved 5%+ since last alert"
        if sym == "IREN" and stop:
            above = price >= stop
            if state["iren_above_stop"] is not None and above != state["iren_above_stop"]:
                reason = "recovered above the stop" if above else "fell back below the stop"
            state["iren_above_stop"] = above
        state["below10"][sym] = is_below
        if reason:
            alerts.append({"symbol": sym, "price": price, "avg_cost": avg,
                           "reason": reason, "ts": datetime.now(ET).isoformat()})
            state["last_alert"][sym] = price
    state["seeded"] = True
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)
    for a in alerts:
        with open(ALERTS, "a") as f:
            f.write(json.dumps(a) + "\n")
        print(f"ALERT {a['symbol']} ${a['price']} — {a['reason']} (avg cost ${a['avg_cost']})")
    return alerts


def run_forever(cfg):
    while True:
        if _market_open(cfg):
            poll_once(cfg)
        time.sleep(cfg["monitor"]["poll_seconds"])
