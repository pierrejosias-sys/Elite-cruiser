"""CLI entry point.

  python3 run.py scan            # Analyst: check watchlist vs the setup
  python3 run.py monitor         # Portfolio Monitor: one poll (or --loop)
  python3 run.py paper status    # paper account status
  python3 run.py paper buy SYM $ # paper buy (demo phase)
  python3 run.py paper sell SYM  # paper sell
  python3 run.py ticket SYM      # build an order ticket (needs setup qualifying + demo trades done)
  python3 run.py journal-exit SYM QUANTITY REASON FILL_JSON
                                  # record a live exit fill (order placed by the
                                  # orchestrating Claude Code Remote session via
                                  # the real Robinhood MCP tools -- broker_mcp's
                                  # _call() is a stub a plain process can't use)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bot import broker, journal, monitor, paper, scanner  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "config.json")) as f:
    CFG = json.load(f)


def main(argv):
    if not argv:
        print(__doc__)
        return
    cmd = argv[0]
    if cmd == "scan":
        for r in scanner.scan(CFG["watchlist"]):
            mark = "QUALIFIES" if r.get("qualifies") else "no"
            print(f"{r['symbol']}: {mark} — close ${r.get('close')} "
                  f"(50d ${r.get('sma50')}, 20d ${r.get('sma20')}, ATR ${r.get('atr14')})")
    elif cmd == "monitor":
        if "--loop" in argv:
            monitor.run_forever(CFG)
        else:
            alerts = monitor.poll_once(CFG)
            print(f"poll done, {len(alerts)} alert(s)")
            for a in alerts:
                print("ALERT_JSON " + json.dumps(a))
    elif cmd == "paper":
        sub = argv[1] if len(argv) > 1 else "status"
        if sub == "status":
            print(json.dumps(paper.status(), indent=2))
            print(f"closed demo trades: {journal.demo_count()}/10")
        elif sub == "buy":
            print(paper.buy(argv[2], float(argv[3])))
        elif sub == "sell":
            print(paper.sell(argv[2]))
    elif cmd == "ticket":
        sym = argv[1]
        result = scanner.check(sym)
        try:
            ticket = broker.build_ticket(sym, 70.42, result, journal.demo_count())
            print(json.dumps(ticket, indent=2))
        except Exception as e:
            print(f"ticket blocked: {e}")
    elif cmd == "journal-exit":
        sym, qty, reason, fill_json = argv[1], argv[2], argv[3], argv[4]
        entry = journal.log({"mode": "live", "action": "exit", "symbol": sym,
                             "quantity": float(qty), "reason": reason,
                             "fill": json.loads(fill_json)})
        print(json.dumps(entry))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
