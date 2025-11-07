# SD Card Benchmark Lab

Utility repository for evaluating SD card performance on Raspberry Pi 5 + Hailo-8 Edge AI workloads, inspired by the BS4U-TECH analysis of alternative cards for official images.

## Quick Start

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Flash the desired Raspberry Pi OS image to the SD card under test and mount it on your workstation.
4. Update `data/sd_cards.yaml` with the card details if necessary.
5. Run the benchmark:
   ```
   python scripts/run_benchmark.py "SanDisk Extreme MicroSDXC 64GB" D:\ --results-dir results
   ```
   Replace `D:\` with the mounted path for the SD card.
6. Repeat for each SD card product, using the same plan or adjusting `data/default_plan.yaml`.

## Reports

After collecting JSON result files in `results/`, generate summary assets:

```
python scripts/generate_report.py results --output-dir reports
```

This command produces:

- `reports/summary.md` – Markdown table comparing average throughput per test.
- `reports/comparison.png` – Bar chart for quick visual comparison.

## Repository Layout

- `data/`: SD card descriptors and default benchmark plan.
- `scripts/`: CLI utilities to run benchmarks and build reports.
- `src/sdcard_benchmark/`: Core benchmarking logic and helpers.
- `docs/`: Website-ready narrative content and guidelines for sharing results.

## Safety Notes

- The benchmark writes large temporary files (default 2 GiB). Ensure free space is available.
- All temporary files are removed by default; set `cleanup: false` in the plan to retain artifacts.
- Run the tests on freshly imaged cards to minimize fragmentation.

## Extending

- Adjust the YAML plan to test different file sizes or sample counts.
- Add new metrics (e.g., temperature logging) by extending `sdcard_benchmark.runner`.
- Include cost-per-performance analyses in `sdcard_benchmark.summary` or the reporting scripts.

