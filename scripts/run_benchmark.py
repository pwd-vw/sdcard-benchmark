"""Command-line entry point to execute SD card benchmarks."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
import string

from sdcard_benchmark.config import BenchmarkPlan, SDCard, load_cards, load_plan
from sdcard_benchmark.runner import BenchmarkRunner


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SD card benchmark suite")
    parser.add_argument(
        "card_name",
        nargs="?",
        default=None,
        help="Name of the SD card as defined in the config file. If omitted, you'll be prompted to choose.",
    )
    parser.add_argument(
        "target_path",
        nargs="?",
        default=None,
        help="Mounted path on the SD card to run tests. If omitted, you'll be prompted to choose.",
    )
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


def prompt_card_selection(cards: list[SDCard]) -> SDCard:
    if not cards:
        print("No SD cards found in configuration. Switching to custom card entry.")
        return prompt_custom_card()

    print("Select an SD card to benchmark:")
    for index, card in enumerate(cards, start=1):
        descriptor = f"{card.capacity_gb} GB" if card.capacity_gb else "Unknown capacity"
        print(f" [{index}] {card.name} ({descriptor})")
    custom_index = len(cards) + 1
    print(f" [{custom_index}] Enter a custom SD card")

    while True:
        choice = input(f"Enter choice (1-{custom_index}): ").strip()
        if not choice.isdigit():
            print("Please enter a number.")
            continue
        value = int(choice)
        if 1 <= value <= len(cards):
            return cards[value - 1]
        if value == custom_index:
            return prompt_custom_card()
        print(f"Choice must be between 1 and {custom_index}.")


def prompt_custom_card() -> SDCard:
    print("Enter details for the SD card you would like to benchmark.")

    name = _prompt_required("Card name")
    capacity_gb = _prompt_int("Capacity (GB)", default=0)
    price_thb = _prompt_optional_float("Price (THB)")
    read_mb_s = _prompt_optional_float("Advertised read speed (MB/s)")
    write_mb_s = _prompt_optional_float("Advertised write speed (MB/s)")
    application_class = _prompt_optional_str("Application class (e.g. A1)")
    u_class = _prompt_optional_str("UHS speed class (e.g. U3)")
    v_class = _prompt_optional_str("Video speed class (e.g. V30)")
    endurance_notes = _prompt_optional_str("Endurance notes")

    return SDCard(
        name=name,
        capacity_gb=capacity_gb,
        price_thb=price_thb,
        read_mb_s=read_mb_s,
        write_mb_s=write_mb_s,
        application_class=application_class,
        u_class=u_class,
        v_class=v_class,
        endurance_notes=endurance_notes,
        metadata={},
    )


def _prompt_required(prompt: str) -> str:
    while True:
        value = input(f"{prompt}: ").strip()
        if value:
            return value
        print("This field is required.")


def _prompt_int(prompt: str, default: int = 0) -> int:
    while True:
        value = input(f"{prompt} [{default}]: ").strip()
        if not value:
            return default
        try:
            return int(value)
        except ValueError:
            print("Please enter a whole number.")


def _prompt_optional_float(prompt: str) -> float | None:
    while True:
        value = input(f"{prompt} (leave blank to skip): ").strip()
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            print("Please enter a numeric value.")


def _prompt_optional_str(prompt: str) -> str | None:
    value = input(f"{prompt} (leave blank to skip): ").strip()
    return value or None


def make_progress_printer() -> Callable[[str], None]:
    def progress(message: str) -> None:
        print(f"[sdcard-benchmark] {message}")

    return progress


def discover_mount_points() -> list[Path]:
    candidates: list[Path] = []

    if sys.platform.startswith("win"):
        for letter in string.ascii_uppercase:
            root = Path(f"{letter}:/")
            if root.exists() and root.is_dir():
                candidates.append(root)
    else:
        for base in (Path("/Volumes"), Path("/media"), Path("/mnt")):
            if base.exists() and base.is_dir():
                for child in base.iterdir():
                    if child.is_dir():
                        candidates.append(child)

    seen = set()
    unique: list[Path] = []
    for path in candidates:
        normalized = path.resolve()
        if normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return unique


def prompt_target_path(candidates: list[Path]) -> Path:
    if candidates:
        print("Select target path for the SD card:")
        for index, path in enumerate(candidates, start=1):
            print(f" [{index}] {path}")
        manual_index = len(candidates) + 1
        print(f" [{manual_index}] Enter a path manually")
    else:
        print("Could not automatically detect mounted paths. Please enter the target directory manually.")
        manual_index = 1

    while True:
        if candidates:
            choice = input(f"Enter choice (1-{manual_index}): ").strip()
            if not choice.isdigit():
                print("Please enter a number.")
                continue
            value = int(choice)
            if 1 <= value <= len(candidates):
                selected = candidates[value - 1]
                if selected.exists() and selected.is_dir():
                    return selected
                print(f"Selected path {selected} is not a directory. Please choose again.")
                continue
            if value == manual_index:
                return _prompt_target_path_manual()
            print(f"Choice must be between 1 and {manual_index}.")
        else:
            return _prompt_target_path_manual()


def _prompt_target_path_manual() -> Path:
    while True:
        value = input("Target path: ").strip()
        guess = Path(value).expanduser()
        if guess.exists() and guess.is_dir():
            return guess
        print(f"Path '{guess}' is not a directory. Please try again.")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    progress = make_progress_printer()
    progress("Loading SD card definitions.")
    cards = load_cards(args.cards_config)
    progress(f"Loaded {len(cards)} card definition(s).")

    if args.card_name:
        card = find_card(cards, args.card_name)
    else:
        card = prompt_card_selection(cards)
    progress(f"Selected card: {card.name}")

    if args.target_path:
        target_path = Path(args.target_path).expanduser()
        if not target_path.exists() or not target_path.is_dir():
            raise SystemExit(f"Target path '{target_path}' is not a valid directory.")
    else:
        progress("Attempting to discover mounted paths.")
        candidates = discover_mount_points()
        target_path = prompt_target_path(candidates)
    progress(f"Selected target path: {target_path}")

    plan = load_plan(args.plan)
    progress("Benchmark plan ready.")

    runner = BenchmarkRunner(
        card=card,
        target_path=target_path,
        plan=plan,
        work_dir=args.work_dir or args.results_dir,
        seed=args.seed,
        progress_callback=progress,
    )

    progress("Starting benchmark run.")
    outcome = runner.run()
    progress("Saving benchmark results.")
    saved_path = runner.save(outcome, destination=args.results_dir)
    progress("Benchmark complete.")
    print(f"Benchmark complete. Results saved to {saved_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

