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


def _configure_chinese_font(plt) -> None:
    try:
        import matplotlib.font_manager as fm
    except ImportError:
        return

    candidates = [
        "Arial Unicode MS",
        "PingFang SC",
        "Heiti SC",
        "Heiti TC",
        "Songti SC",
        "Noto Sans CJK SC",
        "Microsoft YaHei",
        "SimHei",
        "WenQuanYi Zen Hei",
    ]
    installed = {font.name for font in fm.fontManager.ttflist}
    for name in candidates:
        if name in installed:
            plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            return


DEFAULT_RESULTS = [
    "results/datasets/bjfs_2026_117_gps/results.csv",
    "results/datasets/daej_2026_117_gps/results.csv",
    "results/datasets/hksl_2026_117_gps/results.csv",
    "results/datasets/twtf_2026_117_gps_from_mixed/results.csv",
    "results/datasets/twtf_2026_117_bds/results.csv",
    "results/datasets/twtf_2026_117_gps_bds/results.csv",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="训练线性回归定位误差补偿模型")
    parser.add_argument("--results", nargs="*", default=DEFAULT_RESULTS, help="输入定位结果 CSV 文件")
    parser.add_argument("--output-dir", default="results/ml_compensation", help="输出目录")
    parser.add_argument("--train-ratio", type=float, default=0.7, help="训练集比例")
    args = parser.parse_args()

    paths = [Path(path) for path in args.results if Path(path).exists()]
    if len(paths) < 3:
        raise RuntimeError("附加题训练至少需要 3 个结果 CSV 文件")

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

    print(f"样本行数：{len(rows)}，训练集={len(train_rows)}，测试集={len(test_rows)}")
    print(
        "测试集三维 RMS 原始/补偿后 (m)："
        f"{test_metrics['original_3d_rms']:.3f} / {test_metrics['compensated_3d_rms']:.3f}"
    )
    print(f"输出文件已保存：{output_dir}")


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
        print("未安装 matplotlib，已跳过误差补偿图绘制")
        return
    _configure_chinese_font(plt)

    labels = ["训练水平", "训练三维", "测试水平", "测试三维"]
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
    ax.bar([value - width / 2 for value in x], original, width=width, label="原始误差")
    ax.bar([value + width / 2 for value in x], compensated, width=width, label="补偿后误差")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("RMS 误差 (m)")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
