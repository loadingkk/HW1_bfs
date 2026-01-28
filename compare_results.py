import argparse
import re
from pathlib import Path
from typing import Dict


def parse_metrics(path: Path) -> Dict[str, float]:
    metrics = {}
    pattern = re.compile(r"^([^:]+):\s+([0-9.eE+-]+)\s*$")
    pattern_marked = re.compile(r"^([^:]+):\s+!\s*([0-9.eE+-]+)\s*$")
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            m = pattern.match(stripped)
            if not m:
                m = pattern_marked.match(stripped)
            if not m:
                continue
            key = m.group(1).strip()
            try:
                val = float(m.group(2))
            except ValueError:
                continue
            metrics[key] = val
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Graph500 reference vs custom outputs.")
    parser.add_argument(
        "--reference",
        default="src/graph500_reference_bfs_stdout.txt",
        help="Path to reference stdout file",
    )
    parser.add_argument(
        "--custom",
        default="src/graph500_custom_bfs_stdout.txt",
        help="Path to custom stdout file",
    )
    parser.add_argument(
        "--out",
        default="comparison.png",
        help="Output image path",
    )
    args = parser.parse_args()

    ref_path = Path(args.reference)
    cust_path = Path(args.custom)

    ref = parse_metrics(ref_path)
    cust = parse_metrics(cust_path)

    keys = [
        "bfs  mean_time",
        "bfs  median_time",
        "bfs  harmonic_mean_TEPS",
    ]

    data = []
    for k in keys:
        if k not in ref or k not in cust:
            raise SystemExit(f"Missing metric '{k}' in one of the files.")
        data.append((k, ref[k], cust[k]))

    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        print("matplotlib is required for plotting.")
        print("Values:")
        for k, r, c in data:
            print(f"{k}: reference={r} custom={c}")
        raise SystemExit(1) from exc

    labels = [k.replace("bfs  ", "") for k, _, _ in data]
    ref_vals = [r for _, r, _ in data]
    cust_vals = [c for _, _, c in data]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=False)
    for idx, ax in enumerate(axes):
        ax.bar(["reference", "custom"], [ref_vals[idx], cust_vals[idx]], color=["#1f77b4", "#ff7f0e"])
        ax.set_title(labels[idx])
        ax.grid(axis="y", linestyle=":", alpha=0.4)

    fig.suptitle("Graph500 BFS Comparison", y=1.02)
    fig.tight_layout()
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    print(f"Saved plot to {args.out}")


if __name__ == "__main__":
    main()
