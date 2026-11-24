"""CLI for ``uv run python -m cryptomodel.extract --start 2025-11-01 --end 2025-11-03``.

The worker function lives here, not in ``__main__``, because spawned worker processes
must be able to import it by module name.

Each (table, day) runs in a fresh worker process, so its recorded peak memory is its
own. Total memory is about ``--workers`` times one task's peak. In download mode the
raw files of at most ``--workers`` tasks sit in the staging directory at once. See
reports/phase1/extraction_trial.md for measured numbers.
"""

from __future__ import annotations

import argparse
import datetime as dt
import multiprocessing as mp
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from cryptomodel.extract.constants import TABLES
from cryptomodel.extract.pipeline import Limits, extract_table_day
from cryptomodel.extract.source import LocalSource, S3Source, Source
from cryptomodel.paths import data_dir, raw_filtered_dir

# Biggest first within a day, so slow tables start early.
DEFAULT_ORDER = ("traces", "logs", "transactions", "contracts", "blocks")


@dataclass(frozen=True)
class Task:
    table: str
    day: dt.date
    out_root: Path
    source_root: Path | None
    force: bool
    limits: Limits
    staging_dir: Path | None
    connections: int


@dataclass(frozen=True)
class Outcome:
    task: Task
    status: Literal["written", "skipped", "failed"]
    rows: int = 0
    output_bytes: int = 0
    wall_seconds: float = 0.0
    peak_rss_bytes: int = 0
    error: str = ""


def date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    return [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]


def _source(root: Path | None) -> Source:
    return LocalSource(root) if root is not None else S3Source()


def run_task(task: Task) -> Outcome:
    try:
        r = extract_table_day(
            _source(task.source_root),
            task.table,
            task.day,
            task.out_root,
            force=task.force,
            limits=task.limits,
            staging_dir=task.staging_dir,
            connections=task.connections,
        )
    except Exception:
        return Outcome(task, "failed", error=traceback.format_exc(limit=3))
    m = r.manifest
    return Outcome(
        task, r.status, m.rows, m.output_bytes, m.wall_seconds, m.peak_rss_bytes
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m cryptomodel.extract", description=__doc__
    )
    p.add_argument("--start", type=dt.date.fromisoformat, required=True)
    p.add_argument("--end", type=dt.date.fromisoformat, required=True, help="inclusive")
    p.add_argument("--tables", nargs="+", choices=TABLES, default=list(DEFAULT_ORDER))
    p.add_argument(
        "--workers",
        type=int,
        default=5,
        help="(table, day) tasks run at once; 5 = one day",
    )
    p.add_argument("--duckdb-threads", type=int, default=2)
    p.add_argument("--duckdb-memory", default="1GB")
    p.add_argument(
        "--mode",
        choices=("download", "stream"),
        default="download",
        help="download: fetch whole files with parallel ranged GETs into "
        "$CRYPTOMODEL_DATA_DIR/tmp/extract, filter locally, delete (default, faster); "
        "stream: read remote Parquet column chunks directly (no local raw copy)",
    )
    p.add_argument(
        "--connections",
        type=int,
        default=16,
        help="parallel GETs per task (download mode)",
    )
    p.add_argument(
        "--force", action="store_true", help="re-extract even if a manifest matches"
    )
    p.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="local directory with the AWS layout instead of the public S3 bucket",
    )
    args = p.parse_args(argv)
    if args.end < args.start:
        p.error("--end is before --start")
    if args.workers < 1 or args.connections < 1:
        p.error("--workers and --connections must be at least 1")
    if args.mode == "download" and args.source_root is not None:
        p.error("--source-root is a local mirror; use --mode stream with it")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_root = raw_filtered_dir()
    staging = data_dir() / "tmp" / "extract" if args.mode == "download" else None
    limits = Limits(args.duckdb_threads, args.duckdb_memory)
    tables = [t for t in DEFAULT_ORDER if t in args.tables]
    tasks = [
        Task(
            t,
            d,
            out_root,
            args.source_root,
            args.force,
            limits,
            staging,
            args.connections,
        )
        for d in date_range(args.start, args.end)
        for t in tables
    ]
    print(
        f"{len(tasks)} tasks -> {out_root}, mode={args.mode}, workers={args.workers}, "
        f"connections={args.connections}",
        flush=True,
    )
    started = time.monotonic()
    failed = 0
    ctx = mp.get_context("spawn")
    with ProcessPoolExecutor(
        args.workers, mp_context=ctx, max_tasks_per_child=1
    ) as pool:
        futures = [pool.submit(run_task, t) for t in tasks]
        for fut in as_completed(futures):
            try:
                o = fut.result()
            except Exception as exc:  # a worker died (e.g. killed for memory)
                o = Outcome(tasks[futures.index(fut)], "failed", error=repr(exc))
            t = o.task
            if o.status == "failed":
                failed += 1
                print(
                    f"{t.day} {t.table:<12} failed\n{o.error}",
                    file=sys.stderr,
                    flush=True,
                )
                print(f"{t.day} {t.table:<12} failed", flush=True)
                continue
            print(
                f"{t.day} {t.table:<12} {o.status:<7} rows={o.rows:>11,} "
                f"bytes={o.output_bytes:>14,} s={o.wall_seconds:>7.1f} "
                f"peak_rss_mb={o.peak_rss_bytes / 2**20:>7.0f}",
                flush=True,
            )
    elapsed = time.monotonic() - started
    print(f"done in {elapsed:.0f}s, {failed} failed", flush=True)
    return 1 if failed else 0
