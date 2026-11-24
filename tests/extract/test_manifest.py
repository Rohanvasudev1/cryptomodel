"""Manifest contents, idempotence and resume."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from cryptomodel.extract import pipeline
from cryptomodel.extract.manifest import MANIFEST_NAME, read_manifest
from cryptomodel.extract.pipeline import extract_table_day
from cryptomodel.extract.source import LocalSource

from .conftest import DAY, WriteAws, addr

PART = f"date={DAY.isoformat()}"


def contracts(n: int) -> list[dict[str, object]]:
    return [{"address": addr(i), "bytecode": "0x60"} for i in range(n)]


def test_manifest_records_snapshot_and_provenance(
    write_aws: WriteAws, aws_root: Path, out_root: Path
) -> None:
    src = write_aws("contracts", contracts(3))
    result = extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root)
    m = read_manifest(out_root / "contracts" / PART / MANIFEST_NAME)
    assert m is not None and m == result.manifest
    assert m.table == "contracts" and m.date == DAY.isoformat()
    assert m.source_rows == 3 and m.rows == 3
    assert [f.path for f in m.source_files] == [str(src)]
    assert m.source_files[0].size == src.stat().st_size
    assert m.output_bytes == (out_root / "contracts" / PART / "data.parquet").stat().st_size
    assert m.snapshot_date == dt.datetime.fromisoformat(m.extracted_at).date().isoformat()
    assert m.spec_hash and m.code_commit
    raw = json.loads((out_root / "contracts" / PART / MANIFEST_NAME).read_text())
    assert raw["snapshot_date"] == m.snapshot_date


def test_second_run_skips(write_aws: WriteAws, aws_root: Path, out_root: Path) -> None:
    write_aws("contracts", contracts(2))
    first = extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root)
    second = extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root)
    assert first.status == "written" and second.status == "skipped"
    assert second.manifest == first.manifest


def test_changed_source_is_reextracted(write_aws: WriteAws, aws_root: Path, out_root: Path) -> None:
    write_aws("contracts", contracts(2))
    extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root)
    write_aws("contracts", contracts(5))  # AWS rewrote the partition
    again = extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root)
    assert again.status == "written" and again.manifest.rows == 5


def test_missing_or_truncated_output_is_reextracted(
    write_aws: WriteAws, aws_root: Path, out_root: Path
) -> None:
    write_aws("contracts", contracts(2))
    extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root)
    data = out_root / "contracts" / PART / "data.parquet"
    data.write_bytes(data.read_bytes()[:10])
    assert extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root).status == "written"
    data.unlink()
    assert extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root).status == "written"


def test_spec_change_is_reextracted(
    write_aws: WriteAws, aws_root: Path, out_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_aws("contracts", contracts(2))
    extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root)
    monkeypatch.setattr(pipeline, "spec_hash", lambda table: "different")
    assert extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root).status == "written"


def test_crash_mid_write_leaves_no_manifest_and_resumes(
    write_aws: WriteAws, aws_root: Path, out_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_aws("contracts", contracts(2))

    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("disk full")

    monkeypatch.setattr(pipeline, "write_manifest", boom)
    with pytest.raises(RuntimeError):
        extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root)
    part = out_root / "contracts" / PART
    assert not (part / MANIFEST_NAME).exists()
    assert not list(part.glob("*.tmp"))
    monkeypatch.undo()
    assert extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root).status == "written"


def test_missing_source_partition_raises(aws_root: Path, out_root: Path) -> None:
    with pytest.raises(FileNotFoundError):
        extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root)


def test_force_rewrites(write_aws: WriteAws, aws_root: Path, out_root: Path) -> None:
    write_aws("contracts", contracts(2))
    extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root)
    r = extract_table_day(LocalSource(aws_root), "contracts", DAY, out_root, force=True)
    assert r.status == "written"
