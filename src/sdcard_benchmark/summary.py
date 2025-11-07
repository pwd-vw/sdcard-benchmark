"""Aggregate and visualise benchmark results."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt


@dataclass
class TestSnapshot:
    card_name: str
    test_type: str
    throughput_mb_s: float
    iops: float
    latency_ms: float


def load_results(paths: Iterable[str | Path]) -> List[TestSnapshot]:
    snapshots: List[TestSnapshot] = []
    for path in paths:
        path = Path(path)
        if not path.exists():
            continue
        if path.is_dir():
            for child in path.glob("*.json"):
                snapshots.extend(load_results([child]))
            continue

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        card_name = payload["card"]["name"]
        for result in payload["results"]:
            snapshots.append(
                TestSnapshot(
                    card_name=card_name,
                    test_type=result["test_type"],
                    throughput_mb_s=result["throughput_mb_s"],
                    iops=result["iops"],
                    latency_ms=result["latency_ms"],
                )
            )
    return snapshots


def summarise(
    snapshots: Iterable[TestSnapshot],
) -> Tuple[List[str], Dict[str, Dict[str, Dict[str, float]]]]:
    per_card: Dict[str, Dict[str, List[TestSnapshot]]] = {}
    for snap in snapshots:
        card_bucket = per_card.setdefault(snap.card_name, {})
        metric_bucket = card_bucket.setdefault(snap.test_type, [])
        metric_bucket.append(snap)

    tests = sorted({snap.test_type for snap in snapshots})
    summary: Dict[str, Dict[str, Dict[str, float]]] = {}
    for card, metrics in per_card.items():
        summary[card] = {}
        for test in tests:
            values = metrics.get(test, [])
            if not values:
                summary[card][test] = {"throughput": 0.0, "iops": 0.0, "latency": 0.0}
            else:
                summary[card][test] = {
                    "throughput": mean(s.throughput_mb_s for s in values),
                    "iops": mean(s.iops for s in values),
                    "latency": mean(s.latency_ms for s in values),
                }
    return tests, summary


def to_markdown(
    tests: List[str],
    summary: Dict[str, Dict[str, Dict[str, float]]],
    metric: str = "throughput",
    unit: str = "MB/s",
) -> str:
    headers = ["SD Card"] + [test.replace("_", " ").title() + f" ({unit})" for test in tests]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for card, metrics in sorted(summary.items(), key=lambda item: item[0].lower()):
        row = [card]
        for test in tests:
            row.append(f"{metrics.get(test, {}).get(metric, 0.0):.2f}")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def plot(summary: Dict[str, Dict[str, Dict[str, float]]], tests: List[str], destination: str | Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    cards = list(summary.keys())
    x = range(len(cards))
    width = 0.8 / max(1, len(tests))

    plt.figure(figsize=(12, 6))
    for idx, test in enumerate(tests):
        offsets = [position + idx * width for position in x]
        values = [summary[card].get(test, {}).get("throughput", 0.0) for card in cards]
        plt.bar(offsets, values, width=width, label=test.replace("_", " ").title())

    plt.ylabel("Throughput (MB/s)")
    plt.title("SD Card Benchmark Comparison")
    plt.xticks([position + width * (len(tests) - 1) / 2 for position in x], cards, rotation=45, ha="right")
    plt.tight_layout()
    plt.legend()

    plt.savefig(destination)
    plt.close()
    return destination

