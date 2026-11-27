# Hedge Fund Bot — instructions for Claude Code

You are one desk in Josias's trading operation. This codebase is the
shared system: constant monitoring + setup scanning + risk + paper
trading + journaling. Read this file before touching anything.

## The desk (roles)
- **Analyst** (`bot/scanner.py`): checks the watchlist against the ONE
  setup. Reports qualifies / doesn't, with numbers. Never invents a setup.
- **Risk Manager** (`bot/risk.py`): 1% sizing, position limits, and the
  double-verify gate. If Risk says no, the answer is no.
- **Portfolio Monitor** (`bot/monitor.py`): watches held positions every
  60s in market hours; alerts on stop crosses, -10% from avg cost, 5%+ moves.
  Each alert is tagged MCP or Individual. As of Nov 2026, MCP-tagged
  alerts trigger an automatic live exit (see hard rule 9) — Individual
  is never acted on.
- **Trader** (`bot/paper.py` for demo, `bot/broker_mcp.py` for live):
  places entry orders through the connected Robinhood MCP once
  live_trading_enabled is true and double-verify passes, and exit
  orders on MCP-tagged monitor alerts (no double-verify — see rule 9).

## Hard rules (Josias's — never relax, never work around)
1. **MCP account only** (Robinhood "Agentic", ••••0434). Never Individual.
2. **1% risk per trade**, **max 2–3 open positions**, **one named setup**
   (uptrend pullback — see `bot/scanner.py`).
3. **Alert-as-stop**: every entry carries an exit level. Fractional
   positions are market-exit only, so position sizing IS the stop.
4. **Journal everything** (`bot/journal.py`). No journal entry = it didn't happen.
5. **10 demo trades before live size.** Demo = paper engine, closed trades count.
6. **Double-verify before ANY live order**: setup re-check passes AND
   the 10-demo-trade requirement is met. `risk.double_verify` enforces
   it; `broker_mcp.place_order` refuses without it.
7. **Live execution runs through `bot/broker_mcp.py`**, gated by
   `live_trading_enabled` in config.json (Josias flips it, nobody
   else) and the double-verify check above. Muse journals every fill.
8. **No per-ticket human go required.** Removed by Josias's explicit
   request, Nov 2026 — he was told this makes the system capable of
   placing live orders with no human check at execution time, and
   confirmed he wanted it removed anyway. A qualifying setup with demo
   trades done and live_trading_enabled=true can now place a real
   order on its own. Position limits, 1% sizing, and alert-as-stop
   still apply; they were not part of this change.
9. **Automatic live exits (Nov 2026, Josias's explicit request).**
   `monitor.poll_once`'s alerts (stop cross, -10% avg cost, 5%+ move
   either direction) on MCP-tagged positions now trigger a real market
   sell of the full position via `broker_mcp.place_exit_order`, with no
   per-trade check and no platform approval (Robinhood
   human_must_approve_trades is also off on this account). This applies
   to EVERY position in config.json's MCP list, not only ones this bot
   opened — Josias confirmed this explicitly, including that any
   position he wants to hold long-term belongs in a different account
   (trust/401k/Roth), not here. Exits skip risk.double_verify entirely
   (no setup re-check, no demo-trade count) — that gate is for new
   entries only. Individual_watch_only is never touched, full stop —
   hard rule 1 was never part of any of these changes.
   Explicitly declined, same conversation: expanding this into an
   unconstrained "trade whatever makes the most money" agent across
   options/futures/crypto/NFTs. Not built, and should not be built on
   a request framed that way — only as a specific, bounded strategy
   with its own defined entry/exit rules and risk cap, same as the one
   equity setup this system has.
10. **Coverage cadence is a real platform limit, not a config value.**
    A single scheduled task cannot fire more than once per hour (a
    15-minute cron on one trigger was rejected outright). True 60s
    polling (`monitor --loop`, as designed) only runs while a live
    Claude session is actively watching it, capped at ~2h per
    background process. The actual always-on, unattended coverage is
    four separate hourly-cadence scheduled tasks staggered at :00,
    :15, :30, :45 (trig_014TXaxcaGo4oEppxUQDJMRF, trig_01JXNd2svnioNM7XEkifU8bX,
    trig_01Hi1fgfbe9qpDDJ5WvZGCwe, trig_01LbDzSe2Gi65bZLZ1zVMLkV),
    giving ~15-minute worst-case lag, not 60 seconds. Don't claim
    tighter coverage than this without a live session actively
    watching the loop.

## Data
- Prices: Yahoo Finance chart API (`bot/prices.py`), stdlib only.
  Regular-session prices. Robinhood's own account read is ground truth
  for balances — refresh `config.json` positions from that read, not
  from memory.
- Config: `config.json` holds rules, watchlist, the Nov 26, 2026
  positions snapshot, and the Nov 27, 2026 permissions check
  (`account.permissions_checked_2026_11_27`): option level 3, no
  platform-level trade approval, and per-symbol 24hr/all-day
  eligibility. The 24hr flag does NOT extend this bot's execution
  window today — see that block for why (fractional + market order =
  regular_hours only, a Robinhood rule, not a config toggle).
  Permissions are a point-in-time read (`get_accounts`,
  `get_trade_approval_setting`, `get_equity_tradability`) — re-check
  rather than trust this file if it matters for a decision.

## Run it
```
python3 run.py scan            # watchlist vs setup
python3 run.py monitor         # one monitoring poll
python3 run.py monitor --loop  # constant monitoring
python3 run.py paper status    # demo account + demo trade count
python3 run.py ticket MU       # build ticket (blocked until demo trades done)
```

## Robinhood MCP (hooked up)
`bot/broker_mcp.py` is the only module allowed to talk to the Robinhood
MCP server. `_MCP_CALLS` maps to the real tool names: get_portfolio,
get_equity_positions, place_equity_order, against the MCP account
(••••0434). Entry orders (`place_order`) still need
`live_trading_enabled: true` in config.json (Josias flips it) AND a
fresh double-verify pass (setup qualifies + 10 demo trades done — note
min_demo_trades_before_live is currently 0, so that half of the check
always passes) on every single order. Exit orders
(`place_exit_order`) need only `live_trading_enabled: true` — no
double-verify, no per-ticket human go. See hard rules 8 and 9.
`_call()` is a stub: the real tool calls only happen when a Claude Code
Remote session (this session, or a scheduled trigger) actually runs
this code and performs the mcp__Robinhood__* calls itself.

## Working agreements
- Verify before claiming: show the actual output, not a summary of it.
- When a rule and a request conflict, name the conflict plainly and stop.
- Keep replies short. Numbers over adjectives.
