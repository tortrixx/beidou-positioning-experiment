from __future__ import annotations

from typing import Iterable, Tuple


SUPPORTED_SYSTEMS = ("G", "C")
SUPPORTED_SYSTEMS_TEXT = "当前仅支持 GPS(G) 和 BDS(C)，请使用 G、C 或 G,C"


def parse_systems(text: str) -> Tuple[str, ...]:
    return validate_systems(s.strip().upper() for s in text.split(",") if s.strip())


def validate_systems(systems: Iterable[str]) -> Tuple[str, ...]:
    normalized = tuple(system.strip().upper() for system in systems if system.strip())
    if not normalized:
        raise ValueError("至少需要选择一个 GNSS 系统")
    unsupported = [system for system in normalized if system not in SUPPORTED_SYSTEMS]
    if unsupported:
        raise ValueError(f"{SUPPORTED_SYSTEMS_TEXT}；不支持的输入：{','.join(unsupported)}")
    return normalized
