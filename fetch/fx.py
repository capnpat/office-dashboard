"""AUD exchange rates from the free fawazahmed0 currency API (daily, includes VND)."""
import datetime as dt
from common import get, read_json, write_json, now_iso
from config import FX_CURRENCIES

URLS = [
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{d}/v1/currencies/aud.json",
    "https://{d}.currency-api.pages.dev/v1/currencies/aud.json",
]

def fetch_day(d):
    for u in URLS:
        try:
            j = get(u.format(d=d), tries=2).json()
            return j.get("date", d), {c: j["aud"][c] for c in FX_CURRENCIES if c in j["aud"]}
        except Exception:
            continue
    return None, None

def run():
    hist = read_json("fx_history.json", {}) or {}
    date, latest = fetch_day("latest")
    if not latest:
        raise RuntimeError("no FX source reachable")
    hist[date] = latest
    # backfill the last 35 days once
    today = dt.date.fromisoformat(date)
    for i in range(1, 36):
        d = (today - dt.timedelta(days=i)).isoformat()
        if d not in hist:
            dd, v = fetch_day(d)
            if v:
                hist[dd] = v
    keep = sorted(hist)[-400:]
    hist = {k: hist[k] for k in keep}
    write_json("fx_history.json", hist)
    days = sorted(hist)
    out = []
    for c in FX_CURRENCIES:
        s = [(d, hist[d][c]) for d in days if c in hist[d]]
        if not s:
            continue
        last = s[-1][1]
        prev = s[-2][1] if len(s) > 1 else last
        s30 = s[-31:]
        out.append({"pair": "AUD/" + c.upper(), "rate": last, "prev": prev,
                    "spark": [v for _, v in s30], "first30": s30[0][1]})
    write_json("fx.json", {"updated": now_iso(), "date": date, "pairs": out})
    return f"{len(out)} pairs, {date}"
