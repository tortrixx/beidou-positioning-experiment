from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from batch import summarize_result_csv, write_summary


DATASETS = [
    ("bjfs_2026_117_gps", "G", "results/datasets/bjfs_2026_117_gps/results.csv"),
    ("daej_2026_117_gps", "G", "results/datasets/daej_2026_117_gps/results.csv"),
    ("hksl_2026_117_gps", "G", "results/datasets/hksl_2026_117_gps/results.csv"),
    ("twtf_2026_117_gps_from_mixed", "G", "results/datasets/twtf_2026_117_gps_from_mixed/results.csv"),
    ("twtf_2026_117_bds", "C", "results/datasets/twtf_2026_117_bds/results.csv"),
    ("twtf_2026_117_gps_bds", "G,C", "results/datasets/twtf_2026_117_gps_bds/results.csv"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize batch positioning result CSV files")
    parser.add_argument("--output", default="results/summary.csv", help="Output summary CSV path")
    args = parser.parse_args()

    summaries = []
    for dataset, system, csv_path in DATASETS:
        path = Path(csv_path)
        if not path.exists():
            print(f"Skip missing result: {path}")
            continue
        summary = summarize_result_csv(dataset, system, path)
        summaries.append(summary)
        print(
            f"{dataset} [{system}] epochs={summary['epochs']} "
            f"horiz_rms={summary['horiz_rms']:.3f} 3d_rms={summary['3d_rms']:.3f}"
        )

    if not summaries:
        raise RuntimeError("No result CSV files found; run scripts/run_continuous.py first")
    write_summary(args.output, summaries)
    print(f"Summary saved: {args.output}")


if __name__ == "__main__":
    main()
