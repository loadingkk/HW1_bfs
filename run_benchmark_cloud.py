from benchmark_pipeline import DEFAULT_SCALES, run_benchmarks


def main() -> None:
    run_benchmarks(location="cloud", scales=DEFAULT_SCALES)


if __name__ == "__main__":
    main()
