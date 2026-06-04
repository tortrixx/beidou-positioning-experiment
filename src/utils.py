"""RINEX 固定宽度字段的基础转换函数。"""

from __future__ import annotations

from typing import Optional


def rinex_float(text: str) -> Optional[float]:
    """把 RINEX 中可能使用 D 指数的浮点字段转为 float。"""
    value = text.strip()
    if not value:
        return None
    return float(value.replace("D", "E"))


def rinex_int(text: str) -> Optional[int]:
    """把空白可选整数字段安全转为 int 或 None。"""
    value = text.strip()
    if not value:
        return None
    return int(value)
