"""Configuration utilities for SD card benchmarking."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass(frozen=True)
class SDCard:
    """Descriptor for an SD card under test."""

    name: str
    capacity_gb: int
    price_thb: float | None
    read_mb_s: float | None
    write_mb_s: float | None
    application_class: str | None
    u_class: str | None
    v_class: str | None
    endurance_notes: str | None
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class BenchmarkPlan:
    """Benchmark execution parameters."""

    file_size_mb: int = 2048
    block_size_kb: int = 1024
    random_samples: int = 2048
    random_block_kb: int = 4
    cleanup: bool = True


def load_cards(path: str | Path) -> List[SDCard]:
    """Load SD card definitions from a YAML file."""

    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    cards: List[SDCard] = []
    for entry in data.get("sd_cards", []):
        metadata = {k: v for k, v in entry.items() if k not in {
            "name",
            "capacity_gb",
            "price_thb",
            "read_mb_s",
            "write_mb_s",
            "application_class",
            "u_class",
            "v_class",
            "endurance_notes",
        }}

        cards.append(
            SDCard(
                name=entry["name"],
                capacity_gb=int(entry.get("capacity_gb", 0)),
                price_thb=_maybe_float(entry.get("price_thb")),
                read_mb_s=_maybe_float(entry.get("read_mb_s")),
                write_mb_s=_maybe_float(entry.get("write_mb_s")),
                application_class=entry.get("application_class"),
                u_class=entry.get("u_class"),
                v_class=entry.get("v_class"),
                endurance_notes=entry.get("endurance_notes"),
                metadata=metadata,
            )
        )

    return cards


def load_plan(path: str | Path | None) -> BenchmarkPlan:
    """Load the benchmark plan from YAML or use defaults."""

    if path is None:
        return BenchmarkPlan()

    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    return BenchmarkPlan(
        file_size_mb=int(data.get("file_size_mb", BenchmarkPlan.file_size_mb)),
        block_size_kb=int(data.get("block_size_kb", BenchmarkPlan.block_size_kb)),
        random_samples=int(data.get("random_samples", BenchmarkPlan.random_samples)),
        random_block_kb=int(data.get("random_block_kb", BenchmarkPlan.random_block_kb)),
        cleanup=bool(data.get("cleanup", BenchmarkPlan.cleanup)),
    )


def _maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

