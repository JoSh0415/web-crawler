from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path
from typing import Callable, List

from src.crawler import POLITENESS_DELAY, crawl_all_pages
from src.indexer import InvertedIndex, load_index, save_index
from src.search import format_index_entry, format_search_results, find_matching_doc_ids


DEFAULT_INDEX_PATH = Path("data/index.json")
DEFAULT_LOAD_RUNS = 5
DEFAULT_OPERATION_RUNS = 200

DEFAULT_PRINT_TERMS = [
    "nonsense",
    "good",
    "indifference",
]

DEFAULT_QUERIES = [
    "indifference",
    "good friends",
    '"good friends"',
    "indiffernce",
]


def percentile(sorted_values: List[float], fraction: float) -> float:
    """Return an approximate percentile from a sorted list of values."""
    if not sorted_values:
        return 0.0

    index = round((len(sorted_values) - 1) * fraction)
    return sorted_values[index]


def time_operation(operation: Callable[[], object], runs: int) -> dict[str, float]:
    """Measure one callable repeatedly and return summary timing statistics in ms."""
    durations_ms: List[float] = []

    for _ in range(runs):
        start = time.perf_counter()
        operation()
        end = time.perf_counter()
        durations_ms.append((end - start) * 1000.0)

    durations_ms.sort()

    return {
        "mean_ms": statistics.mean(durations_ms),
        "median_ms": statistics.median(durations_ms),
        "min_ms": durations_ms[0],
        "max_ms": durations_ms[-1],
        "p95_ms": percentile(durations_ms, 0.95),
    }


def count_total_postings(index: InvertedIndex) -> int:
    """Return the total number of term->document posting entries."""
    return sum(len(postings) for postings in index.index.values())


def count_total_occurrences(index: InvertedIndex) -> int:
    """Return the total number of indexed token occurrences across all postings."""
    return sum(
        posting.frequency
        for postings in index.index.values()
        for posting in postings.values()
    )


def format_ms(value: float) -> str:
    """Format a millisecond value for human-readable output."""
    return f"{value:.3f}"


def benchmark_load(index_path: Path, runs: int) -> dict[str, float]:
    """Benchmark loading the saved index from disk."""
    return time_operation(lambda: load_index(index_path), runs)


def benchmark_print_terms(index: InvertedIndex, runs: int) -> list[dict[str, object]]:
    """Benchmark the print command formatting path for several terms."""
    results: list[dict[str, object]] = []

    for term in DEFAULT_PRINT_TERMS:
        timings = time_operation(lambda term=term: format_index_entry(index, term), runs)
        posting_count = len(index.get_postings(term))
        results.append(
            {
                "term": term,
                "posting_count": posting_count,
                **timings,
            }
        )

    return results


def benchmark_queries(index: InvertedIndex, runs: int) -> list[dict[str, object]]:
    """Benchmark the find command retrieval/formatting path for several example queries."""
    results: list[dict[str, object]] = []

    for query in DEFAULT_QUERIES:
        timings = time_operation(lambda query=query: format_search_results(index, query), runs)
        result_count = len(find_matching_doc_ids(index, query))
        results.append(
            {
                "query": query,
                "result_count": result_count,
                **timings,
            }
        )

    return results


def maybe_time_polite_build(include_build: bool, index_path: Path) -> dict[str, object] | None:
    """
    Optionally benchmark a real polite build.

    This uses the live website and therefore respects the default politeness delay.
    It should be run sparingly.
    """
    if not include_build:
        return None

    start = time.perf_counter()
    index = crawl_all_pages(politeness_delay=POLITENESS_DELAY)
    end = time.perf_counter()

    save_index(index, index_path)

    return {
        "build_seconds": end - start,
        "documents_indexed": len(index.documents),
        "vocabulary_size": len(index.index),
    }


def generate_markdown_report(
    index_path: Path,
    index: InvertedIndex,
    load_stats: dict[str, float],
    print_stats: list[dict[str, object]],
    query_stats: list[dict[str, object]],
    build_stats: dict[str, object] | None,
    load_runs: int,
    operation_runs: int,
) -> str:
    """Generate a markdown benchmark report that can be pasted into the README."""
    lines: list[str] = []

    lines.append("## Benchmark Results")
    lines.append("")
    lines.append(f"Benchmarks were run against `{index_path}`.")
    lines.append("")
    lines.append("### Index Statistics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Documents | {len(index.documents)} |")
    lines.append(f"| Vocabulary size | {len(index.index)} |")
    lines.append(f"| Total postings | {count_total_postings(index)} |")
    lines.append(f"| Total indexed occurrences | {count_total_occurrences(index)} |")
    lines.append("")

    if build_stats is not None:
        lines.append("### Real Polite Build Timing")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|---|---:|")
        lines.append(f"| Build time (seconds) | {build_stats['build_seconds']:.2f} |")
        lines.append(f"| Documents indexed | {build_stats['documents_indexed']} |")
        lines.append(f"| Vocabulary size | {build_stats['vocabulary_size']} |")
        lines.append("")

    lines.append("### Load Benchmark")
    lines.append("")
    lines.append(f"Measured over {load_runs} runs.")
    lines.append("")
    lines.append("| Mean (ms) | Median (ms) | Min (ms) | Max (ms) | P95 (ms) |")
    lines.append("|---:|---:|---:|---:|---:|")
    lines.append(
        "| "
        f"{format_ms(load_stats['mean_ms'])} | "
        f"{format_ms(load_stats['median_ms'])} | "
        f"{format_ms(load_stats['min_ms'])} | "
        f"{format_ms(load_stats['max_ms'])} | "
        f"{format_ms(load_stats['p95_ms'])} |"
    )
    lines.append("")

    lines.append("### `print` Benchmark")
    lines.append("")
    lines.append(f"Measured over {operation_runs} runs per term.")
    lines.append("")
    lines.append("| Term | Postings | Mean (ms) | Median (ms) | P95 (ms) |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in print_stats:
        lines.append(
            f"| `{row['term']}` | {row['posting_count']} | "
            f"{format_ms(row['mean_ms'])} | "
            f"{format_ms(row['median_ms'])} | "
            f"{format_ms(row['p95_ms'])} |"
        )
    lines.append("")

    lines.append("### `find` Benchmark")
    lines.append("")
    lines.append(f"Measured over {operation_runs} runs per query.")
    lines.append("")
    lines.append("| Query | Results | Mean (ms) | Median (ms) | P95 (ms) |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in query_stats:
        lines.append(
            f"| `{row['query']}` | {row['result_count']} | "
            f"{format_ms(row['mean_ms'])} | "
            f"{format_ms(row['median_ms'])} | "
            f"{format_ms(row['p95_ms'])} |"
        )
    lines.append("")
    lines.append(
        "Build benchmarking against the live site was optional and, when used, "
        "was run with the required 6-second politeness delay rather than an unsafe fast mode."
    )
    lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the benchmark script."""
    parser = argparse.ArgumentParser(
        description="Benchmark index loading and search operations."
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Path to the compiled index file (default: data/index.json).",
    )
    parser.add_argument(
        "--load-runs",
        type=int,
        default=DEFAULT_LOAD_RUNS,
        help="Number of repeated load measurements.",
    )
    parser.add_argument(
        "--operation-runs",
        type=int,
        default=DEFAULT_OPERATION_RUNS,
        help="Number of repeated print/find measurements per term/query.",
    )
    parser.add_argument(
        "--include-build",
        action="store_true",
        help=(
            "Run one real polite build against the live site before benchmarking. "
            "This is slow and should be used sparingly."
        ),
    )
    return parser.parse_args()


def main() -> None:
    """Run benchmarks and print a markdown report."""
    args = parse_args()

    build_stats = maybe_time_polite_build(args.include_build, args.index)

    if not args.index.exists():
        raise FileNotFoundError(
            f"Index file not found at {args.index}. Run build first or pass --include-build."
        )

    load_stats = benchmark_load(args.index, args.load_runs)
    index = load_index(args.index)
    print_stats = benchmark_print_terms(index, args.operation_runs)
    query_stats = benchmark_queries(index, args.operation_runs)

    report = generate_markdown_report(
        index_path=args.index,
        index=index,
        load_stats=load_stats,
        print_stats=print_stats,
        query_stats=query_stats,
        build_stats=build_stats,
        load_runs=args.load_runs,
        operation_runs=args.operation_runs,
    )

    print(report)


if __name__ == "__main__":
    main()