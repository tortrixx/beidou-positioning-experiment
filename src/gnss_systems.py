"""GNSS 系统输入解析：当前实验支持 GPS(G)、BDS(C) 和 G,C 联合。"""

from __future__ import annotations

from typing import Iterable, Tuple


SUPPORTED_SYSTEMS = ("G", "C")
SUPPORTED_SYSTEMS_TEXT = "当前仅支持 GPS(G) 和 BDS(C)，请使用 G、C 或 G,C"


def parse_systems(text: str) -> Tuple[str, ...]:
    """把 GUI/命令行中的 'G,C' 文本解析成系统元组。"""
    return validate_systems(s.strip().upper() for s in text.split(",") if s.strip())


def validate_systems(systems: Iterable[str]) -> Tuple[str, ...]:
    """校验系统代码，避免后续定位流程收到不支持的系统。"""
    normalized = tuple(system.strip().upper() for system in systems if system.strip())
    if not normalized:
        raise ValueError("至少需要选择一个 GNSS 系统")
    unsupported = [system for system in normalized if system not in SUPPORTED_SYSTEMS]
    if unsupported:
        raise ValueError(f"{SUPPORTED_SYSTEMS_TEXT}；不支持的输入：{','.join(unsupported)}")
    return normalized
