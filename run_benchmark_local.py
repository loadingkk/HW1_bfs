import argparse

from benchmark_pipeline import DEFAULT_SCALES, run_benchmarks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local Graph500 benchmarks.")
    parser.add_argument(
        "--scales",
        nargs="+",
        type=int,
        default=DEFAULT_SCALES,
        help="Scale list to run, e.g. --scales 24 or --scales 22 24",
    )
    parser.add_argument(
        "--np",
        type=int,
        default=1,
        help="MPI process count. Use >1 to run via mpirun, e.g. --np 8",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.np < 1:
        raise ValueError("--np must be >= 1")
    run_benchmarks(location="local", scales=args.scales, np=args.np)


if __name__ == "__main__":
    main()
