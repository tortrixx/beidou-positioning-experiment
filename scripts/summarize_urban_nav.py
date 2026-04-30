from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from data_inventory import summarize_dataset_directory, write_summary_json


def main() -> None:
    parser = argparse.ArgumentParser(description="汇总 UrbanNav 观测文件和 NMEA 文件信息")
    parser.add_argument("--root", default="data/datasets/urban_nav_hk_medium_urban_1", help="UrbanNav 数据目录")
    parser.add_argument("--json", default="data/datasets/urban_nav_hk_medium_urban_1/metadata.json")
    parser.add_argument("--csv", default="data/datasets/urban_nav_hk_medium_urban_1/observations.csv")
    args = parser.parse_args()

    summary = summarize_dataset_directory(args.root)
    write_summary_json(args.json, summary)
    _write_observation_csv(Path(args.csv), summary["observations"])

    print(f"数据集：{summary['dataset_id']}")
    print(f"观测文件数：{len(summary['observations'])}")
    print(f"导航文件数：{len(summary['navigation_files'])}")
    for row in summary["observations"]:
        print(
            f"{row['receiver']}：历元数={row['epochs']} 系统={row['systems']} "
            f"北斗历元数={row['bds_epochs']} NMEA={row['has_nmea']}"
        )
    print(f"元数据已保存：{args.json}")
    print(f"观测摘要已保存：{args.csv}")


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
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
