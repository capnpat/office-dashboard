"""News from RSS feeds or, where a site has no feed, links scraped from its front page."""
import re, hashlib, datetime as dt
from urllib.parse import urljoin, urlparse
import feedparser
from bs4 import BeautifulSoup
from common import get, read_json, write_json, now_iso
from config import NEWS_SOURCES, NEWS_KEEP

def _id(url):
    return hashlib.sha1(url.encode()).hexdigest()[:12]

def rss(src):
    r = get(src["url"])
    f = feedparser.parse(r.content)
    out = []
    for e in f.entries[:30]:
        t = e.get("published_parsed") or e.get("updated_parsed")
        when = dt.datetime(*t[:6], tzinfo=dt.timezone.utc).isoformat() if t else None
        out.append({"title": e.get("title", "").strip(), "url": e.get("link"), "published": when})
    return out

def scrape(src):
    r = get(src["url"], browser=True)
    soup = BeautifulSoup(r.text, "html.parser")
    seen, out, sample = set(), [], []
    host = urlparse(src["url"]).netloc
    for a in soup.find_all("a", href=True):
        href = urljoin(src["url"], a["href"])
        title = " ".join(a.get_text(" ").split())
        if len(sample) < 80:
            sample.append([href, title[:80]])
        ok_link = src["link_contains"] in href if src.get("link_contains") else (urlparse(href).netloc == host and urlparse(href).path.count("/") >= 2)
        if not ok_link or len(title) < src.get("min_title", 20) or href in seen:
            continue
        seen.add(href)
        when = None
        m = re.search(r"(\d{2})-(\d{2})-(\d{4})", href)
        if m:
            when = f"{m.group(3)}-{m.group(1)}-{m.group(2)}T00:00:00+00:00"
        out.append({"title": title, "url": href, "published": when})
    if not out:
        write_json(f"debug_{src['name'].lower().replace(' ', '')}.json", {"status": r.status_code, "length": len(r.text), "links": sample})
    return out[:30]

def run():
    prev = read_json("news.json", {}) or {}
    first_seen = {i["id"]: i["first_seen"] for i in prev.get("items", [])}
    items, status = [], {}
    stamp = now_iso()
    for src in NEWS_SOURCES:
        try:
            got = rss(src) if src["type"] == "rss" else scrape(src)
            status[src["name"]] = {"ok": True, "count": len(got)}
        except Exception as e:
            got = [i for i in prev.get("items", []) if i["source"] == src["name"]]
            status[src["name"]] = {"ok": False, "error": str(e)[:200]}
        for g in got:
            if not g.get("title") or not g.get("url"):
                continue
            iid = _id(g["url"])
            items.append({"id": iid, "source": src["name"], "title": g["title"], "url": g["url"],
                          "published": g.get("published") or first_seen.get(iid, stamp),
                          "first_seen": first_seen.get(iid, stamp)})
    uniq = {i["id"]: i for i in items}
    items = sorted(uniq.values(), key=lambda i: i["published"] or "", reverse=True)[:NEWS_KEEP]
    write_json("news.json", {"updated": stamp, "items": items, "sources": status})
    bad = [k for k, v in status.items() if not v["ok"]]
    if len(bad) == len(NEWS_SOURCES):
        raise RuntimeError("all news sources failed")
    return f"{len(items)} items" + (f", failed {', '.join(bad)}" if bad else "")
