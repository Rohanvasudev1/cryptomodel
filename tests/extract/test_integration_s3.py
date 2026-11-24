"""Reads one real AWS partition. Skipped unless CRYPTOMODEL_NET_TESTS=1."""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from cryptomodel.extract.pipeline import extract_table_day
from cryptomodel.extract.source import S3Source

pytestmark = [
    pytest.mark.net,
    pytest.mark.skipif(
        os.environ.get("CRYPTOMODEL_NET_TESTS") != "1",
        reason="set CRYPTOMODEL_NET_TESTS=1",
    ),
]


def test_blocks_one_real_day(tmp_path: Path) -> None:
    day = dt.date(2025, 11, 1)
    result = extract_table_day(S3Source(), "blocks", day, tmp_path)
    assert result.status == "written"
    m = result.manifest
    assert 6_500 < m.rows < 7_300 and m.rows == m.source_rows
    out = pq.read_table(tmp_path / "blocks" / f"date={day}" / "data.parquet")
    assert out.schema.field("hash").type == pa.binary(32)
    numbers = out.column("number").to_pylist()
    assert len(set(numbers)) == len(numbers)
