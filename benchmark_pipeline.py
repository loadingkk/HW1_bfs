import argparse
import csv
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
RESULT_DIR = ROOT_DIR / "result"
RAW_DIR = RESULT_DIR / "raw"
CSV_PATH = RESULT_DIR / "benchmark_results.csv"

DEFAULT_SCALES = [18, 19, 20, 21, 22, 23, 24]

CSV_COLUMNS = [
    "timestamp_utc",
    "location",
    "scale",
    "impl",
    "binary",
    "bfs_min_time",
    "bfs_median_time",
    "bfs_mean_time",
    "stdout_file",
    "stderr_file",
]


@dataclass
class RunResult:
    timestamp_utc: str
    location: str
    scale: int
    impl: str
    binary: str
    bfs_min_time: float
    bfs_median_time: float
    bfs_mean_time: float
    stdout_file: str
    stderr_file: str

    def as_row(self) -> Dict[str, str]:
        return {
            "timestamp_utc": self.timestamp_utc,
            "location": self.location,
            "scale": str(self.scale),
            "impl": self.impl,
            "binary": self.binary,
            "bfs_min_time": f"{self.bfs_min_time:.10g}",
            "bfs_median_time": f"{self.bfs_median_time:.10g}",
            "bfs_mean_time": f"{self.bfs_mean_time:.10g}",
            "stdout_file": self.stdout_file,
            "stderr_file": self.stderr_file,
        }


def parse_metrics(text: str) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    pattern = re.compile(r"^([^:]+):\s+!?\s*([0-9.eE+-]+)\s*$")
    for line in text.splitlines():
        stripped = line.strip()
        matched = pattern.match(stripped)
        if not matched:
            continue
        key = matched.group(1).strip()
        value = matched.group(2)
        try:
            metrics[key] = float(value)
        except ValueError:
            continue
    return metrics


def ensure_paths() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def load_existing_rows() -> List[Dict[str, str]]:
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    return rows


def write_rows(rows: Iterable[Dict[str, str]]) -> None:
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})


def upsert_row(new_row: Dict[str, str]) -> None:
    key = (new_row["location"], new_row["scale"], new_row["impl"])
    rows = load_existing_rows()
    replaced = False
    for index, row in enumerate(rows):
        row_key = (row.get("location", ""), row.get("scale", ""), row.get("impl", ""))
        if row_key == key:
            rows[index] = new_row
            replaced = True
            break
    if not replaced:
        rows.append(new_row)
    rows.sort(key=lambda item: (item.get("location", ""), int(item.get("scale", "0")), item.get("impl", "")))
    write_rows(rows)


def run_binary(binary_path: Path, scale: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(binary_path), str(scale)],
        cwd=SRC_DIR,
        capture_output=True,
        text=True,
        check=False,
    )


def run_once(location: str, scale: int, impl: str, binary_name: str) -> RunResult:
    binary_path = SRC_DIR / binary_name
    if not binary_path.exists():
        raise FileNotFoundError(
            f"Missing binary: {binary_path}. Please ensure it is compiled before running this script."
        )

    completed = run_binary(binary_path, scale)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Run failed: {binary_name} {scale}\n"
            f"Exit code: {completed.returncode}\n"
            f"stderr:\n{completed.stderr}"
        )

    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_dir = RAW_DIR / location / f"scale_{scale}"
    run_dir.mkdir(parents=True, exist_ok=True)

    stdout_path = run_dir / f"{impl}_stdout.txt"
    stderr_path = run_dir / f"{impl}_stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    metrics = parse_metrics(completed.stdout)
    required_keys = ["bfs  min_time", "bfs  median_time", "bfs  mean_time"]
    missing = [key for key in required_keys if key not in metrics]
    if missing:
        raise ValueError(
            f"Missing required metrics in stdout for {impl} scale {scale}: {', '.join(missing)}"
        )

    return RunResult(
        timestamp_utc=timestamp_utc,
        location=location,
        scale=scale,
        impl=impl,
        binary=binary_name,
        bfs_min_time=metrics["bfs  min_time"],
        bfs_median_time=metrics["bfs  median_time"],
        bfs_mean_time=metrics["bfs  mean_time"],
        stdout_file=str(stdout_path.relative_to(ROOT_DIR)),
        stderr_file=str(stderr_path.relative_to(ROOT_DIR)),
    )


def run_benchmarks(location: str, scales: Iterable[int]) -> None:
    ensure_paths()
    for scale in scales:
        print(f"[run] location={location} scale={scale} impl=reference")
        ref = run_once(location=location, scale=scale, impl="reference", binary_name="graph500_reference_bfs")
        upsert_row(ref.as_row())
        print(f"[saved] {CSV_PATH} <- {location} scale={scale} reference")

        print(f"[run] location={location} scale={scale} impl=custom")
        custom = run_once(location=location, scale=scale, impl="custom", binary_name="graph500_custom_bfs")
        upsert_row(custom.as_row())
        print(f"[saved] {CSV_PATH} <- {location} scale={scale} custom")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Graph500 BFS binaries and persist metrics to result CSV.")
    parser.add_argument(
        "--location",
        required=True,
        choices=["local", "cloud"],
        help="Execution location label stored in result CSV.",
    )
    parser.add_argument(
        "--scales",
        nargs="+",
        type=int,
        default=DEFAULT_SCALES,
        help="Scale list to run, e.g. --scales 18 19 20",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_benchmarks(location=args.location, scales=args.scales)


if __name__ == "__main__":
    main()
