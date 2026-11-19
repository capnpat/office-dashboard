"""Monthly live animal exports from the DAFF 'All livestock exports by market'
spreadsheet (head by species, destination and month)."""
import io, re, datetime as dt
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import openpyxl
from common import get, write_json, now_iso
from config import EXPORTS_PAGE

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
SPECIES = {"cattle": "Cattle", "sheep": "Sheep", "goat": "Goats", "goats": "Goats", "buffalo": "Buffalo"}

def find_xlsx():
    soup = BeautifulSoup(get(EXPORTS_PAGE, browser=True).text, "html.parser")
    for a in soup.find_all("a", href=True):
        if re.search(r"\.xlsx?($|\?)", a["href"], re.I):
            return urljoin(EXPORTS_PAGE, a["href"])
    raise RuntimeError("no spreadsheet link found on DAFF page")

def month_num(v):
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, (dt.date, dt.datetime)):
        return v.month
    s = str(v).strip().lower()[:3]
    return MONTHS.get(s) or (int(s) if s.isdigit() else None)

def run():
    url = find_xlsx()
    wb = openpyxl.load_workbook(io.BytesIO(get(url, browser=True, timeout=90).content), read_only=True, data_only=True)
    totals, markets, sheet_used = {}, {}, None
    for ws in wb.worksheets:
        rows = ws.iter_rows(values_only=True)
        head = None
        for i, row in enumerate(rows):
            cells = [str(c).strip().lower() if c is not None else "" for c in row]
            if "species" in cells and any("quantity" in c for c in cells):
                head = cells; break
            if i > 30:
                break
        if not head:
            continue
        col = lambda *names: next((i for i, c in enumerate(head) if any(n in c for n in names)), None)
        ci_sp, ci_q = col("species"), col("quantity")
        ci_m, ci_y = col("month"), next((i for i, c in enumerate(head) if c.startswith("year") or c == "year of export"), None)
        ci_c = col("destination", "country", "market")
        if None in (ci_sp, ci_q, ci_m, ci_y):
            continue
        sheet_used = ws.title
        for row in rows:
            try:
                sp = SPECIES.get(str(row[ci_sp]).strip().lower())
                q = float(row[ci_q] or 0); m = month_num(row[ci_m]); y = int(str(row[ci_y])[:4])
            except Exception:
                continue
            if not sp or not m:
                continue
            k = f"{y:04d}-{m:02d}"
            totals.setdefault(k, {}).setdefault(sp, 0); totals[k][sp] += q
            if ci_c is not None and row[ci_c]:
                markets.setdefault(sp, {}).setdefault(k, {}).setdefault(str(row[ci_c]).strip(), 0)
                markets[sp][k][str(row[ci_c]).strip()] += q
        break
    if not totals:
        raise RuntimeError("could not read the spreadsheet layout")
    months = sorted(totals)[-25:]
    last12 = months[-12:]
    top = {}
    for sp, bym in markets.items():
        agg = {}
        for k in last12:
            for c, q in bym.get(k, {}).items():
                agg[c] = agg.get(c, 0) + q
        top[sp] = sorted(([c, int(q)] for c, q in agg.items()), key=lambda x: -x[1])[:6]
    write_json("exports.json", {"updated": now_iso(), "source": url, "sheet": sheet_used,
                                "months": [{"month": k, **{s: int(v) for s, v in totals[k].items()}} for k in months],
                                "top_markets_12m": top})
    return f"{len(months)} months to {months[-1]}"
