import json
import pandas as pd

# INPUT_FILE = "free_bike_status_24h.jsonl"
INPUT_FILE = "input.jsonl"
OUTPUT_FILE = "free_bike_status.csv"

rows = []

with open(INPUT_FILE, "r", encoding="utf-8") as f:

    for line in f:

        record = json.loads(line)

        collector_timestamp = record["collector_timestamp"]

        bikes = record["snapshot"]["data"]["bikes"]

        for bike in bikes:

            rows.append({
                "collector_timestamp": collector_timestamp,
                "bike_id": bike.get("bike_id"),
                "lat": bike.get("lat"),
                "lon": bike.get("lon"),
                "is_reserved": bike.get("is_reserved"),
                "is_disabled": bike.get("is_disabled"),
                "vehicle_type_id": bike.get("vehicle_type_id"),
                "last_reported": bike.get("last_reported"),
                "current_range_meters": bike.get("current_range_meters")
            })

df = pd.DataFrame(rows)

df.to_csv(OUTPUT_FILE, index=False)

print(f"Saved {len(df)} rows to {OUTPUT_FILE}")