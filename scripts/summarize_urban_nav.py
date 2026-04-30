from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from data_inventory import summarize_dataset_directory, write_summary_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize UrbanNav observation/NMEA files")
    parser.add_argument("--root", default="data/datasets/urban_nav_hk_medium_urban_1", help="UrbanNav source directory")
    parser.add_argument("--json", default="data/datasets/urban_nav_hk_medium_urban_1/metadata.json")
    parser.add_argument("--csv", default="data/datasets/urban_nav_hk_medium_urban_1/observations.csv")
    args = parser.parse_args()

    summary = summarize_dataset_directory(args.root)
    write_summary_json(args.json, summary)
    _write_observation_csv(Path(args.csv), summary["observations"])

    print(f"Dataset: {summary['dataset_id']}")
    print(f"Observation files: {len(summary['observations'])}")
    print(f"Navigation files: {len(summary['navigation_files'])}")
    for row in summary["observations"]:
        print(
            f"{row['receiver']}: epochs={row['epochs']} systems={row['systems']} "
            f"bds_epochs={row['bds_epochs']} nmea={row['has_nmea']}"
        )
    print(f"Metadata saved: {args.json}")
    print(f"Observation summary saved: {args.csv}")


def _write_observation_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "receiver",
        "file",
        "version",
        "marker",
        "epochs",
        "systems",
        "bds_epochs",
        "bds_satellites",
        "approx_position_xyz",
        "has_nmea",
        "nmea_path",
        "time_first_obs",
        "time_system",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


if __name__ == "__main__":
    main()
