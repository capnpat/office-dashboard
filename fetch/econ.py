"""Economic indicators. IMF DataMapper for GDP growth, inflation and
unemployment (annual, current-year estimate). BIS for central bank policy rates."""
import csv, io, time, datetime as dt
from common import get, write_json, read_json, now_iso
from config import COUNTRIES, MANUAL_POLICY_RATES

IMF = "https://www.imf.org/external/datamapper/api/v1/{ind}/{codes}"
IMF_INDS = {"gdp": "NGDP_RPCH", "cpi": "PCPIPCH", "unemp": "LUR"}
BIS = "https://stats.bis.org/api/v1/data/WS_CBPOL/M.{codes}/all"

WB = "https://api.worldbank.org/v2/country/{codes}/indicator/{ind}"
WB_INDS = {"gdp": "NY.GDP.MKTP.KD.ZG", "cpi": "FP.CPI.TOTL.ZG", "unemp": "SL.UEM.TOTL.ZS"}

def worldbank():
    codes = ";".join(c["iso3"] for c in COUNTRIES)
    out = {}
    for k, ind in WB_INDS.items():
        j = get(WB.format(codes=codes, ind=ind), params={"format": "json", "mrnev": 1, "per_page": 100}, timeout=90, tries=3).json()
        for r in (j[1] if len(j) > 1 and j[1] else []):
            if r.get("value") is not None:
                out.setdefault(r["countryiso3code"], {})[k] = {"value": r["value"], "year": r["date"], "src": "World Bank"}
    return out

def imf():
    codes = "/".join(c["iso3"] for c in COUNTRIES)
    yr = str(dt.date.today().year)
    out = {}
    for k, ind in IMF_INDS.items():
        j = None
        for wait in (0, 20):
            time.sleep(wait)
            try:
                j = get(IMF.format(ind=ind, codes=codes), tries=1, timeout=45, browser=True,
                        headers={"Accept": "application/json", "Referer": "https://www.imf.org/external/datamapper/"}).json()
                break
            except Exception as e:
                last = e
        if j is None:
            raise last
        vals = j.get("values", {}).get(ind, {})
        for c in COUNTRIES:
            s = vals.get(c["iso3"], {})
            y = yr if yr in s else (max(s) if s else None)
            out.setdefault(c["iso3"], {})[k] = {"value": s.get(y) if y else None, "year": y}
    return out

def bis():
    codes = "+".join(c["iso2"] for c in COUNTRIES if c["iso2"] not in MANUAL_POLICY_RATES)
    r = get(BIS.format(codes=codes), params={"lastNObservations": 1, "format": "csv"})
    out = {}
    for row in csv.DictReader(io.StringIO(r.text)):
        area = row.get("REF_AREA"); v = row.get("OBS_VALUE"); t = row.get("TIME_PERIOD")
        if area and v not in (None, "", "NaN"):
            out[area] = {"value": float(v), "as_at": t}
    return out

def run():
    notes = []
    try:
        im = imf()
    except Exception as e:
        im = {}; notes.append(f"IMF failed: {str(e)[:80]}")
        try:
            im = worldbank(); notes.append("using World Bank figures")
        except Exception as e2:
            notes.append(f"World Bank failed: {str(e2)[:80]}")
    try:
        rates = bis()
    except Exception as e:
        rates = {}; notes.append(f"BIS failed: {e}")
    rates.update({k: dict(v, manual=True) for k, v in MANUAL_POLICY_RATES.items()})
    prev = {r["country"]: r for r in (read_json("econ.json", {}) or {}).get("rows", [])}
    rows = []
    for c in COUNTRIES:
        i = im.get(c["iso3"]) or {k: prev.get(c["name"], {}).get(k) for k in ("gdp", "cpi", "unemp")}
        if c["iso2"] not in rates and prev.get(c["name"], {}).get("rate"):
            rates[c["iso2"]] = prev[c["name"]]["rate"]
        rows.append({"country": c["name"], "rate_name": c["rate_name"],
                     "gdp": i.get("gdp"), "cpi": i.get("cpi"), "unemp": i.get("unemp"),
                     "rate": rates.get(c["iso2"])})
    write_json("econ.json", {"updated": now_iso(), "rows": rows, "notes": notes})
    if not im:
        raise RuntimeError("; ".join(notes))
    return "; ".join(notes) or "ok"
