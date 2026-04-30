from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


FEATURE_NAMES = [
    "used_sats",
    "pdop",
    "gdop",
    "residual_rms_m",
    "residual_max_m",
    "clock_bias_m",
    "h",
]
TARGET_NAMES = ["east", "north", "up"]


@dataclass
class LinearCompensationModel:
    feature_names: List[str]
    means: List[float]
    scales: List[float]
    coefficients: Dict[str, List[float]]

    def predict(self, row: Dict[str, str | float]) -> Dict[str, float]:
        features = _scaled_features(row, self.feature_names, self.means, self.scales)
        values = [1.0] + features
        return {
            target: sum(coef * value for coef, value in zip(coefficients, values))
            for target, coefficients in self.coefficients.items()
        }

    def to_json(self) -> str:
        return json.dumps(
            {
                "feature_names": self.feature_names,
                "means": self.means,
                "scales": self.scales,
                "coefficients": self.coefficients,
            },
            indent=2,
            ensure_ascii=False,
        )


def load_result_rows(paths: Sequence[str | Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path_like in paths:
        path = Path(path_like)
        dataset = path.parent.name
        with path.open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row = dict(row)
                row["dataset"] = dataset
                rows.append(row)
    return rows


def split_train_test(rows: Sequence[Dict[str, str]], train_ratio: float = 0.7) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    if not 0.0 < train_ratio < 1.0:
        raise ValueError("train_ratio 训练集比例必须在 0 和 1 之间")
    ordered = sorted(enumerate(rows), key=lambda item: ((item[0] * 1103515245 + 12345) % 2**31))
    split = max(1, min(len(ordered) - 1, int(len(ordered) * train_ratio)))
    train = [row for _, row in ordered[:split]]
    test = [row for _, row in ordered[split:]]
    return train, test


def train_linear_model(rows: Sequence[Dict[str, str]], ridge: float = 1.0e-6) -> LinearCompensationModel:
    if len(rows) < 2:
        raise ValueError("训练至少需要两行样本")

    means, scales = _feature_stats(rows, FEATURE_NAMES)
    x_rows = [[1.0] + _scaled_features(row, FEATURE_NAMES, means, scales) for row in rows]
    coefficients: Dict[str, List[float]] = {}
    for target in TARGET_NAMES:
        y = [_float(row, target) for row in rows]
        coefficients[target] = _fit_ridge(x_rows, y, ridge=ridge)
    return LinearCompensationModel(
        feature_names=list(FEATURE_NAMES),
        means=means,
        scales=scales,
        coefficients=coefficients,
    )


def evaluate_compensation(
    model: LinearCompensationModel,
    rows: Sequence[Dict[str, str]],
) -> Dict[str, float]:
    original_horiz: List[float] = []
    original_3d: List[float] = []
    compensated_horiz: List[float] = []
    compensated_3d: List[float] = []

    for row in rows:
        east = _float(row, "east")
        north = _float(row, "north")
        up = _float(row, "up")
        pred = model.predict(row)
        comp_east = east - pred["east"]
        comp_north = north - pred["north"]
        comp_up = up - pred["up"]
        original_horiz.append(math.hypot(east, north))
        original_3d.append(math.sqrt(east * east + north * north + up * up))
        compensated_horiz.append(math.hypot(comp_east, comp_north))
        compensated_3d.append(math.sqrt(comp_east * comp_east + comp_north * comp_north + comp_up * comp_up))

    return {
        "samples": len(rows),
        "original_horiz_rms": _rms(original_horiz),
        "compensated_horiz_rms": _rms(compensated_horiz),
        "original_3d_rms": _rms(original_3d),
        "compensated_3d_rms": _rms(compensated_3d),
        "horiz_improvement_pct": _improvement(_rms(original_horiz), _rms(compensated_horiz)),
        "3d_improvement_pct": _improvement(_rms(original_3d), _rms(compensated_3d)),
    }


def write_predictions(
    path: str | Path,
    model: LinearCompensationModel,
    rows: Sequence[Dict[str, str]],
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "dataset",
        "time",
        "east",
        "north",
        "up",
        "pred_east",
        "pred_north",
        "pred_up",
        "comp_east",
        "comp_north",
        "comp_up",
        "original_horiz",
        "compensated_horiz",
        "original_3d",
        "compensated_3d",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            east = _float(row, "east")
            north = _float(row, "north")
            up = _float(row, "up")
            pred = model.predict(row)
            comp_east = east - pred["east"]
            comp_north = north - pred["north"]
            comp_up = up - pred["up"]
            writer.writerow(
                {
                    "dataset": row.get("dataset", ""),
                    "time": row.get("time", ""),
                    "east": f"{east:.6f}",
                    "north": f"{north:.6f}",
                    "up": f"{up:.6f}",
                    "pred_east": f"{pred['east']:.6f}",
                    "pred_north": f"{pred['north']:.6f}",
                    "pred_up": f"{pred['up']:.6f}",
                    "comp_east": f"{comp_east:.6f}",
                    "comp_north": f"{comp_north:.6f}",
                    "comp_up": f"{comp_up:.6f}",
                    "original_horiz": f"{math.hypot(east, north):.6f}",
                    "compensated_horiz": f"{math.hypot(comp_east, comp_north):.6f}",
                    "original_3d": f"{math.sqrt(east * east + north * north + up * up):.6f}",
                    "compensated_3d": f"{math.sqrt(comp_east * comp_east + comp_north * comp_north + comp_up * comp_up):.6f}",
                }
            )


def save_model(path: str | Path, model: LinearCompensationModel) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(model.to_json(), encoding="utf-8")


def _feature_stats(rows: Sequence[Dict[str, str]], feature_names: Sequence[str]) -> Tuple[List[float], List[float]]:
    means: List[float] = []
    scales: List[float] = []
    for feature in feature_names:
        values = [_float(row, feature) for row in rows]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        scale = math.sqrt(variance) or 1.0
        means.append(mean)
        scales.append(scale)
    return means, scales


def _scaled_features(
    row: Dict[str, str | float],
    feature_names: Sequence[str],
    means: Sequence[float],
    scales: Sequence[float],
) -> List[float]:
    return [(_float(row, feature) - mean) / scale for feature, mean, scale in zip(feature_names, means, scales)]


def _fit_ridge(x_rows: Sequence[Sequence[float]], y: Sequence[float], ridge: float) -> List[float]:
    size = len(x_rows[0])
    normal = [[0.0 for _ in range(size)] for _ in range(size)]
    rhs = [0.0 for _ in range(size)]
    for row, target in zip(x_rows, y):
        for i in range(size):
            rhs[i] += row[i] * target
            for j in range(size):
                normal[i][j] += row[i] * row[j]
    for i in range(1, size):
        normal[i][i] += ridge
    return _solve_linear(normal, rhs)


def _solve_linear(a: List[List[float]], b: List[float]) -> List[float]:
    size = len(a)
    matrix = [row[:] + [b[idx]] for idx, row in enumerate(a)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda row: abs(matrix[row][col]))
        if abs(matrix[pivot][col]) < 1.0e-12:
            raise ValueError("回归矩阵奇异，无法训练模型")
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        scale = matrix[col][col]
        for j in range(col, size + 1):
            matrix[col][j] /= scale
        for row in range(size):
            if row == col:
                continue
            factor = matrix[row][col]
            for j in range(col, size + 1):
                matrix[row][j] -= factor * matrix[col][j]
    return [matrix[row][size] for row in range(size)]


def _float(row: Dict[str, str | float], name: str) -> float:
    value = row.get(name, 0.0)
    if value in (None, ""):
        return 0.0
    return float(value)


def _rms(values: Iterable[float]) -> float:
    vals = list(values)
    if not vals:
        return float("nan")
    return math.sqrt(sum(value * value for value in vals) / len(vals))


def _improvement(original: float, compensated: float) -> float:
    if original == 0.0 or math.isnan(original):
        return 0.0
    return (original - compensated) / original * 100.0
