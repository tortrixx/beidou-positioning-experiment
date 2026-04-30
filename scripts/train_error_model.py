from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from ml_compensation import (
    evaluate_compensation,
    load_result_rows,
    save_model,
    split_train_test,
    train_linear_model,
    write_predictions,
)


DEFAULT_RESULTS = [
    "results/datasets/bjfs_2026_117_gps/results.csv",
    "results/datasets/daej_2026_117_gps/results.csv",
    "results/datasets/hksl_2026_117_gps/results.csv",
    "results/datasets/twtf_2026_117_gps_from_mixed/results.csv",
    "results/datasets/twtf_2026_117_bds/results.csv",
    "results/datasets/twtf_2026_117_gps_bds/results.csv",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Train linear regression positioning error compensation model")
    parser.add_argument("--results", nargs="*", default=DEFAULT_RESULTS, help="Input positioning result CSV files")
    parser.add_argument("--output-dir", default="results/ml_compensation", help="Output directory")
    parser.add_argument("--train-ratio", type=float, default=0.7, help="Train split ratio")
    args = parser.parse_args()

    paths = [Path(path) for path in args.results if Path(path).exists()]
    if len(paths) < 3:
        raise RuntimeError("At least three result CSV files are required for the AI extension")

    rows = load_result_rows(paths)
    train_rows, test_rows = split_train_test(rows, train_ratio=args.train_ratio)
    model = train_linear_model(train_rows)
    train_metrics = evaluate_compensation(model, train_rows)
    test_metrics = evaluate_compensation(model, test_rows)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_model(output_dir / "linear_model.json", model)
    write_predictions(output_dir / "test_predictions.csv", model, test_rows)
    _write_metrics(output_dir / "metrics.csv", train_metrics, test_metrics)
    _plot_comparison(output_dir / "compensation_comparison.png", train_metrics, test_metrics)

    print(f"Rows: {len(rows)} train={len(train_rows)} test={len(test_rows)}")
    print(
        "Test 3D RMS original/compensated (m): "
        f"{test_metrics['original_3d_rms']:.3f} / {test_metrics['compensated_3d_rms']:.3f}"
    )
    print(f"Outputs saved: {output_dir}")


def _write_metrics(path: Path, train_metrics: dict[str, float], test_metrics: dict[str, float]) -> None:
    fields = ["split"] + list(train_metrics.keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerow({"split": "train", **train_metrics})
        writer.writerow({"split": "test", **test_metrics})


def _plot_comparison(path: Path, train_metrics: dict[str, float], test_metrics: dict[str, float]) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available; skip compensation plot")
        return

    labels = ["Train horiz", "Train 3D", "Test horiz", "Test 3D"]
    original = [
        train_metrics["original_horiz_rms"],
        train_metrics["original_3d_rms"],
        test_metrics["original_horiz_rms"],
        test_metrics["original_3d_rms"],
    ]
    compensated = [
        train_metrics["compensated_horiz_rms"],
        train_metrics["compensated_3d_rms"],
        test_metrics["compensated_horiz_rms"],
        test_metrics["compensated_3d_rms"],
    ]

    x = list(range(len(labels)))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar([value - width / 2 for value in x], original, width=width, label="Original")
    ax.bar([value + width / 2 for value in x], compensated, width=width, label="Compensated")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("RMS error (m)")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
