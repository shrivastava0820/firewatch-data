# firewatch-data

Global active-fire detections from NASA FIRMS, fetched hourly and
published as slim JSON for a static frontend.

No server, no database. GitHub Actions runs the fetcher on a cron,
commits the result to this repo, and the frontend reads it directly
from raw.githubusercontent.com.

## Data
65,057 raw → 55,736 after the confidence filter → 37,463 unique
Source: NASA FIRMS area API, VIIRS NOAA-20 and NOAA-21 (near real-time),
global bounding box, 24-hour window.

Global detections are available roughly 3 hours after satellite
overpass, so the fetch runs hourly — faster gains nothing.

Low-confidence detections are dropped. Detections seen by both
satellites are deduplicated to ~1 km, keeping the higher FRP reading.

## Output

- `data/latest.json` — current snapshot, overwritten each run
- `data/archive/YYYY/MM/DD.json` — one file per UTC day, written once

### `latest.json`

    {
      "schema": "firewatch/v1",
      "generated_utc": "2026-08-31T14:00:00Z",
      "window_hours": 24,
      "counts": { "raw": 0, "kept": 0, "deduped": 0 },
      "detections": [
        {
          "lat": 12.34567,
          "lng": 76.54321,
          "bright": 331.2,
          "frp": 4.8,
          "conf": "n",
          "acq": "2026-08-31T09:12:00Z",
          "sat": "NOAA-20",
          "daynight": "D"
        }
      ]
    }

## Setup

Requires a free FIRMS MAP_KEY (https://firms.modaps.eosdis.nasa.gov/api/map_key/),
stored as the repo secret `FIRMS_MAP_KEY`.

    export FIRMS_MAP_KEY=...
    python fetch_fires.py

Python 3.11+, standard library only.

## Attribution

Data: NASA FIRMS / LANCE. NASA supports full and open sharing of this
data and asks that it be credited when redistributed.

## Licence

MIT (code). Data is NASA's, not mine.