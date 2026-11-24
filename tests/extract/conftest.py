"""Synthetic AWS-shaped Parquet fixtures. No network.

The schemas copy the real AWS ``v1.0/eth`` schemas (read from the 2025-11-01 partition
footers). AWS writes missing strings in ``traces`` as the literal ``'None'``; the fixtures
do the same so the filters are tested against that quirk.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

TS = pa.timestamp("ns")

AWS_SCHEMAS: dict[str, pa.Schema] = {
    "blocks": pa.schema(
        [
            ("difficulty", pa.float64()),
            ("hash", pa.string()),
            ("miner", pa.string()),
            ("nonce", pa.string()),
            ("number", pa.int64()),
            ("size", pa.int64()),
            ("timestamp", TS),
            ("base_fee_per_gas", pa.int64()),
            ("gas_limit", pa.int64()),
            ("gas_used", pa.int64()),
            ("extra_data", pa.string()),
            ("logs_bloom", pa.string()),
            ("parent_hash", pa.string()),
            ("state_root", pa.string()),
            ("receipts_root", pa.string()),
            ("transactions_root", pa.string()),
            ("sha3_uncles", pa.string()),
            ("transaction_count", pa.int64()),
            ("date", pa.string()),
            ("last_modified", TS),
        ]
    ),
    "transactions": pa.schema(
        [
            ("gas", pa.int64()),
            ("hash", pa.string()),
            ("input", pa.string()),
            ("nonce", pa.int64()),
            ("value", pa.float64()),
            ("block_number", pa.int64()),
            ("block_hash", pa.string()),
            ("transaction_index", pa.int64()),
            ("from_address", pa.string()),
            ("to_address", pa.string()),
            ("gas_price", pa.int64()),
            ("receipt_cumulative_gas_used", pa.int64()),
            ("receipt_gas_used", pa.int64()),
            ("receipt_contract_address", pa.string()),
            ("receipt_status", pa.int64()),
            ("receipt_effective_gas_price", pa.int64()),
            ("transaction_type", pa.int64()),
            ("max_fee_per_gas", pa.int64()),
            ("max_priority_fee_per_gas", pa.int64()),
            ("block_timestamp", TS),
            ("date", pa.string()),
            ("last_modified", TS),
        ]
    ),
    "logs": pa.schema(
        [
            ("address", pa.string()),
            ("topics", pa.list_(pa.string())),
            ("data", pa.string()),
            ("transaction_index", pa.int64()),
            ("log_index", pa.int64()),
            ("transaction_hash", pa.string()),
            ("block_number", pa.int64()),
            ("block_hash", pa.string()),
            ("block_timestamp", TS),
            ("date", pa.string()),
            ("last_modified", TS),
        ]
    ),
    "traces": pa.schema(
        [
            ("block_number", pa.int64()),
            ("transaction_hash", pa.string()),
            ("transaction_index", pa.int64()),
            ("error", pa.string()),
            ("status", pa.int64()),
            ("trace_id", pa.string()),
            ("subtraces", pa.int64()),
            ("trace_address", pa.string()),
            ("block_hash", pa.string()),
            ("trace_type", pa.string()),
            ("gas", pa.float64()),
            ("gas_used", pa.float64()),
            ("from_address", pa.string()),
            ("value", pa.float64()),
            ("reward_type", pa.string()),
            ("input", pa.string()),
            ("output", pa.string()),
            ("call_type", pa.string()),
            ("to_address", pa.string()),
            ("block_timestamp", TS),
            ("date", pa.string()),
            ("last_modified", TS),
        ]
    ),
    "contracts": pa.schema(
        [
            ("address", pa.string()),
            ("bytecode", pa.string()),
            ("block_number", pa.int64()),
            ("block_hash", pa.string()),
            ("block_timestamp", TS),
            ("date", pa.string()),
            ("last_modified", TS),
        ]
    ),
}

DAY = dt.date(2025, 11, 1)
T0 = dt.datetime(2025, 11, 1, 0, 0, 12)


def addr(n: int) -> str:
    return "0x" + f"{n:040x}"


def h32(n: int) -> str:
    return "0x" + f"{n:064x}"


def _default(field: pa.Field) -> Any:
    t = field.type
    if pa.types.is_string(t):
        return "None"
    if pa.types.is_list(t):
        return []
    if pa.types.is_timestamp(t):
        return T0
    if pa.types.is_floating(t):
        return 0.0
    return 0


def make_table(table: str, rows: list[dict[str, Any]]) -> pa.Table:
    schema = AWS_SCHEMAS[table]
    cols: dict[str, list[Any]] = {f.name: [] for f in schema}
    for row in rows:
        unknown = set(row) - set(cols)
        assert not unknown, f"unknown columns {unknown}"
        for f in schema:
            cols[f.name].append(row.get(f.name, _default(f)))
    return pa.table(cols, schema=schema)


WriteAws = Callable[..., Path]


@pytest.fixture
def aws_root(tmp_path: Path) -> Path:
    root = tmp_path / "aws"
    root.mkdir()
    return root


@pytest.fixture
def out_root(tmp_path: Path) -> Path:
    return tmp_path / "out"


@pytest.fixture
def write_aws(aws_root: Path) -> WriteAws:
    """Write rows as an AWS-style partition: <root>/<table>/date=YYYY-MM-DD/part-N.parquet."""

    def _write(table: str, rows: list[dict[str, Any]], day: dt.date = DAY, part: int = 0) -> Path:
        d = aws_root / table / f"date={day.isoformat()}"
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"part-{part:05d}.snappy.parquet"
        pq.write_table(make_table(table, rows), path, compression="snappy")
        return path

    return _write
