from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from experiment_modules import RinexDataModule, SinglePointPositioningModule
from gnss_systems import parse_systems


def main() -> None:
    parser = argparse.ArgumentParser(description="单历元 GNSS 单点定位解算")
    parser.add_argument("--obs", default="data/sample/bjfs1170.26o", help="RINEX 观测文件路径")
    parser.add_argument("--nav", default="data/sample/brdc1170.26n", help="RINEX 导航文件路径")
    parser.add_argument("--epoch", type=int, default=0, help="历元索引，从 0 开始")
    parser.add_argument("--max-iter", type=int, default=8, help="最小二乘最大迭代次数")
    parser.add_argument("--err-thresh", type=float, default=0.01, help="收敛阈值，单位 m")
    parser.add_argument("--elev-mask", type=float, default=10.0, help="高度角截止角，单位 deg")
    parser.add_argument("--residual-gate", type=float, default=None, help="验后残差剔除阈值，单位 m")
    parser.add_argument("--systems", default="G", help="GNSS 系统：G、C 或 G,C")
    args = parser.parse_args()

    dataset = RinexDataModule().load(args.obs, args.nav)
    obs_header = dataset.obs_header
    epochs = dataset.epochs

    if args.epoch < 0:
        raise ValueError("历元索引必须 >= 0")
    if args.epoch >= len(epochs):
        raise ValueError("历元索引超出范围")

    systems = parse_systems(args.systems)
    solver = SinglePointPositioningModule(dataset.nav_header, dataset.nav_records)
    solution = solver.solve_epoch(
        epochs[args.epoch],
        obs_header.approx_position_xyz,
        max_iter=args.max_iter,
        elev_mask_deg=args.elev_mask,
        systems=systems,
        error_thresh_m=args.err_thresh,
        residual_gate_m=args.residual_gate,
        time_system=obs_header.time_system,
    )

    print(f"历元时间：{solution.time}")
    print(f"ECEF: {solution.position_ecef[0]:.3f}, {solution.position_ecef[1]:.3f}, {solution.position_ecef[2]:.3f}")
    print(f"BLH 经纬高：{solution.position_blh[0]:.8f}, {solution.position_blh[1]:.8f}, {solution.position_blh[2]:.3f}")
    print(f"接收机钟差 (m)：{solution.clock_bias_m:.3f}")
    print(f"参与解算卫星数：{len(solution.used_sats)}")
    print(f"PDOP: {solution.pdop:.3f}  GDOP: {solution.gdop:.3f}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
