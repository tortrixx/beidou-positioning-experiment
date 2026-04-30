from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from experiment_modules import RinexDataModule


def main() -> None:
    parser = argparse.ArgumentParser(description="Quick RINEX 2.11 inspection")
    parser.add_argument("--obs", default="data/sample/bjfs1170.26o", help="Path to RINEX obs file")
    parser.add_argument("--nav", default="data/sample/brdc1170.26n", help="Path to RINEX nav file")
    args = parser.parse_args()

    try:
        dataset = RinexDataModule().load(args.obs, args.nav)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    header = dataset.obs_header
    epochs = dataset.epochs
    nav_header = dataset.nav_header
    nav_records = dataset.nav_records

    print(f"OBS version: {header.version}")
    print(f"Marker: {header.marker_name}")
    print(f"Obs types: {header.obs_types}")
    if header.obs_types_by_sys:
        print(f"Obs types by system: {header.obs_types_by_sys}")
    print(f"Epochs: {len(epochs)}")
    if epochs:
        first = epochs[0]
        print(f"First epoch: {first.time} sats={len(first.sat_obs)}")
        print(f"First epoch satellites: {list(first.sat_obs.keys())}")

    print(f"NAV records: {len(nav_records)}")
    print(f"ION alpha: {nav_header.ion_alpha}")
    print(f"ION beta: {nav_header.ion_beta}")
    if nav_records:
        print(f"First NAV PRN: {nav_records[0].prn} at {nav_records[0].epoch}")


if __name__ == "__main__":
    main()
