"""Risk Manager role: position sizing + the double-verify gate.

Hard rules (from Josias, do not relax in code):
  - MCP account only. Never Individual.
  - 1% risk per trade.
  - Max 2-3 open positions.
  - One named setup only (see scanner.py).
  - Alert-as-stop: every entry carries an exit level; fractional
    positions are market-exit only, so sizing IS the stop.
  - 10 demo trades before any live size.
  - Double-verify: a live order needs TWO independent confirmations
    (setup re-check + Josias's explicit go on the exact ticket).
    This module enforces the gate; broker.py refuses without it.
"""


class RiskError(Exception):
    pass


def position_size(account_value, entry, invalidation, risk_pct=1.0):
    """Dollars to allocate so a move to invalidation loses ~risk_pct."""
    if entry <= invalidation:
        raise RiskError("entry must be above invalidation")
    risk_dollars = account_value * (risk_pct / 100.0)
    per_share_risk = entry - invalidation
    shares = risk_dollars / per_share_risk
    return {"shares": round(shares, 6), "dollars": round(shares * entry, 2),
            "risk_dollars": round(risk_dollars, 2)}


def check_limits(open_positions, max_positions=3):
    if open_positions >= max_positions:
        raise RiskError(f"position limit reached ({open_positions}/{max_positions})")
    return True


def double_verify(setup_result, josias_go, demo_trades_done, min_demo=10):
    """Gate for ANY live order. Returns True only if every check passes."""
    checks = {
        "setup_qualifies": bool(setup_result and setup_result.get("qualifies")),
        "josias_explicit_go": bool(josias_go),
        "demo_requirement_met": demo_trades_done >= min_demo,
    }
    if not all(checks.values()):
        failed = [k for k, v in checks.items() if not v]
        raise RiskError(f"double-verify failed: {', '.join(failed)}")
    return True
