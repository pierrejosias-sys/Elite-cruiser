"""Price data via Yahoo Finance chart API (stdlib only, no API key).

Verified working Nov 26, 2026 from this machine. Stooq timed out; Yahoo is
the route. Prices are regular-session; Robinhood's own read stays ground
truth for balances.
"""
import json
import urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
BASE = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range={rng}"


def _get(url, timeout=10):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def quote(symbol):
    """Latest regular-session price for one symbol, or None on failure."""
    try:
        data = _get(BASE.format(sym=symbol, rng="1d"))
        return data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception:
        return None


def daily_bars(symbol, rng="6mo"):
    """Daily OHLCV bars as a list of dicts, oldest first. [] on failure."""
    try:
        data = _get(BASE.format(sym=symbol, rng=rng))
        res = data["chart"]["result"][0]
        ts = res["timestamp"]
        q = res["indicators"]["quote"][0]
        bars = []
        for i, t in enumerate(ts):
            o, h, l, c, v = q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i]
            if None in (o, h, l, c):
                continue
            bars.append({"t": t, "open": o, "high": h, "low": l, "close": c, "volume": v or 0})
        return bars
    except Exception:
        return []


def quotes(symbols):
    """{symbol: price} for a list of symbols; failures are omitted."""
    out = {}
    for s in symbols:
        p = quote(s)
        if p is not None:
            out[s] = p
    return out
