"""Watch web pages for changes. Compares the main text of each page with the
last saved copy and records an alert with the first added lines."""
import os, difflib, hashlib
from bs4 import BeautifulSoup
from common import get, read_json, write_json, now_iso, DATA
from config import MONITORED_PAGES

def page_text(page):
    r = get(page["url"])
    soup = BeautifulSoup(r.text, "html.parser")
    node = soup.select_one(page.get("selector") or "body") or soup.body or soup
    for t in node(["script", "style", "noscript", "nav", "header", "footer", "form", "svg"]):
        t.decompose()
    lines = [" ".join(l.split()) for l in node.get_text("\n").split("\n")]
    return "\n".join(l for l in lines if l)

def run():
    state = read_json("monitor.json", {"pages": {}, "alerts": []}) or {"pages": {}, "alerts": []}
    stamp = now_iso()
    msgs = []
    for p in MONITORED_PAGES:
        snap = os.path.join(DATA, "monitor", p["key"] + ".txt")
        st = state["pages"].setdefault(p["key"], {})
        st.update({"name": p["name"], "url": p["url"], "checked": stamp})
        try:
            text = page_text(p)
        except Exception as e:
            st.update({"ok": False, "error": str(e)[:200]}); msgs.append(f"{p['key']} failed"); continue
        h = hashlib.sha1(text.encode()).hexdigest()
        old = open(snap, encoding="utf-8").read() if os.path.exists(snap) else None
        st["ok"] = True; st.pop("error", None)
        if old is None:
            st["baseline"] = stamp
        elif hashlib.sha1(old.encode()).hexdigest() != h:
            diff = list(difflib.unified_diff(old.split("\n"), text.split("\n"), lineterm="", n=0))
            added = [l[1:] for l in diff if l.startswith("+") and not l.startswith("+++")]
            removed = [l[1:] for l in diff if l.startswith("-") and not l.startswith("---")]
            summary = added[0] if added else (f"Removed {removed[0]}" if removed else "Content changed")
            state["alerts"].insert(0, {"key": p["key"], "name": p["name"], "url": p["url"], "at": stamp,
                                       "summary": summary[:180], "added": len(added), "removed": len(removed)})
            st["changed"] = stamp
            msgs.append(f"{p['key']} changed")
        with open(snap, "w", encoding="utf-8") as f:
            f.write(text)
    state["alerts"] = state["alerts"][:50]
    state["updated"] = stamp
    write_json("monitor.json", state)
    return ", ".join(msgs) or "no changes"
