import os
import json
import argparse
from pathlib import Path
from collections import Counter
from dataclasses import dataclass, field


# ==========================================================
# Track Object
# ==========================================================

@dataclass
class Track:

    track_id: int

    bike_id: str

    crm: int

    origin_lat: float
    origin_lon: float

    current_lat: float
    current_lon: float

    start_time: int
    current_time: int

    history: list = field(default_factory=list)

    destination=None

    state="ACTIVE"

    mapping="UNKNOWN"


# ==========================================================
# Load one snapshot
# ==========================================================

def load_snapshot(path):

    with open(path) as f:

        data = json.load(f)

    scooters = []

    for feature in data["features"]:

        p = feature["properties"]

        g = feature["geometry"]

        scooters.append({

            "bike_id": p["bike_id"],

            "crm": p["current_range_meters"],

            "reserved": p["is_reserved"],

            "disabled": p["is_disabled"],

            "timestamp": p["last_reported"],

            "lat": g["coordinates"][1],

            "lon": g["coordinates"][0]

        })

    return scooters


# ==========================================================
# CRM Frequency
# ==========================================================

def compute_crm_frequency(snapshot):

    counter = Counter()

    for scooter in snapshot:

        counter[scooter["crm"]] += 1

    return counter


# ==========================================================
# Filter Rare CRM
# ==========================================================

def filter_rare_crm(snapshot, crm_frequency, threshold=10):

    filtered = []

    for scooter in snapshot:

        if crm_frequency[scooter["crm"]] < threshold:

            filtered.append(scooter)

    return filtered


# ==========================================================
# Initialize Tracks
# ==========================================================

def initialize_tracks(snapshot, crm_frequency):

    tracks = []

    track_id = 0

    grouped = {}

    for scooter in snapshot:

        crm = scooter["crm"]

        grouped.setdefault(crm, []).append(scooter)

    for crm, scooters in grouped.items():

        if crm_frequency[crm] >= 10:

            continue

        # Algorithm Line 6
        if len(scooters) == 1:

            s = scooters[0]

            t = Track(

                track_id=track_id,

                bike_id=s["bike_id"],

                crm=crm,

                origin_lat=s["lat"],
                origin_lon=s["lon"],

                current_lat=s["lat"],
                current_lon=s["lon"],

                start_time=s["timestamp"],

                current_time=s["timestamp"]

            )

            t.history.append(

                (

                    s["timestamp"],

                    s["lat"],

                    s["lon"],

                    crm

                )

            )

            tracks.append(t)

            track_id += 1

    return tracks


# ==========================================================
# Save initialized tracks
# ==========================================================

def save_tracks(tracks, outfile):

    rows = []

    for t in tracks:

        rows.append({

            "track_id": t.track_id,

            "bike_id": t.bike_id,

            "crm": t.crm,

            "origin_lat": t.origin_lat,

            "origin_lon": t.origin_lon,

            "timestamp": t.start_time,

            "state": t.state

        })

    with open(outfile, "w") as f:

        json.dump(rows, f, indent=2)


# ==========================================================
# Main
# ==========================================================

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
        help="Directory to save initialized tracks"
    )

    parser.add_argument(
        "--crm_threshold",
        type=int,
        default=10
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)

    output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot_files = sorted(input_dir.glob("snapshot_*.json"))

    print(f"\nFound {len(snapshot_files)} snapshots")

    total_tracks = 0

    for snapshot_file in snapshot_files:

        print(f"Processing {snapshot_file.name}")

        snapshot = load_snapshot(snapshot_file)

        crm_frequency = compute_crm_frequency(snapshot)

        tracks = initialize_tracks(snapshot, crm_frequency)

        outfile = output_dir / f"{snapshot_file.stem}_tracks.json"

        save_tracks(tracks, outfile)

        total_tracks += len(tracks)

        print(f"Initialized {len(tracks)} tracks")

    print("\n=======================================")

    print(f"Total initialized tracks : {total_tracks}")

    print("=======================================")


if __name__ == "__main__":

    main()