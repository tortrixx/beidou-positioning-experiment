from __future__ import annotations

import gzip
from pathlib import Path


def read_rinex_text(path: str | Path, *, kind: str) -> list[str]:
    rinex_path = Path(path)
    lower = rinex_path.name.lower()
    if kind == "obs" and (
        lower.endswith(".crx")
        or lower.endswith(".crx.gz")
        or lower.endswith(".d")
        or ".d.gz" in lower
    ):
        raise ValueError(
            "检测到 Hatanaka 压缩观测文件。请先将 .crx/.d 转换为普通 RINEX "
            ".rnx/.obs/.o 后再处理。"
        )

    if lower.endswith(".gz"):
        with gzip.open(rinex_path, "rt", encoding="utf-8", errors="ignore") as f:
            return f.read().splitlines()
    return rinex_path.read_text(encoding="utf-8", errors="ignore").splitlines()
