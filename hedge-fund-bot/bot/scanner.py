"""Analyst role: checks the watchlist against Josias's one setup.

Setup (uptrend pullback):
  1. Close above the 50-day average
  2. Pullback to near the 20-day average (within 1 ATR)
  3. Green close on above-average volume (20-day avg)
  Invalidation: below the pullback low, or 1.5 ATR below entry.

A name qualifies only if ALL conditions pass. No setup = no trade.
"""
from . import indicators as ind
from . import prices


def check(symbol):
    bars = prices.daily_bars(symbol)
    if len(bars) < 55:
        return {"symbol": symbol, "qualifies": False, "reason": "not enough data"}
    closes = [b["close"] for b in bars]
    last = bars[-1]
    sma20 = ind.sma(closes, 20)
    sma50 = ind.sma(closes, 50)
    atr14 = ind.atr(bars, 14)
    avol = ind.avg_volume(bars[:-1], 20)  # avg of prior 20 sessions

    above50 = last["close"] > sma50
    near20 = abs(last["close"] - sma20) <= atr14
    green = last["close"] > last["open"]
    vol_ok = avol is not None and last["volume"] > avol

    qualifies = above50 and near20 and green and vol_ok
    return {
        "symbol": symbol,
        "close": round(last["close"], 2),
        "sma20": round(sma20, 2),
        "sma50": round(sma50, 2),
        "atr14": round(atr14, 2),
        "above_50d": above50,
        "near_20d": near20,
        "green_close": green,
        "volume_above_avg": vol_ok,
        "qualifies": qualifies,
        "invalidation": round(min(b["low"] for b in bars[-10:]), 2),
    }


def scan(watchlist):
    return [check(s) for s in watchlist]
