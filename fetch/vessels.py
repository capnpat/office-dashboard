"""Livestock carrier positions from aisstream.io (free key, AISSTREAM_API_KEY secret).

Listens to the AIS stream over the configured area for a short time each run
and keeps the latest position heard for each named vessel."""
import os, json, asyncio, time, re
from common import read_json, write_json, now_iso
from config import VESSELS, VESSEL_BOX, VESSEL_LISTEN_SECONDS

def norm(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())

WANT = {norm(v): v for v in VESSELS}

async def listen(key, seconds, ships):
    import websockets
    sub = {"APIKey": key, "BoundingBoxes": [VESSEL_BOX],
           "FilterMessageTypes": ["PositionReport", "ShipStaticData", "StandardClassBPositionReport"]}
    known = [int(m) for m, s in ships.items() if s.get("mmsi")]
    end = time.time() + seconds
    n = 0
    async with websockets.connect("wss://stream.aisstream.io/v0/stream", max_size=2**22) as ws:
        await ws.send(json.dumps(sub))
        while time.time() < end:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=max(1, end - time.time()))
            except asyncio.TimeoutError:
                break
            n += 1
            msg = json.loads(raw)
            md = msg.get("MetaData", {})
            mmsi = str(md.get("MMSI", ""))
            name = norm(md.get("ShipName"))
            if name not in WANT and mmsi not in ships:
                continue
            s = ships.setdefault(mmsi, {"mmsi": mmsi, "name": WANT.get(name, md.get("ShipName", "").strip()), "track": []})
            mt = msg.get("MessageType")
            body = msg.get("Message", {}).get(mt, {})
            if mt == "ShipStaticData":
                s["destination"] = (body.get("Destination") or "").strip()
                eta = body.get("Eta") or {}
                if eta.get("Month"):
                    s["eta"] = f"{eta.get('Day', 0):02d}/{eta.get('Month', 0):02d} {eta.get('Hour', 0):02d}{eta.get('Minute', 0):02d}"
                s["imo"] = body.get("ImoNumber")
            else:
                lat, lon = md.get("latitude"), md.get("longitude")
                if lat is None or lon is None:
                    continue
                s.update({"lat": lat, "lon": lon, "seen": now_iso(), "sog": body.get("Sog"), "cog": body.get("Cog"),
                          "status": body.get("NavigationalStatus")})
                tr = s.setdefault("track", [])
                if not tr or abs(tr[-1][0] - lat) + abs(tr[-1][1] - lon) > 0.05:
                    tr.append([round(lat, 3), round(lon, 3)])
                    del tr[:-40]
    return n

def run():
    prev = read_json("vessels.json", {}) or {}
    ships = prev.get("ships", {})
    key = os.environ.get("AISSTREAM_API_KEY")
    if not key:
        write_json("vessels.json", {"updated": now_iso(), "ships": ships, "watch": VESSELS, "note": "no API key"})
        return "skipped, no AISSTREAM_API_KEY secret"
    n = asyncio.run(listen(key, VESSEL_LISTEN_SECONDS, ships))
    write_json("vessels.json", {"updated": now_iso(), "ships": ships, "watch": VESSELS, "messages": n})
    heard = sum(1 for s in ships.values() if s.get("seen"))
    return f"{n} AIS messages, {heard} tracked vessels with a position"
