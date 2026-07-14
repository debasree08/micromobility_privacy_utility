"""
------------------------------------------------------------
Threat Model Reconstruction Attack
Algorithm 1 from the paper.
------------------------------------------------------------
"""

import json
import argparse

from pathlib import Path
from collections import Counter
from dataclasses import dataclass, field

from math import radians, sin, cos, sqrt, atan2
import pandas as pd
from collections import Counter

# ==========================================================
# Track Object
# ==========================================================

# @dataclass
# class Track:

#     bike_id: str

#     crm: int

#     origin: tuple
#     origin_time: int

#     destination: tuple = None
#     destination_time: int = None

#     mapping: str = None

#     candidates: list = field(default_factory=list)


@dataclass
class Track:

    bike_id: str

    crm: int

    origin_lat: float
    origin_lon: float
    origin_time: int

    destination_lat: float = None
    destination_lon: float = None
    destination_time: int = None

    mapping: str = None

    candidates: list = field(default_factory=list)

# ==========================================================
# Load one snapshot
# ==========================================================

def load_snapshot(filepath):

    with open(filepath) as f:
        data = json.load(f)

    scooters = []

    for feature in data["features"]:

        p = feature["properties"]
        g = feature["geometry"]

        scooters.append({

            "bike_id": p["bike_id"],

            "crm": p["current_range_meters"],

            "timestamp": p["last_reported"],

            "reserved": p["is_reserved"],

            "disabled": p["is_disabled"],

            "lat": g["coordinates"][1],

            "lon": g["coordinates"][0]

        })

    return scooters
# ==========================================================
# Load all snapshot
# ==========================================================
def load_all_snapshots(input_dir):

    files = sorted(

        Path(input_dir).glob("snapshot_*.json")

    )

    snapshots = []

    for f in files:

        snapshots.append(

            load_snapshot(f)

        )

    return files, snapshots

# ==========================================================
# Compute harvesine distance
# ==========================================================
def haversine(lat1, lon1, lat2, lon2):

    R = 6371

    dlat = radians(lat2-lat1)
    dlon = radians(lon2-lon1)

    a = (
        sin(dlat/2)**2
        +
        cos(radians(lat1))
        *
        cos(radians(lat2))
        *
        sin(dlon/2)**2
    )

    c = 2 * atan2(

        sqrt(a),

        sqrt(1-a)

    )

    return R*c

# ==========================================================
# CRM frequency
# ==========================================================

def compute_crm_frequency(snapshot):

    counter = Counter()

    for scooter in snapshot:

        counter[

            scooter["crm"]

        ] += 1

    return counter
# ==========================================================
# Rare MMVS
# ==========================================================

def initialize_tracks(snapshot, crm_frequency, threshold=10):

    tracks = []

    for scooter in snapshot:

        if crm_frequency[
            scooter["crm"]
        ] >= threshold:

            continue

        tracks.append(

            Track(

                bike_id=scooter["bike_id"],

                crm=scooter["crm"],

                origin_lat=scooter["lat"],

                origin_lon=scooter["lon"],

                origin_time=scooter["timestamp"]

            )

        )

    return tracks
# ==========================================================
# Battery consistency
# ==========================================================

def battery_consistent(

    start_crm,

    end_crm,

    distance

):

    crm_drop = start_crm - end_crm

    if crm_drop <= 0:

        return False

    if distance > crm_drop * 1.25:

        return False

    return True
    return tracks

# ==========================================================
# speed feasibility
# ==========================================================


def speed_feasible(

    distance,

    dt,

    avg_speed=10

):

    if dt <= 0:

        return False

    speed = distance / (dt / 3600)

    return speed <= avg_speed

# ==========================================================
# Snapshot lookup
# ==========================================================


def snapshot_lookup(snapshot):

    lookup = {}

    for scooter in snapshot:

        lookup[
            scooter["bike_id"]
        ] = scooter

    return lookup

# ==========================================================
# Detect disappearance
# ==========================================================


def has_disappeared(

    track,

    next_lookup

):

    return track.bike_id not in next_lookup

# ==========================================================
# Initialize reconstruction attack
# ==========================================================

def initialize_reconstruction(

    tracks,

    next_snapshot

):

    next_lookup = snapshot_lookup(

        next_snapshot

    )

    active_tracks = []

    for track in tracks:

        if has_disappeared(

            track,

            next_lookup

        ):

            active_tracks.append(track)

    return active_tracks


# ==========================================================
# Candidate validator
# ==========================================================


def is_candidate(

    track,

    scooter

):

    # CRM should decrease

    if scooter["crm"] >= track.crm:

        return False

    # Travel time

    dt = (

        scooter["timestamp"]

        -

        track.origin_time

    )

    if dt <= 0:

        return False

    # Travel distance

    distance = haversine(

        track.origin_lat,

        track.origin_lon,

        scooter["lat"],

        scooter["lon"]

    )

    # Speed constraint

    if not speed_feasible(

        distance,

        dt

    ):

        return False

    # Battery constraint

    if not battery_consistent(

        track.crm,

        scooter["crm"],

        distance

    ):

        return False
    # crm_drop = (

    #     track.crm

    #     -

    #     scooter["crm"]

    # )

    # if not battery_feasible(

    #     distance,

    #     crm_drop

    # ):

    #     return False

    return True

# ==========================================================
# Search one snapshot
# ==========================================================
def search_snapshot(

    track,

    snapshot

):

    candidates = []

    for scooter in snapshot:

        if is_candidate(

            track,

            scooter

        ):

            candidates.append(scooter)

    return candidates

# ==========================================================
# Search all future snapshot
# ==========================================================

def continue_track(

    track,

    future_snapshots

):

    for snapshot in future_snapshots:

        candidates = search_snapshot(

            track,

            snapshot

        )

        if len(candidates) > 0:

            track.candidates = candidates

            return track

    return track



# ==========================================================
# One to one case
# ==========================================================

def classify_track(track):

    n = len(track.candidates)

    if n == 0:

        track.mapping = "No Match"

        return track

    elif n == 1:

        track.mapping = "One-to-One"

        candidate = track.candidates[0]

        track.destination_lat = candidate["lat"]
        track.destination_lon = candidate["lon"]
        track.destination_time = candidate["timestamp"]

    else:

        track.mapping = "One-to-Many"

        best = min(

            track.candidates,

            key=lambda x: abs(
                track.crm - x["crm"]
            )

        )

        track.destination_lat = best["lat"]
        track.destination_lon = best["lon"]
        track.destination_time = best["timestamp"]

    return track

from collections import defaultdict

# ==========================================================
# Many to one case
# ==========================================================

def detect_many_to_one(tracks):

    groups = defaultdict(list)

    for track in tracks:

        if track.mapping == "No Match":

            continue

        key = (

            track.destination_lat,

            track.destination_lon,

            track.destination_time

        )

        groups[key].append(track)

    for group in groups.values():

        if len(group) > 1:

            for t in group:

                t.mapping = "Many-to-One"

    return tracks


# ==========================================================
# Process all tracks
# ==========================================================

def classify_tracks(tracks):

    classified = []

    for track in tracks:

        classified.append(

            classify_track(track)

        )

    classified = detect_many_to_one(

        classified

    )

    return classified



# ==========================================================
# Print statistics
# ==========================================================

def print_statistics(tracks):

    counter = Counter()

    for t in tracks:

        counter[t.mapping] += 1

    print()

    print("="*50)

    print("Trajectory Inference Summary")

    print("="*50)

    for k,v in counter.items():

        print(f"{k:15s}: {v}")

    print("="*50)


# ==========================================================
# Save results
# ==========================================================

def save_results(

    tracks,

    outfile

):

    rows = []

    for t in tracks:

        rows.append({

            "bike_id": t.bike_id,

            "crm": t.crm,

            "origin_lat": t.origin_lat,

            "origin_lon": t.origin_lon,

            "origin_time": t.origin_time,

            "destination_lat": t.destination_lat,

            "destination_lon": t.destination_lon,

            "destination_time": t.destination_time,

            "mapping": t.mapping

        })

    df = pd.DataFrame(rows)

    df.to_csv(

        outfile,

        index=False

    )

  



if __name__ == "__main__":

    
    
    files, snapshots = load_all_snapshots("synthetic_data")

    print(len(files))

    print(len(snapshots))

    crm = compute_crm_frequency(

    snapshots[0]

    )

    tracks = initialize_tracks(

        snapshots[0],

        crm

    )

    print()

    print("Initialized tracks :", len(tracks))

    active_tracks = initialize_reconstruction(

        tracks,

        snapshots[1]

    )

    print("Startoff candidates :", len(active_tracks))

    reconstructed_tracks = []

    for track in active_tracks:

        reconstructed_tracks.append(

            continue_track(

                track,

                snapshots[2:]

            )

        )

    classified_tracks = classify_tracks(

    reconstructed_tracks

    )

    print_statistics(

        classified_tracks

    )

    save_results(

        classified_tracks,

        "trajectory_results.csv"

    )

    print(

        "Tracks reconstructed:",

        len(reconstructed_tracks)

    )

