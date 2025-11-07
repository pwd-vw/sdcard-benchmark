"""Aggregate benchmark results and generate visual reports."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from sdcard_benchmark.summary import load_results, plot, summarise, to_markdown


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SD card benchmark summary")
    parser.add_argument("results", help="Directory or JSON files containing benchmark results", nargs="+")
    parser.add_argument("--output-dir", default="reports", help="Directory to store generated reports")
    parser.add_argument("--markdown-name", default="summary.md", help="Markdown filename")
    parser.add_argument("--chart-name", default="comparison.png", help="Chart filename")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    snapshots = load_results(args.results)
    if not snapshots:
        raise SystemExit("No benchmark results found. Provide path(s) to JSON result files.")

    tests, summary = summarise(snapshots)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sections = [
        "# SD Card Benchmark Summary",
        "\n## Throughput (MB/s)",
        to_markdown(tests, summary, metric="throughput", unit="MB/s"),
        "\n## IOPS",
        to_markdown(tests, summary, metric="iops", unit="IOPS"),
        "\n## Latency (ms)",
        to_markdown(tests, summary, metric="latency", unit="ms"),
    ]
    markdown_content = "\n".join(sections)
    md_path = output_dir / args.markdown_name
    md_path.write_text(markdown_content, encoding="utf-8")

    chart_path = output_dir / args.chart_name
    plot(summary, tests, chart_path)

    print(f"Markdown summary saved to {md_path}")
    print(f"Comparison chart saved to {chart_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

