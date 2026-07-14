"""
k_anonymity.py

Grid-based k-anonymity for GBFS Micromobility Data.

This script spatially aggregates scooters into grid cells and
removes cells containing fewer than k vehicles.

Usage
-----
python k_anonymity.py \
    --input data/raw/free_bike_status.json \
    --output data/anonymized.json \
    --k 3 \
    --grid 0.001
"""

import json
import math
import argparse
from collections import defaultdict
import os


def grid_cell(lat, lon, grid_size):
    """
    Assign latitude/longitude to a spatial grid.

    Parameters
    ----------
    lat : float
    lon : float
    grid_size : float

    Returns
    -------
    tuple
        (grid_x, grid_y)
    """

    gx = math.floor(lon / grid_size)
    gy = math.floor(lat / grid_size)

    return gx, gy


def apply_k_anonymity(features, k=3, grid_size=0.001):

    groups = defaultdict(list)

    for feature in features:

        lon, lat = feature["geometry"]["coordinates"]

        cell = grid_cell(lat, lon, grid_size)

        groups[cell].append(feature)

    anonymized = []

    removed = 0

    for cell, scooters in groups.items():

        if len(scooters) >= k:
            anonymized.extend(scooters)
        else:
            removed += len(scooters)

    return anonymized, removed, len(features)


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
        help="Directory to save anonymized snapshots"
    )

    parser.add_argument(
        "--k",
        type=int,
        default=3
    )

    parser.add_argument(
        "--grid",
        type=float,
        default=0.001,
        help="Grid size in degrees (~110 m)"
    )

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    total_records = 0
    retained_records = 0
    removed_records = 0
    processed_files = 0

    files = sorted(
        f for f in os.listdir(args.input_dir)
        if f.endswith(".json")
    )

    for filename in files:

        input_path = os.path.join(args.input_dir, filename)

        with open(input_path, "r") as f:
            data = json.load(f)

        anonymized, removed, total = apply_k_anonymity(
            data["features"],
            args.k,
            args.grid
        )

        data["features"] = anonymized

        output_path = os.path.join(args.output_dir, filename)

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        processed_files += 1
        total_records += total
        retained_records += len(anonymized)
        removed_records += removed

    print("\n" + "=" * 60)
    print("GBFS k-Anonymity Report")
    print("=" * 60)
    print(f"Snapshots processed : {processed_files}")
    print(f"Total records       : {total_records}")
    print(f"Retained records    : {retained_records}")
    print(f"Removed records     : {removed_records}")

    if total_records > 0:
        print(f"Removal percentage  : {100 * removed_records / total_records:.2f}%")

    print(f"k                   : {args.k}")
    print(f"Grid size           : {args.grid} (~110 m)")
    print(f"Output directory    : {args.output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()