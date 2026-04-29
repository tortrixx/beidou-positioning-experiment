from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from plotting import plot_error_and_dop, plot_trajectory


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot positioning results from CSV")
    parser.add_argument("--csv", default="results.csv", help="Results CSV path")
    parser.add_argument("--save-dir", default="", help="Save plots to directory instead of show")
    args = parser.parse_args()

    times = []
    horiz = []
    three_d = []
    pdop = []
    lat = []
    lon = []

    with open(args.csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            times.append(idx)
            horiz.append(float(row["horiz"]))
            three_d.append(float(row["three_d"]))
            pdop.append(float(row["pdop"]))
            lat.append(float(row["lat"]))
            lon.append(float(row["lon"]))

    if args.save_dir:
        err_path = f"{args.save_dir}/error_dop.png"
        traj_path = f"{args.save_dir}/trajectory.png"
        saved_error = plot_error_and_dop(times, horiz, three_d, pdop, save_path=err_path)
        saved_traj = plot_trajectory(lat, lon, save_path=traj_path)
        if saved_error and saved_traj:
            print(f"Plots saved: {err_path}, {traj_path}")
        else:
            raise RuntimeError("Plot generation failed")
    else:
        plot_error_and_dop(times, horiz, three_d, pdop)
        plot_trajectory(lat, lon)


if __name__ == "__main__":
    main()
