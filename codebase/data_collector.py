# -*- coding: utf-8 -*-
import requests
import json
import time
from datetime import datetime, timezone
import os

URL = "API" #replace with API from BMT or other MMV API
OUTPUT_FILE = "free_bike_status_24h.jsonl"

INTERVAL = 600  # 10 minutes
SNAPSHOTS = 144

start_time = time.time()

for i in range(SNAPSHOTS):

    ts = datetime.now(timezone.utc).isoformat()

    try:
        r = requests.get(URL, timeout=30)
        r.raise_for_status()

        record = {
            "collector_timestamp": ts,
            "snapshot": r.json()
        }

        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
            f.flush()
            os.fsync(f.fileno())

        print(f"Saved snapshot {i+1}/{SNAPSHOTS} at {ts}")
        print(f"[{i+1}/{SNAPSHOTS}] Snapshot written at {ts}")

    except Exception as e:
        print(f"Error: {e}")

    next_run = start_time + (i + 1) * INTERVAL
    sleep_time = max(0, next_run - time.time())
    time.sleep(sleep_time)
    
    


    