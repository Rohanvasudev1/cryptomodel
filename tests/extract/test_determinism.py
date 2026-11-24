"""Output is sorted on each table's natural key and byte-identical across runs."""

from __future__ import annotations

import random
from pathlib import Path

import pyarrow.parquet as pq

from cryptomodel.extract.constants import EVENT_TOPICS
from cryptomodel.extract.pipeline import Limits, extract_table_day
from cryptomodel.extract.source import LocalSource

from .conftest import DAY, addr, h32, make_table

TRANSFER = EVENT_TOPICS["ERC20_TRANSFER"].topic0


def _write_shuffled_logs(aws_root: Path, n: int, parts: int) -> None:
    """``n`` logs over ``parts`` files, shuffled, in many small row groups so DuckDB
    scans them on several threads."""
    rows = [
        {
            "block_number": 1_000 + i // 50,
            "log_index": i % 50,
            "transaction_index": (i % 50) // 5,
            "address": addr(i % 97),
            "topics": [TRANSFER, h32(i), h32(i + 1)],
            "data": "0x" + f"{i:064x}",
        }
        for i in range(n)
    ]
    random.Random(0).shuffle(rows)
    d = aws_root / "logs" / f"date={DAY.isoformat()}"
    d.mkdir(parents=True)
    for p in range(parts):
        pq.write_table(
            make_table("logs", rows[p::parts]),
            d / f"part-{p:05d}.snappy.parquet",
            row_group_size=1_000,
        )


def test_same_day_twice_is_byte_identical(aws_root: Path, tmp_path: Path) -> None:
    _write_shuffled_logs(aws_root, n=60_000, parts=3)
    source = LocalSource(aws_root)
    limits = Limits(duckdb_threads=4)
    rel = Path("logs") / f"date={DAY.isoformat()}" / "data.parquet"

    outs = []
    for run in ("a", "b", "c"):
        extract_table_day(source, "logs", DAY, tmp_path / run, limits=limits)
        outs.append((tmp_path / run / rel).read_bytes())

    assert outs[0] == outs[1] == outs[2]
    keys = pq.read_table(tmp_path / "a" / rel, columns=["block_number", "log_index"])
    pairs = list(zip(*(c.to_pylist() for c in keys.columns), strict=True))
    assert len(pairs) == 60_000
    assert pairs == sorted(pairs)
    assert not (
        tmp_path / "a" / "logs" / f"date={DAY.isoformat()}" / "duckdb_tmp"
    ).exists()


def test_traces_sort_depth_first(aws_root: Path, tmp_path: Path) -> None:
    order = ["None", "0", "0,2", "0,10", "1", "2", "10"]
    rows = [
        {"trace_type": "suicide", "transaction_index": 0, "trace_address": a}
        for a in reversed(order)
    ]
    d = aws_root / "traces" / f"date={DAY.isoformat()}"
    d.mkdir(parents=True)
    pq.write_table(make_table("traces", rows), d / "part-00000.snappy.parquet")

    extract_table_day(LocalSource(aws_root), "traces", DAY, tmp_path / "out")

    out = pq.read_table(tmp_path / "out" / "traces" / f"date={DAY.isoformat()}")
    assert out.column("trace_address").to_pylist() == [None, *order[1:]]
