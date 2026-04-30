from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from redundancy import RedundancyCase, run_redundancy_cases, write_redundancy_summary


STATUS_TEXT = {
    "ok": "正常",
    "warning": "警告",
    "expected_error": "预期错误",
    "error": "错误",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="运行多种 RINEX 输入的冗余与容错测试")
    parser.add_argument("--output", default="results/redundancy_tests/summary.csv", help="汇总 CSV 输出路径")
    parser.add_argument("--max-epochs", type=int, default=20, help="每个可运行案例的最大历元数")
    args = parser.parse_args()

    root = Path("data/datasets")
    result_root = Path("results/redundancy_tests")
    stress = root / "redundancy_stress_2026_117"
    urban = root / "urban_nav_hk_medium_urban_1"

    cases = [
        RedundancyCase(
            name="sample_rinex2_gps",
            obs_path=root.parent / "sample" / "bjfs1170.26o",
            nav_path=root.parent / "sample" / "brdc1170.26n",
            systems=("G",),
            max_epochs=args.max_epochs,
            output_csv=result_root / "sample_rinex2_gps.csv",
        ),
        RedundancyCase(
            name="downloaded_rinex2_gzip_gps",
            obs_path=stress / "rinex" / "chan1170.26o.gz",
            nav_path=stress / "rinex" / "brdc1170.26n.gz",
            systems=("G",),
            max_epochs=args.max_epochs,
            output_csv=result_root / "downloaded_rinex2_gzip_gps.csv",
        ),
        RedundancyCase(
            name="downloaded_rinex3_gzip_gps_bds",
            obs_path=stress / "rinex" / "AUCK00NZL_R_20261170000_01D_30S_MO.rnx.gz",
            nav_path=stress / "rinex" / "BRDM00DLR_S_20261170000_01D_MN.rnx.gz",
            systems=("G", "C"),
            max_epochs=args.max_epochs,
            output_csv=result_root / "downloaded_rinex3_gzip_gps_bds.csv",
        ),
        RedundancyCase(
            name="urban_dynamic_gps_bds",
            obs_path=urban / "rinex" / "UrbanNav-HK-Medium-Urban-1.ublox.m8t.GC.obs",
            nav_path=urban / "rinex" / "BRDM00DLR_S_20211370000_01D_MN.rnx",
            systems=("G", "C"),
            max_epochs=args.max_epochs,
            output_csv=result_root / "urban_dynamic_gps_bds.csv",
        ),
        RedundancyCase(
            name="no_selected_system_warning",
            obs_path=root.parent / "sample" / "bjfs1170.26o",
            nav_path=root.parent / "sample" / "brdc1170.26n",
            systems=("C",),
            max_epochs=3,
            min_solutions=1,
        ),
        RedundancyCase(
            name="hatanka_requires_conversion",
            obs_path=stress / "raw" / "ABMF00GLP_R_20211370000_01D_30S_MO.crx.gz",
            nav_path=urban / "rinex" / "BRDM00DLR_S_20211370000_01D_MN.rnx",
            systems=("G", "C"),
            max_epochs=1,
            expect_error="Hatanaka",
        ),
    ]

    rows = run_redundancy_cases(cases)
    write_redundancy_summary(args.output, rows)
    for row in rows:
        print(
            f"{row['name']}：状态={STATUS_TEXT.get(str(row['status']), row['status'])} 系统={row['systems']} "
            f"有效解={row['solutions']} 信息={row['message']}"
        )

    unexpected = [row for row in rows if row["status"] == "error"]
    if unexpected:
        raise SystemExit(1)
    print(f"冗余测试汇总已保存：{args.output}")


if __name__ == "__main__":
    main()
