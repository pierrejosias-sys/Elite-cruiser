"""Broker — STUB. This module places NO orders.

Why: Robinhood has no public trading API for this account, and the
standing workflow is: Tyrone places ONLY a ticket Josias approved in
chat, in the MCP account. Claude stays read-only on Robinhood.

If that workflow ever changes by Josias's explicit decision, the live
path must still pass risk.double_verify() (setup qualifies + Josias's
go on the exact ticket + 10 demo trades done) and config
live_trading_enabled must be flipped by Josias himself. Until then,
every function here raises.
"""
from . import risk


class BrokerDisabled(Exception):
    pass


def place_order(*args, **kwargs):
    raise BrokerDisabled(
        "Live orders are disabled. Workflow: Muse + Claude agree the setup "
        "qualifies, Claude writes the exact ticket, Josias approves it in "
        "chat, Tyrone places it in MCP, Muse journals the fill."
    )


def build_ticket(symbol, account_value, setup_result, demo_trades_done):
    """Builds the exact order ticket. Not sent by this function."""
    risk.double_verify(setup_result, demo_trades_done)
    size = risk.position_size(account_value, setup_result["close"],
                              setup_result["invalidation"])
    return {
        "account": "MCP (••••0434)",
        "symbol": symbol,
        "side": "buy",
        "type": "market (fractional)",
        "dollars": size["dollars"],
        "shares_est": size["shares"],
        "entry_ref": setup_result["close"],
        "invalidation": setup_result["invalidation"],
        "alert_at_exit": setup_result["invalidation"],
        "risk_dollars": size["risk_dollars"],
        "status": "READY — setup qualifies, demo requirement met",
    }
