"""Performance metric helpers for SD card benchmarking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


MEBI = 1024 * 1024


@dataclass
class Metric:
    """Numeric metric with basic derived values."""

    name: str
    raw_value: float
    unit: str
    description: str
    higher_is_better: bool = True
    extra: Dict[str, float] = field(default_factory=dict)

    @property
    def value(self) -> float:
        return self.raw_value


def throughput_mb_s(total_bytes: int, seconds: float) -> float:
    if seconds <= 0:
        return 0.0
    return (total_bytes / MEBI) / seconds


def latency_ms(seconds: float, operations: int) -> float:
    if operations <= 0:
        return 0.0
    return (seconds / operations) * 1000


def iops(operations: int, seconds: float) -> float:
    if seconds <= 0:
        return 0.0
    return operations / seconds

