"""Run each data block whose refresh interval has passed. Usage
python fetch/run.py [--force] [block ...]"""
import sys, datetime as dt, traceback
import fx, mla, econ, news, monitor
from common import read_json, write_json, now_iso
from config import INTERVALS

BLOCKS = {"fx": fx, "news": news, "monitor": monitor, "econ": econ, "mla": mla}

def due(status, name):
    last = status.get(name, {}).get("last_ok")
    if not last:
        return True
    age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(last)
    return age.total_seconds() / 3600 >= INTERVALS[name] - 0.05

def main(argv):
    force = "--force" in argv
    only = [a for a in argv if not a.startswith("--")] or list(BLOCKS)
    status = read_json("status.json", {}) or {}
    for name in only:
        if not force and not due(status, name):
            print(f"{name}: not due"); continue
        st = status.setdefault(name, {})
        st["last_try"] = now_iso()
        try:
            msg = BLOCKS[name].run()
            st.update({"ok": True, "last_ok": st["last_try"], "message": msg}); st.pop("error", None)
            print(f"{name}: {msg}")
        except Exception as e:
            st.update({"ok": False, "error": f"{type(e).__name__}: {e}"[:300]})
            print(f"{name}: FAILED"); traceback.print_exc()
        write_json("status.json", status)

if __name__ == "__main__":
    main(sys.argv[1:])
