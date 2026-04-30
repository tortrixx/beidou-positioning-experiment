from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from experiment_modules import SoftwareSystemModule
from gnss_systems import parse_systems
from plotting import plot_error_and_dop, plot_trajectory


def main() -> None:
    parser = argparse.ArgumentParser(description="连续历元 GNSS 单点定位处理")
    parser.add_argument("--obs", default="data/sample/bjfs1170.26o", help="RINEX 观测文件路径")
    parser.add_argument("--nav", default="data/sample/brdc1170.26n", help="RINEX 导航文件路径")
    parser.add_argument("--step", type=int, default=1, help="每隔 N 个历元处理一次")
    parser.add_argument("--max-epochs", type=int, default=0, help="最多处理历元数，0 表示全部")
    parser.add_argument("--plot", action="store_true", help="绘制误差、DOP 和轨迹图")
    parser.add_argument("--csv", default="results.csv", help="输出 CSV 路径")
    parser.add_argument("--max-iter", type=int, default=8, help="最小二乘最大迭代次数")
    parser.add_argument("--err-thresh", type=float, default=0.01, help="收敛阈值，单位 m")
    parser.add_argument("--elev-mask", type=float, default=10.0, help="高度角截止角，单位 deg")
    parser.add_argument("--residual-gate", type=float, default=None, help="验后残差剔除阈值，单位 m")
    parser.add_argument("--systems", default="G", help="GNSS 系统：G、C 或 G,C")
    parser.add_argument("--save-plots", default="", help="将图像保存到指定目录，不弹窗显示")
    args = parser.parse_args()

    systems = parse_systems(args.systems)
    result = SoftwareSystemModule().run(
        args.obs,
        args.nav,
        step=args.step,
        max_epochs=args.max_epochs,
        max_iter=args.max_iter,
        elev_mask_deg=args.elev_mask,
        systems=systems,
        error_thresh_m=args.err_thresh,
        residual_gate_m=args.residual_gate,
        output_csv=args.csv,
    )
    solutions = result.solutions
    errors = result.errors
    stats = result.stats

    print(f"有效解数量：{len(solutions)}")
    print(
        "水平误差 RMS/均值/最大值 (m)："
        f"{stats['horiz_rms']:.3f} / {stats['horiz_mean']:.3f} / {stats['horiz_max']:.3f}"
    )
    print(
        "三维误差 RMS/均值/最大值 (m)："
        f"{stats['3d_rms']:.3f} / {stats['3d_mean']:.3f} / {stats['3d_max']:.3f}"
    )

    print(f"CSV 已保存：{args.csv}")
    if not solutions:
        print(
            "没有有效定位解，已跳过绘图。"
            f"处理历元数：{stats.get('processed_epochs', 0)}，"
            f"跳过历元数：{stats.get('skipped_epochs', 0)}"
        )
        skip_reasons = stats.get("skip_reasons", {})
        if skip_reasons:
            for reason, count in skip_reasons.items():
                print(f"跳过原因：{reason}（{count}）")
        return

    if args.plot:
        times = list(range(len(solutions)))
        horiz = [err["horiz"] for err in errors]
        three_d = [err["three_d"] for err in errors]
        pdop = [sol.pdop for sol in solutions]
        sat_counts = [len(sol.used_sats) for sol in solutions]
        lat = [sol.position_blh[0] for sol in solutions]
        lon = [sol.position_blh[1] for sol in solutions]

        if args.save_plots:
            err_path = f"{args.save_plots}/error_dop.png"
            traj_path = f"{args.save_plots}/trajectory.png"
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
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
