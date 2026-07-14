import os
import json
import argparse
from pathlib import Path
from collections import Counter
import csv
from pathlib import Path

# -------------------------------------------------------
# Load one GBFS snapshot
# -------------------------------------------------------

def load_snapshot(file_path):
    """
    Load a single GBFS snapshot.

    Returns
    -------
    dict
        Dictionary indexed by bike_id
    """

    with open(file_path, "r") as f:
        data = json.load(f)

    scooters = {}

    for feature in data["features"]:

        p = feature["properties"]
        g = feature["geometry"]["coordinates"]

        scooters[p["bike_id"]] = {
            "bike_id": p["bike_id"],
            "crm": p["current_range_meters"],
            "reserved": p["is_reserved"],
            "disabled": p["is_disabled"],
            "timestamp": p["last_reported"],
            "lon": g[0],
            "lat": g[1]
        }

    return scooters


# -------------------------------------------------------
# List snapshots
# -------------------------------------------------------

def get_snapshot_files(input_dir):
    """
    Returns snapshot files sorted chronologically.
    """

    files = sorted(Path(input_dir).glob("snapshot_*.json"))

    if len(files) == 0:
        raise RuntimeError("No snapshots found.")

    return files


# -------------------------------------------------------
# Output directory
# -------------------------------------------------------

def ensure_output_dir(output_dir):
    os.makedirs(output_dir, exist_ok=True)


# -------------------------------------------------------
# Save status csv
# -------------------------------------------------------

def save_status_csv(records, outfile):

    if len(records) == 0:
        return

    with open(outfile, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


# -------------------------------------------------------
# Print summary
# -------------------------------------------------------

def print_summary(counter):

    print("\n" + "=" * 55)
    print("MMV Status Summary")
    print("=" * 55)

    for status in [
        "Residential",
        "Startoff",
        "Dropoff",
        "Passby",
        "Disabled"
    ]:
        print(f"{status:<15}: {counter[status]}")

    print("=" * 55)

# -------------------------------------------------------
# Infer Disabled and Passby
# -------------------------------------------------------

def infer_status(previous, current, nxt, snapshot_name, counter):

    records = []

    for bike_id, scooter in current.items():

        status = "Unknown"

        # -------------------------------------------------
        # 1. Disabled
        # -------------------------------------------------
        if scooter["disabled"]:

            status = "Disabled"

        # -------------------------------------------------
        # 2. Passby
        # -------------------------------------------------
        elif bike_id in nxt:

            nxt_scooter = nxt[bike_id]

            crm_drop = nxt_scooter["crm"] < scooter["crm"]

            moved = (
                scooter["lat"] != nxt_scooter["lat"] or
                scooter["lon"] != nxt_scooter["lon"]
            )

            reserved = (
                scooter["reserved"] and
                nxt_scooter["reserved"]
            )

            if crm_drop and moved and reserved:

                status = "Passby"

        # -------------------------------------------------
        # 3. Residential / Startoff / Dropoff
        # -------------------------------------------------
        if status == "Unknown":

            present_prev = bike_id in previous
            present_next = bike_id in nxt

            # -------------------------
            # Scooter existed previously
            # -------------------------
            if present_prev:

                prev = previous[bike_id]

                same_crm = (
                    prev["crm"] == scooter["crm"]
                )

                same_location = (
                    prev["lat"] == scooter["lat"] and
                    prev["lon"] == scooter["lon"]
                )

                close_time = (
                    abs(
                        scooter["timestamp"] -
                        prev["timestamp"]
                    ) <= 600
                )

                if same_crm and same_location and close_time:

                    if not present_next:

                        # disappeared in next snapshot
                        status = "Startoff"

                    else:

                        # still present → Residential
                        status = "Residential"

            # -------------------------
            # Newly appeared scooter
            # -------------------------
            else:

                if present_next:

                    status = "Dropoff"

        # -------------------------------------------------
        # Save result
        # -------------------------------------------------
        counter[status] += 1

        records.append({

            "snapshot": snapshot_name,
            "bike_id": bike_id,
            "status": status,
            "crm": scooter["crm"],
            "reserved": scooter["reserved"],
            "disabled": scooter["disabled"],
            "timestamp": scooter["timestamp"],
            "longitude": scooter["lon"],
            "latitude": scooter["lat"]

        })

    return records
# -------------------------------------------------------
# Main
# -------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input_dir",
        required=True,
        help="Directory containing GBFS snapshots"
    )

    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory to save inferred status"
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot_files = sorted(input_dir.glob("snapshot_*.json"))

    print(f"Found {len(snapshot_files)} snapshots.")

    if len(snapshot_files) < 2:
        raise ValueError("Need at least two snapshots for status inference.")

    # Initialize AFTER the check
    summary_counter = Counter()
    records = []

    for i in range(1, len(snapshot_files)-1):

        previous = load_snapshot(snapshot_files[i-1])
        current = load_snapshot(snapshot_files[i])
        nxt = load_snapshot(snapshot_files[i+1])

        snapshot_name = snapshot_files[i].stem

        print(f"Processing {snapshot_name}")

        snapshot_records = infer_status(previous,current,nxt,snapshot_name,summary_counter)

        outfile = output_dir / f"{snapshot_name}.csv"

        save_status_csv(snapshot_records, outfile)

        records.extend(snapshot_records)

    print_summary(summary_counter)

    save_status_csv(
        records,
        output_dir / "all_status.csv"
    )

if __name__ == "__main__":
    main()