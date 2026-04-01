import argparse

from python_bfs_exp.benchmark import BenchmarkConfig, benchmark


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a Graph500-style Python benchmark for plain BFS vs MapReduce-style BFS."
    )
    parser.add_argument(
        "--scales",
        nargs="+",
        type=int,
        default=[18, 19, 20, 21, 22, 23, 24],
        help="Graph scales to test. Each scale generates a graph with 2^scale nodes.",
    )
    parser.add_argument(
        "--avg-degree",
        type=int,
        default=8,
        help="Target average degree for the sparse random graph.",
    )
    parser.add_argument(
        "--roots",
        type=int,
        default=5,
        help="Number of non-isolated BFS roots sampled per scale.",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="How many times to repeat each root for each implementation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed for graph generation and root sampling.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    _, summary_rows = benchmark(
        BenchmarkConfig(
            scales=args.scales,
            avg_degree=args.avg_degree,
            roots=args.roots,
            repeats=args.repeats,
            seed=args.seed,
        )
    )

    print("Saved detailed benchmark rows to /Users/fan/graph500/python_bfs_exp/benchmark_results.csv")
    print("Saved summary benchmark rows to /Users/fan/graph500/python_bfs_exp/benchmark_summary.csv")
    for row in summary_rows:
        print(
            f"scale={row['scale']} impl={row['implementation']} runs={row['runs']} "
            f"min={float(row['min_seconds']):.6f}s "
            f"median={float(row['median_seconds']):.6f}s "
            f"mean={float(row['mean_seconds']):.6f}s"
        )


if __name__ == "__main__":
    main()
