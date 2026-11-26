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
- **Trader** (`bot/paper.py` for demo, `bot/broker_mcp.py` for live):
  places orders through the connected Robinhood MCP once
  live_trading_enabled is true and double-verify passes.

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

## Data
- Prices: Yahoo Finance chart API (`bot/prices.py`), stdlib only.
  Regular-session prices. Robinhood's own account read is ground truth
  for balances — refresh `config.json` positions from that read, not
  from memory.
- Config: `config.json` holds rules, watchlist, and the Nov 26, 2026
  positions snapshot.

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
(••••0434). Orders still need `live_trading_enabled: true` in
config.json (Josias flips it) AND a fresh double-verify pass (setup
qualifies + 10 demo trades done) on every single order. There is no
per-ticket human go — see hard rule 8.

## Working agreements
- Verify before claiming: show the actual output, not a summary of it.
- When a rule and a request conflict, name the conflict plainly and stop.
- Keep replies short. Numbers over adjectives.
