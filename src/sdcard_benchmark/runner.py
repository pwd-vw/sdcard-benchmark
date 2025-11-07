"""Benchmark runner implementation."""

from __future__ import annotations

import json
import os
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from .config import BenchmarkPlan, SDCard
from .metrics import iops, latency_ms, throughput_mb_s


@dataclass
class TestOutcome:
    test_type: str
    seconds: float
    total_bytes: int
    operations: int
    throughput_mb_s: float
    iops: float
    latency_ms: float


@dataclass
class BenchmarkOutcome:
    card: SDCard
    plan: BenchmarkPlan
    hostname: str
    start_timestamp: float
    end_timestamp: float
    results: List[TestOutcome]

    def to_dict(self) -> Dict[str, object]:
        payload = {
            "card": asdict(self.card),
            "plan": asdict(self.plan),
            "hostname": self.hostname,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "results": [asdict(result) for result in self.results],
        }
        return payload


class BenchmarkRunner:
    """Execute benchmark plan against a target SD card path."""

    def __init__(
        self,
        card: SDCard,
        target_path: str | Path,
        plan: BenchmarkPlan | None = None,
        work_dir: str | Path | None = None,
        seed: int | None = None,
    ) -> None:
        self.card = card
        self.target_path = Path(target_path)
        self.plan = plan or BenchmarkPlan()
        self.work_dir = Path(work_dir) if work_dir else Path.cwd() / "results"
        self.seed = seed or int(time.time())

        self._random = random.Random(self.seed)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        if not self.target_path.exists():
            raise FileNotFoundError(f"Target path {self.target_path} not found")
        if not self.target_path.is_dir():
            raise NotADirectoryError(f"Target path {self.target_path} is not a directory")

    def run(self) -> BenchmarkOutcome:
        start_ts = time.time()
        results = list(self._execute_suite())
        end_ts = time.time()

        outcome = BenchmarkOutcome(
            card=self.card,
            plan=self.plan,
            hostname=os.environ.get("COMPUTERNAME", "unknown"),
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            results=results,
        )

        return outcome

    def save(self, outcome: BenchmarkOutcome, destination: str | Path | None = None) -> Path:
        destination = Path(destination) if destination else self.work_dir
        destination.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in self.card.name.lower())
        ts = int(outcome.end_timestamp)
        file_path = destination / f"{safe_name}-{ts}.json"
        with file_path.open("w", encoding="utf-8") as handle:
            json.dump(outcome.to_dict(), handle, indent=2)
        return file_path

    def _execute_suite(self) -> Iterable[TestOutcome]:
        plan = self.plan
        test_file = self.target_path / "benchmark-test.bin"
        block_bytes = plan.block_size_kb * 1024
        random_block_bytes = plan.random_block_kb * 1024
        total_bytes = plan.file_size_mb * 1024 * 1024

        if total_bytes <= 0:
            raise ValueError("file_size_mb must be greater than zero")

        # Sequential write
        write_result = self._measure_write(test_file, total_bytes, block_bytes)
        yield write_result

        # Sequential read
        read_result = self._measure_read(test_file, block_bytes)
        yield read_result

        # Random read
        random_read_result = self._measure_random(test_file, random_block_bytes, plan.random_samples, write=False)
        yield random_read_result

        # Random write (in-place)
        random_write_result = self._measure_random(test_file, random_block_bytes, plan.random_samples, write=True)
        yield random_write_result

        if plan.cleanup and test_file.exists():
            test_file.unlink()

    def _measure_write(self, path: Path, total_bytes: int, block_bytes: int) -> TestOutcome:
        blocks = total_bytes // block_bytes
        remainder = total_bytes % block_bytes
        operations = blocks + (1 if remainder else 0)

        start = time.perf_counter()
        with path.open("wb", buffering=0) as handle:
            chunk = bytes(block_bytes)
            for _ in range(blocks):
                handle.write(chunk)
            if remainder:
                handle.write(bytes(remainder))
            handle.flush()
            os.fsync(handle.fileno())
        end = time.perf_counter()

        seconds = end - start
        total = total_bytes
        return TestOutcome(
            test_type="sequential_write",
            seconds=seconds,
            total_bytes=total,
            operations=operations,
            throughput_mb_s=throughput_mb_s(total, seconds),
            iops=iops(operations, seconds),
            latency_ms=latency_ms(seconds, operations),
        )

    def _measure_read(self, path: Path, block_bytes: int) -> TestOutcome:
        total = 0
        operations = 0
        start = time.perf_counter()
        with path.open("rb", buffering=0) as handle:
            while True:
                chunk = handle.read(block_bytes)
                if not chunk:
                    break
                total += len(chunk)
                operations += 1
        end = time.perf_counter()

        seconds = end - start
        return TestOutcome(
            test_type="sequential_read",
            seconds=seconds,
            total_bytes=total,
            operations=operations,
            throughput_mb_s=throughput_mb_s(total, seconds),
            iops=iops(operations, seconds),
            latency_ms=latency_ms(seconds, operations),
        )

    def _measure_random(self, path: Path, block_bytes: int, samples: int, write: bool) -> TestOutcome:
        if block_bytes <= 0:
            raise ValueError("block_bytes must be > 0")
        if samples <= 0:
            raise ValueError("samples must be > 0")

        total_bytes = 0
        start = time.perf_counter()
        mode = "r+b" if write else "rb"
        with path.open(mode, buffering=0) as handle:
            file_size = handle.seek(0, os.SEEK_END)
            for _ in range(samples):
                if file_size <= block_bytes:
                    offset = 0
                else:
                    offset = self._random.randrange(0, file_size - block_bytes)
                handle.seek(offset)
                if write:
                    handle.write(bytes(block_bytes))
                else:
                    handle.read(block_bytes)
                total_bytes += block_bytes
            handle.flush()
            if write:
                os.fsync(handle.fileno())
        end = time.perf_counter()

        seconds = end - start
        return TestOutcome(
            test_type="random_write" if write else "random_read",
            seconds=seconds,
            total_bytes=total_bytes,
            operations=samples,
            throughput_mb_s=throughput_mb_s(total_bytes, seconds),
            iops=iops(samples, seconds),
            latency_ms=latency_ms(seconds, samples),
        )

