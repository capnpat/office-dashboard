import json, os, time, datetime as dt
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
UA = {"User-Agent": "Mozilla/5.0 (office-dashboard; personal use; github.com)"}

def now_iso():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

def get(url, params=None, timeout=30, tries=3, **kw):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout, **kw)
            r.raise_for_status()
            return r
        except Exception as e:  # noqa
            last = e
            time.sleep(2 * (i + 1))
    raise last

def read_json(name, default=None):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def write_json(name, obj):
    p = os.path.join(DATA, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, p)
