from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from experiment_modules import RinexDataModule


def main() -> None:
    parser = argparse.ArgumentParser(description="快速检查 RINEX 观测文件和导航文件")
    parser.add_argument("--obs", default="data/sample/bjfs1170.26o", help="RINEX 观测文件路径")
    parser.add_argument("--nav", default="data/sample/brdc1170.26n", help="RINEX 导航文件路径")
    args = parser.parse_args()

    try:
        dataset = RinexDataModule().load(args.obs, args.nav)
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
    header = dataset.obs_header
    epochs = dataset.epochs
    nav_header = dataset.nav_header
    nav_records = dataset.nav_records

    print(f"观测文件版本：{header.version}")
    print(f"测站标识：{header.marker_name}")
    print(f"观测类型：{header.obs_types}")
    if header.obs_types_by_sys:
        print(f"分系统观测类型：{header.obs_types_by_sys}")
    print(f"历元数量：{len(epochs)}")
    if epochs:
        first = epochs[0]
        print(f"首个历元：{first.time}，卫星数={len(first.sat_obs)}")
        print(f"首个历元卫星：{list(first.sat_obs.keys())}")

    print(f"导航记录数：{len(nav_records)}")
    print(f"电离层 alpha 参数：{nav_header.ion_alpha}")
    print(f"电离层 beta 参数：{nav_header.ion_beta}")
    if nav_records:
        print(f"首条导航记录：{nav_records[0].prn}，时间={nav_records[0].epoch}")


if __name__ == "__main__":
    main()
