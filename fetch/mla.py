"""MLA price indicators from the MLA Statistics API (no key required).

The API returns at most 100 rows per page. History is pulled once a year at a
time from MLA_START_YEAR, saved under data/mla/, then topped up each day.
"""
import csv, io, os, math, datetime as dt
from common import get, read_json, write_json, now_iso, DATA
from config import MLA_INDICATORS, MLA_START_YEAR

BASE = "https://api-mlastatistics.mla.com.au"

def _rows(j):
    if isinstance(j, list):
        return j
    for k in ("data", "Data", "results", "value"):
        if isinstance(j.get(k), list):
            return j[k]
    return []

def _total(j):
    for k, v in (j.items() if isinstance(j, dict) else []):
        if "total" in k.lower() and "row" in k.lower():
            try:
                return int(v)
            except Exception:
                pass
    return None

def indicator_list():
    j = get(BASE + "/indicator").json()
    rows = _rows(j) if isinstance(j, dict) else j
    out = []
    for r in rows:
        rid = next((r[k] for k in r if k.lower() in ("indicatorid", "indicator_id", "id")), None)
        name = next((r[k] for k in r if "desc" in k.lower() or "name" in k.lower()), None)
        if rid is not None and name:
            out.append({"id": rid, "name": str(name)})
    write_json("mla_indicators.json", out)
    return out

def resolve(cfg, ilist):
    if cfg.get("id") is not None:
        return cfg["id"], next((i["name"] for i in ilist if str(i["id"]) == str(cfg["id"])), cfg["short"])
    hits = [i for i in ilist if all(m in i["name"].lower() for m in cfg["match"])]
    if not hits:
        return None, None
    hits.sort(key=lambda i: (0 if i["name"].lower().startswith("national") or "eastern" in i["name"].lower()
                                  or "western" in i["name"].lower() else 1, len(i["name"])))
    return hits[0]["id"], hits[0]["name"]

def _pick(r, *cands):
    for k in r:
        kl = k.lower()
        if any(c in kl for c in cands):
            return r[k]
    return None

def fetch_range(iid, start, end):
    out, page = [], 1
    while True:
        j = get(BASE + "/report/5", params={"indicatorID": iid, "fromDate": start, "toDate": end, "page": page}, tries=2).json()
        rows = _rows(j)
        for r in rows:
            d = _pick(r, "calendar_date", "date")
            v = _pick(r, "indicator_value", "value", "price")
            u = _pick(r, "unit")
            if d and v not in (None, ""):
                out.append((str(d)[:10], float(v), u or ""))
        total = _total(j) if isinstance(j, dict) else None
        if not rows or total is None or page >= math.ceil(total / 100):
            break
        page += 1
    return out

def raw_path(key):
    return os.path.join(DATA, "mla", key + ".csv")

def load_raw(key):
    p = raw_path(key)
    if not os.path.exists(p):
        return {}, ""
    d, unit = {}, ""
    with open(p) as f:
        for row in csv.reader(f):
            d[row[0]] = float(row[1]); unit = row[2] if len(row) > 2 else unit
    return d, unit

def save_raw(key, d, unit):
    os.makedirs(os.path.dirname(raw_path(key)), exist_ok=True)
    with open(raw_path(key), "w", newline="") as f:
        w = csv.writer(f)
        for k in sorted(d):
            w.writerow([k, d[k], unit])

def weekly(series):
    """Collapse daily values to one value per ISO week (mean)."""
    b = {}
    for d, v in series:
        y, w, _ = dt.date.fromisoformat(d).isocalendar()
        b.setdefault((y, w), []).append((d, v))
    out = []
    for k in sorted(b):
        vals = b[k]
        out.append([vals[-1][0], round(sum(v for _, v in vals) / len(vals), 2)])
    return out

def run():
    ilist = indicator_list()
    print(f"  mla: {len(ilist)} indicators listed", flush=True)
    today = dt.date.today()
    charts, notes = [], []
    for cfg in MLA_INDICATORS:
        iid, name = resolve(cfg, ilist)
        if iid is None:
            notes.append(f"{cfg['short']} not found")
            charts.append({"key": cfg["key"], "short": cfg["short"], "missing": True})
            continue
        data, unit = load_raw(cfg["key"])
        if data:
            start = dt.date.fromisoformat(max(data)) - dt.timedelta(days=14)
            chunks = [(start, today)]
        else:
            chunks = [(dt.date(y, 1, 1), min(dt.date(y, 12, 31), today)) for y in range(MLA_START_YEAR, today.year + 1)]
        try:
            for a, b in chunks:
                rows = fetch_range(iid, a.isoformat(), b.isoformat())
                print(f"  mla {cfg['key']} {a.year}: {len(rows)} rows", flush=True)
                for d, v, u in rows:
                    data[d] = v; unit = u or unit
        except Exception as e:
            notes.append(f"{cfg['short']} fetch failed: {str(e)[:120]}")
            print(f"  mla {cfg['key']} failed: {e}", flush=True)
        save_raw(cfg["key"], data, unit)
        s = sorted(data.items())
        if not s:
            charts.append({"key": cfg["key"], "short": cfg["short"], "missing": True}); continue
        w = weekly(s)
        def ago(days):
            target = (dt.date.fromisoformat(s[-1][0]) - dt.timedelta(days=days)).isoformat()
            prior = [v for d, v in s if d <= target]
            return prior[-1] if prior else None
        charts.append({"key": cfg["key"], "short": cfg["short"], "name": name, "unit": unit,
                       "id": iid, "last_date": s[-1][0], "value": s[-1][1],
                       "wk_ago": ago(7), "yr_ago": ago(365), "weekly": w})
    write_json("mla.json", {"updated": now_iso(), "charts": charts})
    return f"{sum(1 for c in charts if not c.get('missing'))}/{len(charts)} indicators" + (f" ({'; '.join(notes)})" if notes else "")
