"""Command-line entry point to execute SD card benchmarks."""

from __future__ import annotations

import argparse
import sys

from sdcard_benchmark.config import BenchmarkPlan, SDCard, load_cards, load_plan
from sdcard_benchmark.runner import BenchmarkRunner


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SD card benchmark suite")
    parser.add_argument("card_name", help="Name of the SD card as defined in the config file")
    parser.add_argument("target_path", help="Mounted path on the SD card to run tests")
    parser.add_argument("--cards-config", default="data/sd_cards.yaml", help="Path to SD card definitions YAML")
    parser.add_argument("--plan", default=None, help="Optional benchmark plan YAML")
    parser.add_argument("--results-dir", default="results", help="Directory to store JSON result files")
    parser.add_argument("--work-dir", default=None, help="Working directory for intermediate files")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    return parser.parse_args(argv)


def find_card(cards: list[SDCard], name: str) -> SDCard:
    candidates = [card for card in cards if card.name.lower() == name.lower()]
    if not candidates:
        available = ", ".join(card.name for card in cards)
        raise SystemExit(f"Card '{name}' not found. Available: {available}")
    return candidates[0]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    cards = load_cards(args.cards_config)
    card = find_card(cards, args.card_name)
    plan = load_plan(args.plan)

    runner = BenchmarkRunner(
        card=card,
        target_path=args.target_path,
        plan=plan,
        work_dir=args.work_dir or args.results_dir,
        seed=args.seed,
    )

    outcome = runner.run()
    saved_path = runner.save(outcome, destination=args.results_dir)
    print(f"Benchmark complete. Results saved to {saved_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

