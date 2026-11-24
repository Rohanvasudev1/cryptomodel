"""The CLI end to end on local fixtures, with worker processes."""

from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

import pytest

from cryptomodel.extract.cli import date_range, main
from cryptomodel.extract.manifest import MANIFEST_NAME

from .conftest import WriteAws, addr, h32


def test_date_range_inclusive() -> None:
    assert date_range(dt.date(2025, 11, 30), dt.date(2025, 12, 2)) == [
        dt.date(2025, 11, 30),
        dt.date(2025, 12, 1),
        dt.date(2025, 12, 2),
    ]


def test_cli_runs_days_and_tables_then_resumes(
    write_aws: WriteAws,
    aws_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    data_dir = tmp_path / "data"
    monkeypatch.setenv("CRYPTOMODEL_DATA_DIR", str(data_dir))
    days = [dt.date(2025, 11, 1), dt.date(2025, 11, 2)]
    for d in days:
        write_aws("contracts", [{"address": addr(1)}], day=d)
        write_aws("blocks", [{"number": 1, "hash": h32(1)}], day=d)
    args = [
        "--start",
        "2025-11-01",
        "--end",
        "2025-11-02",
        "--tables",
        "contracts",
        "blocks",
        "--workers",
        "2",
        "--mode",
        "stream",
        "--source-root",
        str(aws_root),
    ]
    assert main(args) == 0
    for d in days:
        for t in ("contracts", "blocks"):
            assert (data_dir / "raw_filtered" / t / f"date={d}" / MANIFEST_NAME).exists()
    assert main(args) == 0
    out = capsys.readouterr().out
    assert out.count("skipped") >= 4


def test_cli_reports_failure(
    aws_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CRYPTOMODEL_DATA_DIR", str(tmp_path / "data"))
    args = ["--start", "2025-11-01", "--end", "2025-11-01", "--tables", "blocks"]
    assert main([*args, "--workers", "1", "--mode", "stream", "--source-root", str(aws_root)]) == 1


def test_module_entry_point_runs_workers(
    write_aws: WriteAws, aws_root: Path, tmp_path: Path
) -> None:
    # Through ``python -m`` with spawned workers, as the real runs use it.
    write_aws("contracts", [{"address": addr(1)}])
    env = {**os.environ, "CRYPTOMODEL_DATA_DIR": str(tmp_path / "data")}
    args = ["--start", "2025-11-01", "--end", "2025-11-01", "--tables", "contracts"]
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "cryptomodel.extract",
            *args,
            "--mode",
            "stream",
            "--source-root",
            str(aws_root),
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    assert "written" in proc.stdout
