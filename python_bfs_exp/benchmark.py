import csv
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

from python_bfs_exp.bfs import bfs
from python_bfs_exp.graph_gen import choose_roots, generate_graph
from python_bfs_exp.mr_bfs import mr_bfs_with_stats


EXPERIMENT_DIR = Path(__file__).resolve().parent
DETAIL_RESULTS_PATH = EXPERIMENT_DIR / "benchmark_results.csv"
SUMMARY_RESULTS_PATH = EXPERIMENT_DIR / "benchmark_summary.csv"
DETAIL_FIELDS = [
    "scale",
    "graph_size",
    "avg_degree",
    "graph_seed",
    "root",
    "repeat",
    "implementation",
    "elapsed_seconds",
    "visited_count",
    "levels",
    "mapped_pairs",
]
SUMMARY_FIELDS = [
    "scale",
    "graph_size",
    "implementation",
    "runs",
    "min_seconds",
    "median_seconds",
    "mean_seconds",
    "mean_visited_count",
    "mean_levels",
    "mean_mapped_pairs",
]


@dataclass
class BenchmarkConfig:
    scales: list[int]
    avg_degree: int
    roots: int
    repeats: int
    seed: int
    detail_output: Path = DETAIL_RESULTS_PATH
    summary_output: Path = SUMMARY_RESULTS_PATH


@dataclass
class BenchmarkRow:
    scale: int
    graph_size: int
    avg_degree: int
    graph_seed: int
    root: int
    repeat: int
    implementation: str
    elapsed_seconds: float
    visited_count: int
    levels: int
    mapped_pairs: int


def scale_to_graph_size(scale):
    if scale < 1:
        raise ValueError("scale must be >= 1")
    return 1 << scale


def run_plain_bfs(graph, scale, avg_degree, graph_seed, root, repeat):
    start = time.perf_counter()
    order = bfs(graph, root)
    elapsed_seconds = time.perf_counter() - start
    return BenchmarkRow(
        scale=scale,
        graph_size=len(graph),
        avg_degree=avg_degree,
        graph_seed=graph_seed,
        root=root,
        repeat=repeat,
        implementation="plain_bfs",
        elapsed_seconds=elapsed_seconds,
        visited_count=len(order),
        levels=-1,
        mapped_pairs=-1,
    )


def run_mr_bfs(graph, scale, avg_degree, graph_seed, root, repeat):
    start = time.perf_counter()
    order, stats = mr_bfs_with_stats(graph, root)
    elapsed_seconds = time.perf_counter() - start
    return BenchmarkRow(
        scale=scale,
        graph_size=len(graph),
        avg_degree=avg_degree,
        graph_seed=graph_seed,
        root=root,
        repeat=repeat,
        implementation="mapreduce_bfs",
        elapsed_seconds=elapsed_seconds,
        visited_count=len(order),
        levels=stats["levels"],
        mapped_pairs=stats["mapped_pairs"],
    )


def write_detail_results(rows, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DETAIL_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(detail_row_to_dict(row))


def detail_row_to_dict(row):
    return {
        "scale": row.scale,
        "graph_size": row.graph_size,
        "avg_degree": row.avg_degree,
        "graph_seed": row.graph_seed,
        "root": row.root,
        "repeat": row.repeat,
        "implementation": row.implementation,
        "elapsed_seconds": f"{row.elapsed_seconds:.10g}",
        "visited_count": row.visited_count,
        "levels": row.levels,
        "mapped_pairs": row.mapped_pairs,
    }


def initialize_detail_results(output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DETAIL_FIELDS)
        writer.writeheader()


def append_detail_result(row, output_path):
    with output_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DETAIL_FIELDS)
        writer.writerow(detail_row_to_dict(row))


def build_summary_rows(rows):
    grouped = {}
    for row in rows:
        key = (row.scale, row.graph_size, row.implementation)
        grouped.setdefault(key, []).append(row)

    summary_rows = []
    for (scale, graph_size, implementation), group in sorted(grouped.items()):
        elapsed_values = [row.elapsed_seconds for row in group]
        visited_values = [row.visited_count for row in group]
        level_values = [row.levels for row in group if row.levels >= 0]
        mapped_values = [row.mapped_pairs for row in group if row.mapped_pairs >= 0]

        summary_rows.append(
            {
                "scale": scale,
                "graph_size": graph_size,
                "implementation": implementation,
                "runs": len(group),
                "min_seconds": f"{min(elapsed_values):.10g}",
                "median_seconds": f"{statistics.median(elapsed_values):.10g}",
                "mean_seconds": f"{statistics.fmean(elapsed_values):.10g}",
                "mean_visited_count": f"{statistics.fmean(visited_values):.10g}",
                "mean_levels": f"{statistics.fmean(level_values):.10g}" if level_values else "",
                "mean_mapped_pairs": f"{statistics.fmean(mapped_values):.10g}" if mapped_values else "",
            }
        )
    return summary_rows


def write_summary_results(rows, output_path):
    summary_rows = build_summary_rows(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summary_rows)
    return summary_rows


def benchmark(config):
    rows = []
    initialize_detail_results(config.detail_output)

    for index, scale in enumerate(config.scales):
        graph_size = scale_to_graph_size(scale)
        graph_seed = config.seed + index
        print(f"[graph] scale={scale} graph_size={graph_size} seed={graph_seed}")
        graph = generate_graph(num_nodes=graph_size, avg_degree=config.avg_degree, seed=graph_seed)
        roots = choose_roots(graph=graph, root_count=config.roots, seed=graph_seed)
        print(f"[roots] scale={scale} sampled_roots={len(roots)}")

        for root in roots:
            for repeat in range(1, config.repeats + 1):
                print(f"[run] scale={scale} root={root} repeat={repeat} impl=plain_bfs")
                plain_row = run_plain_bfs(
                    graph=graph,
                    scale=scale,
                    avg_degree=config.avg_degree,
                    graph_seed=graph_seed,
                    root=root,
                    repeat=repeat,
                )
                rows.append(plain_row)
                append_detail_result(plain_row, config.detail_output)

                print(f"[run] scale={scale} root={root} repeat={repeat} impl=mapreduce_bfs")
                mr_row = run_mr_bfs(
                    graph=graph,
                    scale=scale,
                    avg_degree=config.avg_degree,
                    graph_seed=graph_seed,
                    root=root,
                    repeat=repeat,
                )
                rows.append(mr_row)
                append_detail_result(mr_row, config.detail_output)

        summary_rows = write_summary_results(rows, config.summary_output)
        scale_rows = [row for row in summary_rows if int(row["scale"]) == scale]
        for row in scale_rows:
            print(
                f"[summary] scale={row['scale']} impl={row['implementation']} runs={row['runs']} "
                f"min={float(row['min_seconds']):.6f}s "
                f"median={float(row['median_seconds']):.6f}s "
                f"mean={float(row['mean_seconds']):.6f}s"
            )

    summary_rows = write_summary_results(rows, config.summary_output)
    return rows, summary_rows
