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
- **Trader** (`bot/paper.py` now, `bot/broker.py` later): paper/demo
  trades today. Live orders are DISABLED in code.

## Hard rules (Josias's — never relax, never work around)
1. **MCP account only** (Robinhood "Agentic", ••••0434). Never Individual.
2. **1% risk per trade**, **max 2–3 open positions**, **one named setup**
   (uptrend pullback — see `bot/scanner.py`).
3. **Alert-as-stop**: every entry carries an exit level. Fractional
   positions are market-exit only, so position sizing IS the stop.
4. **Journal everything** (`bot/journal.py`). No journal entry = it didn't happen.
5. **10 demo trades before live size.** Demo = paper engine, closed trades count.
6. **Double-verify before ANY live order**: setup re-check passes AND
   Josias gives an explicit go on the exact ticket. `risk.double_verify`
   enforces it; `broker.place_order` raises until the workflow changes
   by Josias's explicit decision in chat.
7. **Claude is read-only on Robinhood.** Live execution, if it ever
   happens, is Tyrone placing the exact approved ticket in MCP, then
   reporting the fill. Muse journals.
8. **No autonomous trades.** Ever. A scan result is information, not an order.

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
python3 run.py ticket MU       # build ticket (blocked until demo done + go)
```

## Hooking up the Robinhood MCP (Josias does this himself)
`bot/broker_mcp.py` is the only module allowed to talk to the Robinhood
MCP server. To hook it up: connect the Robinhood MCP in Claude Code,
then fill in the `_MCP_CALLS` table with the real tool names
(account / positions / place_order). Nothing else changes. Reads work
immediately; orders still need `live_trading_enabled: true` in
config.json (Josias flips it) AND a fresh double-verify pass on every
single order. Do not remove or weaken those checks.

## Working agreements
- Verify before claiming: show the actual output, not a summary of it.
- When a rule and a request conflict, name the conflict plainly and stop.
- Keep replies short. Numbers over adjectives.
