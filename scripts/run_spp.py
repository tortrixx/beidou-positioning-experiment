from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from positioning import single_point_position
from rinex_nav import parse_rinex_nav
from rinex_obs import parse_rinex_obs


def main() -> None:
    parser = argparse.ArgumentParser(description="Single-epoch GPS SPP solver")
    parser.add_argument("--obs", default="bjfs1170.26o", help="Path to RINEX obs file")
    parser.add_argument("--nav", default="brdc1170.26n", help="Path to RINEX nav file")
    parser.add_argument("--epoch", type=int, default=0, help="Epoch index (0-based)")
    parser.add_argument("--max-iter", type=int, default=8, help="Max least-squares iterations")
    parser.add_argument("--err-thresh", type=float, default=0.01, help="Convergence threshold (m)")
    parser.add_argument("--elev-mask", type=float, default=10.0, help="Elevation mask (deg)")
    parser.add_argument("--systems", default="G", help="GNSS systems, e.g. G or G,C,R")
    args = parser.parse_args()

    obs_header, epochs = parse_rinex_obs(args.obs)
    nav_header, nav_records = parse_rinex_nav(args.nav)

    if obs_header.approx_position_xyz is None:
        raise ValueError("Missing approximate receiver position in obs header")
    if args.epoch >= len(epochs):
        raise ValueError("Epoch index out of range")

    systems = tuple([s.strip() for s in args.systems.split(",") if s.strip()])
    solution = single_point_position(
        epochs[args.epoch],
        nav_header,
        nav_records,
        obs_header.approx_position_xyz,
        max_iter=args.max_iter,
        elev_mask_deg=args.elev_mask,
        systems=systems,
        error_thresh_m=args.err_thresh,
        time_system=obs_header.time_system,
    )

    print(f"Epoch: {solution.time}")
    print(f"ECEF: {solution.position_ecef[0]:.3f}, {solution.position_ecef[1]:.3f}, {solution.position_ecef[2]:.3f}")
    print(f"BLH: {solution.position_blh[0]:.8f}, {solution.position_blh[1]:.8f}, {solution.position_blh[2]:.3f}")
    print(f"Clock bias (m): {solution.clock_bias_m:.3f}")
    print(f"Used satellites: {len(solution.used_sats)}")
    print(f"PDOP: {solution.pdop:.3f}  GDOP: {solution.gdop:.3f}")


if __name__ == "__main__":
    main()
