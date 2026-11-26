# Hedge Fund Bot

Josias's trading system in one codebase: constant position monitoring,
one-setup scanning, 1% risk sizing, paper/demo trading, and a journal —
built for Claude Code to run and extend. Paper-first; live orders are
disabled in code behind a double-verify gate.

Built Nov 26, 2026, combining:
- The constant-monitoring price watcher (live as a Muse hook; same
  thresholds in `bot/monitor.py`)
- The hedge-fund desk model (Analyst / Risk Manager / Portfolio
  Monitor / Trader roles — see `CLAUDE.md`)
- Josias's rules from the Nov 17 trading brief: MCP only, 1% risk,
  max 2–3 positions, alert-as-stop, 10 demo trades first, journal all

Quick start: `python3 run.py scan` · `python3 run.py monitor` ·
`python3 run.py paper status`. Stdlib only — no installs, no API keys.
