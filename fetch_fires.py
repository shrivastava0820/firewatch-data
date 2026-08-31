#!/usr/bin/env python3
"""Fetch global active-fire detections from NASA FIRMS, slim, dedup, publish."""

import csv, datetime as dt, io, json, os, sys, urllib.request

SENSORS = ["VIIRS_NOAA20_NRT"]
DAYS = 1
OUT = "data/latest.json"
BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

def fetch(key, sensor):
    url = f"{BASE}/{key}/{sensor}/world/{DAYS}"
    with urllib.request.urlopen(url, timeout=300) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode())))


def slim(row):
        if row["confidence"] == "l":
            return None

        date = row["acq_date"]
        t = str(row["acq_time"]).zfill(4)
        acq = f"{date}T{t[:2]}:{t[2:]}:00Z"

        return {
            "lat": round(float(row["latitude"]), 5),
            "lng": round(float(row["longitude"]), 5),
            "bright": float(row["bright_ti4"]),
            "frp": float(row["frp"]),
            "conf": row["confidence"],
            "acq": acq,
            "sat": row["satellite"],
            "daynight": row["daynight"],
        }


def dedup(records):
    records = sorted(records, key=lambda r: -r["frp"])
    seen = {}
    for r in records:
        key = (round(r["lat"] / 0.01), round(r["lng"] / 0.01))
        if key not in seen:
            seen[key] = r
    return list(seen.values())


def write_json(path, payload):
    """Write atomically so a crash never leaves a half-written file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    os.replace(tmp, path)


def main():
    key = os.environ.get("FIRMS_MAP_KEY")
    if not key:
        sys.exit("FIRMS_MAP_KEY not set")

    rows = []
    for s in SENSORS:
        try:
            rows.extend(fetch(key, s))
        except Exception as e:
            print(f"[{s}] failed: {type(e).__name__}: {e}", file=sys.stderr)

    if not rows:
        sys.exit("no data fetched, refusing to overwrite")

    kept = []
    for r in rows:
        s = slim(r)
        if s is not None:
            kept.append(s)

    unique = dedup(kept)
    #print(len(kept), "->", len(unique))

    out = {
        "schema": "firewatch/v1",
        "generated_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_hours": 24,
        "counts": {
            "raw": len(rows),
            "kept": len(kept),
            "deduped": len(unique),
        },
        "source": {
            "provider": "NASA FIRMS",
            "sensors": SENSORS,
            "attribution": "data: NASA FIRMS / LANCE",
        },
        "detections": unique,
    }

    write_json(OUT, out)
    print(f"wrote {OUT}: {len(rows)} raw -> {len(kept)} kept -> {len(unique)} unique")
 
    # One archive file per UTC day, written by the first run after midnight.
    apath = "data/archive/" + dt.datetime.now(dt.UTC).strftime("%Y/%m/%d") + ".json"
    if os.path.exists(apath):
        print("archive exists, skipping")
    else:
        write_json(apath, unique)
        print("archived", apath)


if __name__ == "__main__":
    main()
