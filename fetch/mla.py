"""MLA price indicators from the MLA Statistics API (no key required).

The API returns at most 100 rows per page. History is pulled once a year at a
time from MLA_START_YEAR, saved under data/mla/, then topped up each day.
"""
import csv, io, os, math, datetime as dt
from common import get, read_json, write_json, now_iso, DATA
from config import MLA_INDICATORS, MLA_START_YEAR, MLA_MAX_CHUNKS_PER_RUN

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

def _report(iid, start, end, page):
    try:
        return get(BASE + "/report/5", params={"indicatorID": iid, "fromDate": start, "toDate": end, "page": page}, tries=2).json()
    except Exception as e:
        body = getattr(getattr(e, "response", None), "text", "")[:200]
        if body:
            print(f"  mla {iid} {start}..{end} error body: {body}", flush=True)
        y = (dt.date.fromisoformat(end) - dt.timedelta(days=1)).isoformat()
        if end >= dt.date.today().isoformat() and y >= start:
            return get(BASE + "/report/5", params={"indicatorID": iid, "fromDate": start, "toDate": y, "page": page}, tries=2).json()
        raise

def fetch_range(iid, start, end):
    out, page = [], 1
    while True:
        j = _report(iid, start, end, page)
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
    backfill = read_json("mla_backfill.json", {}) or {}
    per_indicator = max(1, MLA_MAX_CHUNKS_PER_RUN // len(MLA_INDICATORS))
    for cfg in MLA_INDICATORS:
        iid, name = resolve(cfg, ilist)
        if iid is None:
            notes.append(f"{cfg['short']} not found")
            charts.append({"key": cfg["key"], "short": cfg["short"], "missing": True})
            continue
        data, unit = load_raw(cfg["key"])
        done = set(backfill.get(cfg["key"], []))
        chunks = []
        if data:
            start = dt.date.fromisoformat(max(data)) - dt.timedelta(days=14)
            chunks.append((start, today, None))
        # history, newest year first, a limited number per run
        budget = [per_indicator]
        for y in range(today.year, MLA_START_YEAR - 1, -1):
            if y == today.year and data:
                continue
            if y not in done:
                chunks.append((dt.date(y, 1, 1), min(dt.date(y, 12, 31), today), y))
        try:
            for a, b, y in chunks:
                if y is not None and budget[0] <= 0:
                    break
                rows = fetch_range(iid, a.isoformat(), b.isoformat())
                if y is not None:
                    budget[0] -= 1
                    if y < today.year:
                        backfill.setdefault(cfg["key"], []).append(y)
                print(f"  mla {cfg['key']} {a.year}: {len(rows)} rows", flush=True)
                for d, v, u in rows:
                    data[d] = v; unit = u or unit
        except Exception as e:
            notes.append(f"{cfg['short']} fetch failed: {str(e)[:120]}")
            print(f"  mla {cfg['key']} failed: {e}", flush=True)
        save_raw(cfg["key"], data, unit)
        write_json("mla_backfill.json", backfill)
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
    remaining = sum(1 for c in MLA_INDICATORS for y in range(MLA_START_YEAR, today.year) if y not in set(backfill.get(c["key"], [])))
    if remaining:
        notes.append(f"history still loading, {remaining} indicator-years to go")
    write_json("mla.json", {"updated": now_iso(), "charts": charts, "backfill_remaining": remaining})
    return f"{sum(1 for c in charts if not c.get('missing'))}/{len(charts)} indicators" + (f" ({'; '.join(notes)})" if notes else "")
