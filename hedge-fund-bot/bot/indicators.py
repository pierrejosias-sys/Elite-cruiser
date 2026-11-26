"""Indicators: SMA, ATR (Wilder), average volume. Pure functions on bars."""


def sma(values, n):
    if len(values) < n:
        return None
    return sum(values[-n:]) / n


def atr(bars, n=14):
    """Wilder's ATR over daily bars."""
    if len(bars) < n + 1:
        return None
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = bars[i]["high"], bars[i]["low"], bars[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    if len(trs) < n:
        return None
    a = sum(trs[:n]) / n
    for tr in trs[n:]:
        a = (a * (n - 1) + tr) / n
    return a


def avg_volume(bars, n=20):
    vols = [b["volume"] for b in bars if b["volume"]]
    if len(vols) < n:
        return None
    return sum(vols[-n:]) / n
