"""Commodity futures and a freight proxy. Yahoo Finance chart data, with Stooq as a fallback."""
import csv, io, datetime as dt
from common import get, write_json, now_iso
from config import MARKETS

STOOQ = {"ZC=F": "zc.f", "ZW=F": "zw.f", "ZS=F": "zs.f", "ZM=F": "zm.f", "BZ=F": "cb.f", "BDRY": "bdry.us"}

def yahoo(sym):
    j = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}", params={"range": "1y", "interval": "1d"}, tries=2).json()
    r = j["chart"]["result"][0]
    ts, closes = r["timestamp"], r["indicators"]["quote"][0]["close"]
    s = [(dt.datetime.utcfromtimestamp(t).date().isoformat(), c) for t, c in zip(ts, closes) if c is not None]
    return s

def stooq(sym):
    code = STOOQ.get(sym)
    if not code:
        raise RuntimeError("no stooq code")
    r = get("https://stooq.com/q/d/l/", params={"s": code, "i": "d"}, tries=2)
    rows = list(csv.DictReader(io.StringIO(r.text)))
    cutoff = (dt.date.today() - dt.timedelta(days=370)).isoformat()
    return [(x["Date"], float(x["Close"])) for x in rows if x.get("Close") and x["Date"] >= cutoff]

def run():
    out, failed = [], []
    for m in MARKETS:
        s = None
        for fn in (yahoo, stooq):
            try:
                s = fn(m["sym"])
                if s:
                    break
            except Exception:
                continue
        if not s:
            failed.append(m["name"]); continue
        last = s[-1][1]; prev = s[-2][1] if len(s) > 1 else last
        def ago(days):
            t = (dt.date.fromisoformat(s[-1][0]) - dt.timedelta(days=days)).isoformat()
            p = [v for d, v in s if d <= t]
            return p[-1] if p else None
        out.append({**m, "date": s[-1][0], "value": round(last, 3), "prev": round(prev, 3),
                    "m1": ago(30), "y1": ago(365), "spark": [round(v, 3) for _, v in s[-90:]]})
    write_json("markets.json", {"updated": now_iso(), "items": out})
    if not out:
        raise RuntimeError("no market data")
    return f"{len(out)} series" + (f", failed {', '.join(failed)}" if failed else "")
