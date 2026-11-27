"""Robinhood MCP adapter — the plug Josias hooks up himself.

Claude Code connects to the Robinhood MCP server; this module is the
only place in the codebase allowed to talk to it. Read calls (account,
positions, quotes) are always allowed.

Two write (order) paths, both MCP account ONLY, never Individual
(hard rule 1):
  - place_order (entry): live_trading_enabled == true, setup re-check
    passes (scanner.check qualifies), 10 closed demo trades in the
    journal (currently 0 -- see config.risk.min_demo_trades_before_live).
  - place_exit_order (exit, added Nov 2026): live_trading_enabled ==
    true only. No setup re-check, no demo-trade count -- an exit is
    triggered by adverse price action against a held position, not by
    the entry setup. Driven by monitor.poll_once's MCP-tagged alerts.
No per-ticket human go is required for either path (removed by
Josias's explicit request, Nov 2026): orders place automatically once
the above pass. Note: _call() below is a stub a plain Python process
cannot execute against the real MCP server -- actual order placement
happens when a Claude Code Remote session (interactive or a scheduled
trigger) runs this code and performs the real mcp__Robinhood__* tool
calls itself.

The MCP tool names below are placeholders matching the Robinhood MCP
surface (account/positions/orders). When hooking up, map them to the
real tool names the connected server exposes — change ONLY the
_MCP_CALLS table, nothing else.
"""
import json
import os

from . import journal, risk, scanner

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "..", "config.json")

# Map logical ops -> MCP tool names. Hooked up to the connected Robinhood MCP.
_MCP_CALLS = {
    "get_account": "mcp__Robinhood__get_portfolio",
    "get_positions": "mcp__Robinhood__get_equity_positions",
    "place_order": "mcp__Robinhood__place_equity_order",
}

MCP_ACCOUNT_NUMBER = "504640434"  # Robinhood "MCP" account, ••••0434, agentic_allowed=true


class NotHookedUp(Exception):
    pass


def _cfg():
    with open(CONFIG) as f:
        return json.load(f)


def _call(op, **kwargs):
    tool = _MCP_CALLS.get(op)
    if not tool:
        raise NotHookedUp(
            f"MCP not hooked up yet: set _MCP_CALLS['{op}'] to the real "
            "Robinhood MCP tool name in bot/broker_mcp.py"
        )
    # Claude Code executes the MCP tool here and returns its result.
    raise NotHookedUp(f"MCP call '{tool}' must be executed by Claude Code")


def get_account():
    """Read-only: MCP account value + buying power."""
    return _call("get_account", account="MCP")


def get_positions():
    """Read-only: current MCP positions."""
    return _call("get_positions", account="MCP")


def place_order(ticket):
    """The entry order path. Gated two ways. Returns the fill."""
    cfg = _cfg()
    if not cfg.get("live_trading_enabled"):
        raise risk.RiskError("live_trading_enabled is false in config.json")
    fresh = scanner.check(ticket["symbol"])  # re-verify the setup NOW
    risk.double_verify(fresh, journal.demo_count(),
                       cfg["risk"]["min_demo_trades_before_live"])
    fill = _call("place_order", account="MCP", **ticket)
    journal.log({"mode": "live", "action": "order", **ticket, "fill": fill})
    return fill


def place_exit_order(symbol, quantity, reason):
    """The exit path for alert-as-stop (added Nov 2026, per Josias's
    explicit request, no per-trade check). Automatic, MCP account ONLY
    -- never call this for a symbol tagged "Individual" in
    monitor.poll_once's alerts; that account is permanently off-limits
    (hard rule 1).

    Unlike place_order, this does NOT re-check the entry setup or the
    demo-trade count: an exit is triggered by adverse price action
    against an existing position, not by the entry setup qualifying,
    so that gate does not apply here. The only gate is
    live_trading_enabled.

    `quantity` must be the position's current live share count (from
    get_equity_positions, not the config.json snapshot, which can be
    stale) -- this always exits the full position, fractional market
    order only, per config.risk.fractional_market_exit_only.
    """
    cfg = _cfg()
    if not cfg.get("live_trading_enabled"):
        raise risk.RiskError("live_trading_enabled is false in config.json")
    ticket = {"symbol": symbol, "side": "sell", "type": "market",
              "quantity": quantity, "time_in_force": "gfd",
              "market_hours": "regular_hours"}
    fill = _call("place_order", account="MCP", **ticket)
    journal.log({"mode": "live", "action": "exit", "symbol": symbol,
                "quantity": quantity, "reason": reason, "fill": fill})
    return fill
