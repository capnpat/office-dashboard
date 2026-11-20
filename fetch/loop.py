"""Long-running updater for GitHub Actions.

GitHub's scheduler often skips runs, so one job stays up for about five and a
half hours: every 30 minutes it runs the blocks that are due and pushes the
data, and in between it listens to the AIS stream for the livestock carriers.
When it finishes it starts the next job itself."""
import os, sys, time, subprocess, datetime as dt
import run as runner
import vessels

CYCLE = 30 * 60
# Seconds each block may take per cycle before it is stopped
BLOCK_LIMITS = {"mla": 600, "disease": 240, "econ": 420, "exports": 240, "weather": 240}
DEADLINE = time.time() + float(os.environ.get("LOOP_MINUTES", "330")) * 60

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True)

def push(msg):
    sh("git", "add", "data")
    if sh("git", "diff", "--cached", "--quiet").returncode == 0:
        return
    sh("git", "commit", "-q", "-m", msg)
    for _ in range(3):
        sh("git", "pull", "-q", "--rebase", "origin", "main")
        if sh("git", "push", "-q", "origin", "HEAD:main").returncode == 0:
            print("  pushed", flush=True); return
        time.sleep(5)
    print("  push failed", flush=True)

def main():
    first = True
    while time.time() < DEADLINE - 120:
        t0 = time.time()
        stamp = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
        print(f"== cycle {stamp}", flush=True)
        force = ["--force"] if first and "--force" in sys.argv else []
        for b in [b for b in runner.BLOCKS if b != "vessels"]:
            limit = BLOCK_LIMITS.get(b, 180)
            try:
                r = subprocess.run([sys.executable, "-u", "run.py", *force, b], capture_output=True, text=True, timeout=limit)
                print((r.stdout + r.stderr).strip()[-600:], flush=True)
            except subprocess.TimeoutExpired:
                print(f"{b}: stopped after {limit}s", flush=True)
                st = runner.read_json("status.json", {}) or {}
                st.setdefault(b, {}).update({"ok": False, "error": f"timed out after {limit}s"})
                runner.write_json("status.json", st)
            if b in ("markets", "weather"):
                push(f"Data update {stamp}")
        push(f"Data update {stamp}")
        first = False
        listen = min(CYCLE - (time.time() - t0) - 60, DEADLINE - time.time() - 120)
        if listen > 60 and os.environ.get("AISSTREAM_API_KEY"):
            st = runner.read_json("status.json", {}) or {}
            s = st.setdefault("vessels", {}); s["last_try"] = runner.now_iso()
            try:
                msg = vessels.run(listen=int(listen))
                s.update({"ok": True, "last_ok": s["last_try"], "message": msg}); s.pop("error", None)
            except Exception as e:
                s.update({"ok": False, "error": f"{type(e).__name__}: {e}"[:300]})
            runner.write_json("status.json", st)
            print(f"vessels: {s.get('message') or s.get('error')}", flush=True)
            push(f"Vessel positions {dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%MZ')}")
        rest = CYCLE - (time.time() - t0)
        if rest > 0 and time.time() + rest < DEADLINE:
            time.sleep(rest)

if __name__ == "__main__":
    main()
