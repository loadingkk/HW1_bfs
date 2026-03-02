import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


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


def normalize_key(key: str) -> str:
    return " ".join(key.strip().lower().split())


def get_metric(metrics: Dict[str, float], *candidates: str) -> float:
    normalized = {normalize_key(k): v for k, v in metrics.items()}
    for candidate in candidates:
        n = normalize_key(candidate)
        if n in normalized:
            return normalized[n]
    raise KeyError(candidates[0] if candidates else "")


def load_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def to_float(value: str) -> float:
    return float(value.strip())


def collect_series(
    rows: Iterable[Dict[str, str]],
) -> Dict[str, Dict[str, Dict[int, Dict[str, float]]]]:
    series: Dict[str, Dict[str, Dict[int, Dict[str, float]]]] = {}
    for row in rows:
        location = row.get("location", "").strip().lower()
        impl = row.get("impl", "").strip().lower()
        scale_raw = row.get("scale", "").strip()
        if not location or not impl or not scale_raw:
            continue
        scale = int(scale_raw)
        entry = {
            "min": to_float(row.get("bfs_min_time", "nan")),
            "median": to_float(row.get("bfs_median_time", "nan")),
            "mean": to_float(row.get("bfs_mean_time", "nan")),
        }
        series.setdefault(location, {}).setdefault(impl, {})[scale] = entry
    return series


def common_scales(left: Dict[int, Dict[str, float]], right: Dict[int, Dict[str, float]]) -> List[int]:
    return sorted(set(left.keys()) & set(right.keys()))


def ensure_out_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)


def save_local_impl_plot(series: Dict[str, Dict[str, Dict[int, Dict[str, float]]]], out_dir: Path) -> Path:
    import matplotlib.pyplot as plt

    local = series.get("local", {})
    ref = local.get("reference", {})
    cust = local.get("custom", {})
    if not ref and not cust:
        raise ValueError("No local data found in CSV data.")

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ref_scales = sorted(ref.keys())
    cust_scales = sorted(cust.keys())
    if ref_scales:
        ax.plot(ref_scales, [ref[s]["median"] for s in ref_scales], marker="o", label="reference")
    if cust_scales:
        ax.plot(cust_scales, [cust[s]["median"] for s in cust_scales], marker="o", label="custom")

    ax.set_title("Figure 1: local custom vs reference (median_time)")
    ax.set_xlabel("SCALE")
    ax.set_ylabel("seconds")
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.legend()

    fig.tight_layout()
    out_path = out_dir / "fig1_local_custom_vs_reference.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_cloud_impl_plot(series: Dict[str, Dict[str, Dict[int, Dict[str, float]]]], out_dir: Path) -> Path:
    import matplotlib.pyplot as plt

    cloud = series.get("cloud", {})
    ref = cloud.get("reference", {})
    cust = cloud.get("custom", {})
    if not ref and not cust:
        raise ValueError("No cloud data found in CSV data.")

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ref_scales = sorted(ref.keys())
    cust_scales = sorted(cust.keys())
    if ref_scales:
        ax.plot(ref_scales, [ref[s]["median"] for s in ref_scales], marker="o", label="reference")
    if cust_scales:
        ax.plot(cust_scales, [cust[s]["median"] for s in cust_scales], marker="o", label="custom")

    ax.set_title("Figure 2: cloud custom vs reference (median_time)")
    ax.set_xlabel("SCALE")
    ax.set_ylabel("seconds")
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.legend()

    fig.tight_layout()
    out_path = out_dir / "fig2_cloud_custom_vs_reference.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_custom_cross_location_plot(series: Dict[str, Dict[str, Dict[int, Dict[str, float]]]], out_dir: Path) -> Path:
    import matplotlib.pyplot as plt

    local = series.get("local", {})
    cloud = series.get("cloud", {})

    local_custom = local.get("custom", {})
    cloud_custom = cloud.get("custom", {})
    if not local_custom and not cloud_custom:
        raise ValueError("No local/cloud custom data found.")

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    local_scales = sorted(local_custom.keys())
    cloud_scales = sorted(cloud_custom.keys())
    if local_scales:
        ax.plot(local_scales, [local_custom[s]["median"] for s in local_scales], marker="o", label="local")
    if cloud_scales:
        ax.plot(cloud_scales, [cloud_custom[s]["median"] for s in cloud_scales], marker="o", label="cloud")

    ax.set_title("Figure 3: custom local vs cloud (median_time)")
    ax.set_xlabel("SCALE")
    ax.set_ylabel("seconds")
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.legend()

    fig.tight_layout()
    out_path = out_dir / "fig3_custom_local_vs_cloud.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_reference_cross_location_plot(series: Dict[str, Dict[str, Dict[int, Dict[str, float]]]], out_dir: Path) -> Path:
    import matplotlib.pyplot as plt

    local = series.get("local", {})
    cloud = series.get("cloud", {})
    local_ref = local.get("reference", {})
    cloud_ref = cloud.get("reference", {})
    if not local_ref and not cloud_ref:
        raise ValueError("No local/cloud reference data found.")

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    local_scales = sorted(local_ref.keys())
    cloud_scales = sorted(cloud_ref.keys())
    if local_scales:
        ax.plot(local_scales, [local_ref[s]["median"] for s in local_scales], marker="o", label="local")
    if cloud_scales:
        ax.plot(cloud_scales, [cloud_ref[s]["median"] for s in cloud_scales], marker="o", label="cloud")

    ax.set_title("Figure 4: reference local vs cloud (median_time)")
    ax.set_xlabel("SCALE")
    ax.set_ylabel("seconds")
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.legend()

    fig.tight_layout()
    out_path = out_dir / "fig4_reference_local_vs_cloud.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_from_csv(csv_path: Path, out_dir: Path) -> List[Path]:
    rows = load_csv_rows(csv_path)
    series = collect_series(rows)

    ensure_out_dir(out_dir)
    outputs = [
        save_local_impl_plot(series, out_dir),
        save_cloud_impl_plot(series, out_dir),
        save_custom_cross_location_plot(series, out_dir),
        save_reference_cross_location_plot(series, out_dir),
    ]
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Graph500 reference vs custom outputs.")
    parser.add_argument(
        "--from-csv",
        action="store_true",
        help="Generate multi-figure comparison plots from benchmark_results.csv",
    )
    parser.add_argument(
        "--csv",
        default="result/benchmark_results.csv",
        help="Path to benchmark CSV file used with --from-csv",
    )
    parser.add_argument(
        "--out-dir",
        default="result/plots",
        help="Output directory for CSV-based plots",
    )
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

    default_invocation = len(sys.argv) == 1

    if default_invocation:
        args.from_csv = True

    if args.from_csv:
        try:
            outputs = plot_from_csv(Path(args.csv), Path(args.out_dir))
        except Exception as exc:
            raise SystemExit(f"Failed to generate CSV plots: {exc}") from exc
        print("Saved plots:")
        for output in outputs:
            print(f"- {output}")
        return

    ref_path = Path(args.reference)
    cust_path = Path(args.custom)

    ref = parse_metrics(ref_path)
    cust = parse_metrics(cust_path)

    try:
        data: List[Tuple[str, float, float]] = [
            (
                "mean_time",
                get_metric(ref, "bfs mean_time", "bfs  mean_time", "mean_time"),
                get_metric(cust, "bfs mean_time", "bfs  mean_time", "mean_time"),
            ),
            (
                "median_time",
                get_metric(ref, "bfs median_time", "bfs  median_time", "median_time"),
                get_metric(cust, "bfs median_time", "bfs  median_time", "median_time"),
            ),
            (
                "harmonic_mean_TEPS",
                get_metric(ref, "bfs harmonic_mean_TEPS", "bfs  harmonic_mean_TEPS", "harmonic_mean_TEPS"),
                get_metric(cust, "bfs harmonic_mean_TEPS", "bfs  harmonic_mean_TEPS", "harmonic_mean_TEPS"),
            ),
        ]
    except KeyError as exc:
        raise SystemExit(
            f"Missing metric '{exc.args[0]}' in one of the files. "
            "Tip: run without args to plot from CSV, or use --from-csv explicitly."
        ) from exc

    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        print("matplotlib is required for plotting.")
        print("Values:")
        for k, r, c in data:
            print(f"{k}: reference={r} custom={c}")
        raise SystemExit(1) from exc

    labels = [k for k, _, _ in data]
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
