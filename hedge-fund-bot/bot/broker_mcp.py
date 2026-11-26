"""Robinhood MCP adapter — the plug Josias hooks up himself.

Claude Code connects to the Robinhood MCP server; this module is the
only place in the codebase allowed to talk to it. Every order path
runs through risk.double_verify() first. Read calls (account,
positions, quotes) are always allowed. Write calls (orders) require:
  1. config live_trading_enabled == true (Josias flips it, nobody else)
  2. setup re-check passes (scanner.check qualifies)
  3. 10 closed demo trades in the journal
No per-ticket human go is required (removed by Josias's explicit
request, Nov 2026): orders place automatically once the above pass.

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
    """The ONLY live order path. Gated two ways. Returns the fill."""
    cfg = _cfg()
    if not cfg.get("live_trading_enabled"):
        raise risk.RiskError("live_trading_enabled is false in config.json")
    fresh = scanner.check(ticket["symbol"])  # re-verify the setup NOW
    risk.double_verify(fresh, journal.demo_count(),
                       cfg["risk"]["min_demo_trades_before_live"])
    fill = _call("place_order", account="MCP", **ticket)
    journal.log({"mode": "live", "action": "order", **ticket, "fill": fill})
    return fill
