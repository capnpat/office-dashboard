import json, os, time, datetime as dt
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
UA = {"User-Agent": "Mozilla/5.0 (office-dashboard; personal use; github.com)"}

def now_iso():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

try:
    from curl_cffi import requests as browser_requests
except Exception:  # noqa
    browser_requests = None

def get(url, params=None, timeout=30, tries=3, browser=False, headers=None, **kw):
    """GET with retries. browser=True sends the request with a real browser
    fingerprint, which some government and Cloudflare-protected sites require."""
    last = None
    for i in range(tries):
        try:
            if browser and browser_requests:
                r = browser_requests.get(url, params=params, headers=headers, timeout=timeout, impersonate="chrome", **kw)
            else:
                r = requests.get(url, params=params, headers={**UA, **(headers or {})}, timeout=timeout, **kw)
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

def post_json(url, payload, headers=None, timeout=30, tries=2, browser=True):
    last = None
    for i in range(tries):
        try:
            if browser and browser_requests:
                r = browser_requests.post(url, json=payload, headers=headers, timeout=timeout, impersonate="chrome")
            else:
                r = requests.post(url, json=payload, headers={**UA, **(headers or {})}, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa
            last = e
            time.sleep(2 * (i + 1))
    raise last
