from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import List

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from models import PositionSolution
from pipeline import run_continuous_pipeline, write_csv
from plotting import plot_error_and_dop, plot_trajectory


def main() -> None:
    parser = argparse.ArgumentParser(description="Continuous GPS SPP processing")
    parser.add_argument("--obs", default="bjfs1170.26o", help="Path to RINEX obs file")
    parser.add_argument("--nav", default="brdc1170.26n", help="Path to RINEX nav file")
    parser.add_argument("--step", type=int, default=1, help="Process every N epochs")
    parser.add_argument("--max-epochs", type=int, default=0, help="Limit number of epochs (0 = all)")
    parser.add_argument("--plot", action="store_true", help="Plot error, DOP, and trajectory")
    parser.add_argument("--csv", default="results.csv", help="Output CSV path")
    parser.add_argument("--max-iter", type=int, default=8, help="Max least-squares iterations")
    parser.add_argument("--err-thresh", type=float, default=0.01, help="Convergence threshold (m)")
    parser.add_argument("--elev-mask", type=float, default=10.0, help="Elevation mask (deg)")
    parser.add_argument("--systems", default="G", help="GNSS systems, e.g. G or G,C,R")
    parser.add_argument("--save-plots", default="", help="Save plots to directory instead of show")
    args = parser.parse_args()

    systems = tuple([s.strip() for s in args.systems.split(",") if s.strip()])
    obs_header, solutions, errors, stats = run_continuous_pipeline(
        args.obs,
        args.nav,
        step=args.step,
        max_epochs=args.max_epochs,
        max_iter=args.max_iter,
        elev_mask_deg=args.elev_mask,
        systems=systems,
        error_thresh_m=args.err_thresh,
    )

    print(f"Solutions: {len(solutions)}")
    print(
        "Horizontal RMS/Mean/Max (m): "
        f"{stats['horiz_rms']:.3f} / {stats['horiz_mean']:.3f} / {stats['horiz_max']:.3f}"
    )
    print(
        "3D RMS/Mean/Max (m): "
        f"{stats['3d_rms']:.3f} / {stats['3d_mean']:.3f} / {stats['3d_max']:.3f}"
    )

    write_csv(args.csv, solutions, errors)
    print(f"CSV saved: {args.csv}")

    if args.plot:
        times = list(range(len(solutions)))
        horiz = [err["horiz"] for err in errors]
        three_d = [err["three_d"] for err in errors]
        pdop = [sol.pdop for sol in solutions]
        lat = [sol.position_blh[0] for sol in solutions]
        lon = [sol.position_blh[1] for sol in solutions]

        if args.save_plots:
            err_path = f"{args.save_plots}/error_dop.png"
            traj_path = f"{args.save_plots}/trajectory.png"
            plot_error_and_dop(times, horiz, three_d, pdop, save_path=err_path)
            plot_trajectory(lat, lon, save_path=traj_path)
            print(f"Plots saved: {err_path}, {traj_path}")
        else:
            plot_error_and_dop(times, horiz, three_d, pdop)
            plot_trajectory(lat, lon)


if __name__ == "__main__":
    main()
