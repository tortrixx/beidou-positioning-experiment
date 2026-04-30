from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from plotting import plot_error_and_dop, plot_trajectory


def main() -> None:
    parser = argparse.ArgumentParser(description="从定位结果 CSV 绘制误差图和轨迹图")
    parser.add_argument("--csv", default="results.csv", help="定位结果 CSV 路径")
    parser.add_argument("--save-dir", default="", help="保存图像的目录；为空则弹窗显示")
    args = parser.parse_args()

    times = []
    horiz = []
    three_d = []
    pdop = []
    sat_counts = []
    lat = []
    lon = []

    with open(args.csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            times.append(idx)
            horiz.append(float(row["horiz"]))
            three_d.append(float(row["three_d"]))
            pdop.append(float(row["pdop"]))
            sat_counts.append(int(float(row["used_sats"])))
            lat.append(float(row["lat"]))
            lon.append(float(row["lon"]))

    if not times:
        print(f"CSV 中没有结果行：{args.csv}，已跳过绘图")
        return

    if args.save_dir:
        err_path = f"{args.save_dir}/error_dop.png"
        traj_path = f"{args.save_dir}/trajectory.png"
        saved_error = plot_error_and_dop(times, horiz, three_d, pdop, save_path=err_path, sat_counts=sat_counts)
        saved_traj = plot_trajectory(lat, lon, save_path=traj_path)
        if saved_error and saved_traj:
            print(f"图像已保存：{err_path}, {traj_path}")
        else:
            raise RuntimeError("图像生成失败")
    else:
        plot_error_and_dop(times, horiz, three_d, pdop, sat_counts=sat_counts)
        plot_trajectory(lat, lon)


if __name__ == "__main__":
    main()
