"""Journal: every trade (paper or live) gets logged. No exceptions."""
import json
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
JOURNAL = os.path.join(HERE, "..", "journal.jsonl")


def log(entry):
    entry = dict(entry)
    entry.setdefault("ts", datetime.now(timezone.utc).isoformat())
    with open(JOURNAL, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def entries():
    if not os.path.exists(JOURNAL):
        return []
    with open(JOURNAL) as f:
        return [json.loads(line) for line in f if line.strip()]


def demo_count():
    return sum(1 for e in entries() if e.get("mode") == "paper" and e.get("action") == "close")
