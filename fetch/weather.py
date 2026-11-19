"""Weather from Open-Meteo (no key). Current conditions, a 4-day outlook and,
where configured, rainfall to date this year against the 1991 to 2020 average."""
import datetime as dt
from common import get, read_json, write_json, now_iso
from config import WEATHER

FC = "https://api.open-meteo.com/v1/forecast"
ARCH = "https://archive-api.open-meteo.com/v1/archive"

def ytd(loc, cache):
    today = dt.date.today()
    key = loc["name"]
    c = cache.get(key)
    if c and c.get("date") == today.isoformat():
        return c
    j = get(ARCH, params={"latitude": loc["lat"], "longitude": loc["lon"], "start_date": "1991-01-01",
                          "end_date": (today - dt.timedelta(days=1)).isoformat(), "daily": "precipitation_sum",
                          "timezone": "Australia/Perth"}, timeout=90).json()
    days, rain = j["daily"]["time"], j["daily"]["precipitation_sum"]
    md = (today - dt.timedelta(days=1)).strftime("%m-%d")
    by_year = {}
    full = {}
    for d, r in zip(days, rain):
        if r is None:
            continue
        y = int(d[:4])
        full[y] = full.get(y, 0) + r
        if d[5:] <= md:
            by_year[y] = by_year.get(y, 0) + r
    base = [by_year[y] for y in range(1991, 2021) if y in by_year]
    base_full = [full[y] for y in range(1991, 2021) if y in full]
    last30 = sum(r for d, r in zip(days[-30:], rain[-30:]) if r is not None)
    c = {"date": today.isoformat(), "ytd": round(by_year.get(today.year, 0), 1),
         "ytd_avg": round(sum(base) / len(base), 1) if base else None,
         "year_avg": round(sum(base_full) / len(base_full), 1) if base_full else None,
         "last30": round(last30, 1)}
    cache[key] = c
    return c

def run():
    prev = read_json("weather.json", {}) or {}
    cache = prev.get("ytd_cache", {})
    out, failed = [], []
    for loc in WEATHER:
        try:
            j = get(FC, params={"latitude": loc["lat"], "longitude": loc["lon"],
                                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,weather_code",
                                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weather_code",
                                "timezone": "auto", "forecast_days": 4}).json()
            item = {"name": loc["name"], "current": j.get("current", {}), "daily": j.get("daily", {})}
            if loc.get("ytd"):
                try:
                    item["rain"] = ytd(loc, cache)
                except Exception as e:
                    item["rain_error"] = str(e)[:120]
            out.append(item)
        except Exception:
            failed.append(loc["name"])
    write_json("weather.json", {"updated": now_iso(), "locations": out, "ytd_cache": cache})
    if not out:
        raise RuntimeError("no weather data")
    return f"{len(out)} locations" + (f", failed {', '.join(failed)}" if failed else "")
