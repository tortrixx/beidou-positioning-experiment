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
    ("urban_nav_hk_medium_urban_1_bds_200", "C", "results/datasets/urban_nav_hk_medium_urban_1_bds/results.csv"),
    ("urban_nav_hk_medium_urban_1_gps_bds_200", "G,C", "results/datasets/urban_nav_hk_medium_urban_1_gps_bds/results.csv"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="汇总多组定位结果 CSV 的精度指标")
    parser.add_argument("--output", default="results/summary.csv", help="汇总 CSV 输出路径")
    args = parser.parse_args()

    summaries = []
    for dataset, system, csv_path in DATASETS:
        path = Path(csv_path)
        if not path.exists():
            print(f"跳过缺失结果：{path}")
            continue
        summary = summarize_result_csv(dataset, system, path)
        summaries.append(summary)
        print(
            f"{dataset} [{system}] 历元数={summary['epochs']} "
            f"水平 RMS={summary['horiz_rms']:.3f} 三维 RMS={summary['3d_rms']:.3f}"
        )

    if not summaries:
        raise RuntimeError("未找到结果 CSV，请先运行 scripts/run_continuous.py")
    write_summary(args.output, summaries)
    print(f"汇总结果已保存：{args.output}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
