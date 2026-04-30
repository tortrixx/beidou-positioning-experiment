from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from experiment_modules import SoftwareSystemModule
from plotting import plot_error_and_dop, plot_trajectory


def main() -> None:
    parser = argparse.ArgumentParser(description="Continuous GPS SPP processing")
    parser.add_argument("--obs", default="data/sample/bjfs1170.26o", help="Path to RINEX obs file")
    parser.add_argument("--nav", default="data/sample/brdc1170.26n", help="Path to RINEX nav file")
    parser.add_argument("--step", type=int, default=1, help="Process every N epochs")
    parser.add_argument("--max-epochs", type=int, default=0, help="Limit number of epochs (0 = all)")
    parser.add_argument("--plot", action="store_true", help="Plot error, DOP, and trajectory")
    parser.add_argument("--csv", default="results.csv", help="Output CSV path")
    parser.add_argument("--max-iter", type=int, default=8, help="Max least-squares iterations")
    parser.add_argument("--err-thresh", type=float, default=0.01, help="Convergence threshold (m)")
    parser.add_argument("--elev-mask", type=float, default=10.0, help="Elevation mask (deg)")
    parser.add_argument("--residual-gate", type=float, default=None, help="Post-fit residual gate in meters")
    parser.add_argument("--systems", default="G", help="GNSS systems, e.g. G or G,C,R")
    parser.add_argument("--save-plots", default="", help="Save plots to directory instead of show")
    args = parser.parse_args()

    systems = tuple([s.strip() for s in args.systems.split(",") if s.strip()])
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

    print(f"Solutions: {len(solutions)}")
    print(
        "Horizontal RMS/Mean/Max (m): "
        f"{stats['horiz_rms']:.3f} / {stats['horiz_mean']:.3f} / {stats['horiz_max']:.3f}"
    )
    print(
        "3D RMS/Mean/Max (m): "
        f"{stats['3d_rms']:.3f} / {stats['3d_mean']:.3f} / {stats['3d_max']:.3f}"
    )

    print(f"CSV saved: {args.csv}")
    if not solutions:
        print(
            "No valid solutions; skipped plotting. "
            f"Processed epochs: {stats.get('processed_epochs', 0)}, "
            f"skipped epochs: {stats.get('skipped_epochs', 0)}"
        )
        skip_reasons = stats.get("skip_reasons", {})
        if skip_reasons:
            for reason, count in skip_reasons.items():
                print(f"Skip reason: {reason} ({count})")
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
                print(f"Plots saved: {err_path}, {traj_path}")
            else:
                raise RuntimeError("Plot generation failed")
        else:
            plot_error_and_dop(times, horiz, three_d, pdop, sat_counts=sat_counts)
            plot_trajectory(lat, lon)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
