"""Animal disease events from WOAH WAHIS for selected countries.

Uses the public endpoints behind the WAHIS website (no key). WAHIS sits behind
Cloudflare, so requests go out with a browser fingerprint."""
import datetime as dt
from common import get, post_json, write_json, read_json, now_iso
from config import DISEASE_COUNTRIES, DISEASE_DAYS, DISEASE_PRIORITY

BASE = "https://wahis.woah.org/api/v1/pi"
H = {"Accept": "application/json", "Content-Type": "application/json", "accept-language": "en",
     "env": "PRD", "type": "REQUEST", "token": "#PIPRD202006#", "clientId": "OIEwebsite"}

def country_ids():
    cached = read_json("wahis_countries.json")
    if not cached:
        cached = get(BASE + "/country/list", params={"language": "en"}, headers=H, browser=True).json()
        write_json("wahis_countries.json", cached)
    by = {c["name"].lower(): c["areaId"] for c in cached if "name" in c and "areaId" in c}
    ids, missing = [], []
    for n in DISEASE_COUNTRIES:
        hit = by.get(n.lower()) or next((v for k, v in by.items() if n.lower() in k), None)
        (ids.append(hit) if hit is not None else missing.append(n))
    return ids, missing

def run():
    ids, missing = country_ids()
    today = dt.date.today()
    span = {"from": (today - dt.timedelta(days=DISEASE_DAYS)).isoformat(), "to": today.isoformat()}
    base = {"eventIds": [], "reportIds": [], "countries": ids, "firstDiseases": [], "secondDiseases": [],
            "typeStatuses": [], "reasons": [], "eventStatuses": [], "reportTypes": [], "reportStatuses": [],
            "animalTypes": [], "sortColumn": "submissionDate", "sortOrder": "desc", "pageSize": 500, "pageNumber": 0}
    try:
        res = post_json(BASE + "/event/filtered-list?language=en", {**base, "eventStartDate": None, "submissionDate": span}, headers=H)
    except Exception:
        res = post_json(BASE + "/event/filtered-list?language=en", {**base, "eventStartDate": span, "submissionDate": None}, headers=H)
    rows = res.get("list", [])
    seen, out = set(), []
    for r in rows:
        if r.get("isAquatic"):
            continue
        ev = r.get("eventId")
        if ev in seen:
            continue
        seen.add(ev)
        dis = (r.get("disease") or "").strip()
        out.append({"reportId": r.get("reportId"), "eventId": ev, "country": r.get("country"),
                    "disease": dis, "subType": r.get("subType"), "reason": r.get("reason"),
                    "reportType": r.get("reportType"), "status": r.get("eventStatus"),
                    "submitted": r.get("submissionDate"), "started": r.get("eventStartDate"),
                    "priority": any(p in dis.lower() for p in DISEASE_PRIORITY),
                    "url": f"https://wahis.woah.org/#/in-review/{r.get('reportId')}"})
    out.sort(key=lambda x: x.get("submitted") or "", reverse=True)
    write_json("disease.json", {"updated": now_iso(), "days": DISEASE_DAYS, "events": out[:60],
                                "countries_missing": missing})
    return f"{len(out)} events" + (f", countries not matched {', '.join(missing)}" if missing else "")
