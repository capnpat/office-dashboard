"""AusTender current approaches to market, filtered by keyword."""
import re, hashlib
import feedparser
from common import get, read_json, write_json, now_iso
from config import TENDERS_FEED, TENDER_KEYWORDS

def run():
    r = get(TENDERS_FEED, browser=True, timeout=60)
    f = feedparser.parse(r.content)
    prev = read_json("tenders.json", {}) or {}
    first = {i["id"]: i["first_seen"] for i in prev.get("items", [])}
    stamp = now_iso(); out = []
    for e in f.entries:
        title = (e.get("title") or "").strip()
        desc = re.sub(r"<[^>]+>", " ", e.get("summary") or e.get("description") or "")
        desc = " ".join(desc.split())
        text = (title + " " + desc).lower()
        hits = [k for k in TENDER_KEYWORDS if k in text]
        if not hits:
            continue
        iid = hashlib.sha1((e.get("link") or title).encode()).hexdigest()[:12]
        close = None
        m = re.search(r"Clos\w*\s*(?:Date)?\s*(?:&\s*Time)?[:\s]+([0-9]{1,2}[-/ ][A-Za-z0-9]{2,9}[-/ ][0-9]{2,4})", desc)
        if m:
            close = m.group(1)
        agency = None
        m = re.search(r"Agency[:\s]+([^:]+?)(?:\s{2,}|Category|Close|ATM|$)", desc)
        if m:
            agency = m.group(1).strip()[:80]
        out.append({"id": iid, "title": title, "url": e.get("link"), "agency": agency, "close": close,
                    "match": hits[:3], "first_seen": first.get(iid, stamp)})
    out.sort(key=lambda i: i["first_seen"], reverse=True)
    write_json("tenders.json", {"updated": stamp, "items": out[:30], "feed_items": len(f.entries)})
    if not f.entries:
        raise RuntimeError("tender feed empty or unreadable")
    return f"{len(out)} matching of {len(f.entries)}"
