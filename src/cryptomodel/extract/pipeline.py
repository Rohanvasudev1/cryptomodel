"""Extract one (table, day): stream the source through DuckDB into zstd Parquet."""

from __future__ import annotations

import datetime as dt
import functools
import resource
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import duckdb
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.fs as pafs
import pyarrow.parquet as pq

from cryptomodel.extract.download import Download, download_all
from cryptomodel.extract.manifest import (
    DATA_NAME,
    MANIFEST_NAME,
    Manifest,
    manifest_matches,
    read_manifest,
    write_manifest,
)
from cryptomodel.extract.source import Source
from cryptomodel.extract.tables import MACROS, TABLE_SPECS, TableSpec, spec_hash

ZSTD_LEVEL = 3
SCAN_BATCH_ROWS = 32_768
ROW_GROUP_ROWS = 512 * 1024
ROW_GROUP_BYTES = 128 * 1024 * 1024


@dataclass(frozen=True)
class ExtractResult:
    status: Literal["written", "skipped"]
    manifest: Manifest


@dataclass(frozen=True)
class Limits:
    """Per-task resource limits. Total memory is roughly workers x one task's peak."""

    duckdb_threads: int = 2
    duckdb_memory: str = "1GB"


def part_dir(out_root: Path, table: str, day: dt.date) -> Path:
    return out_root / table / f"date={day.isoformat()}"


def extract_table_day(
    source: Source,
    table: str,
    day: dt.date,
    out_root: Path,
    *,
    force: bool = False,
    limits: Limits | None = None,
    staging_dir: Path | None = None,
    connections: int = 16,
) -> ExtractResult:
    """Extract one table for one day, or skip it if a matching manifest exists.

    With ``staging_dir`` (download mode), the day's source files are first downloaded
    whole into ``staging_dir/<table>/date=YYYY-MM-DD/`` over ``connections`` parallel
    ranged GETs, filtered locally, then deleted. Without it (stream mode), the source
    is read remotely column chunk by column chunk. Both write identical output.

    The data file is written to a temp name and renamed; the manifest is written last.
    A crash at any point leaves either no manifest (re-extracted next run) or a
    complete, matching one.
    """
    limits = limits or Limits()
    spec = TABLE_SPECS[table]
    files = source.list_files(table, day)
    current_hash = spec_hash(table)
    pdir = part_dir(out_root, table, day)
    manifest_path = pdir / MANIFEST_NAME

    if not force:
        old = read_manifest(manifest_path)
        if old is not None and manifest_matches(old, files, current_hash, pdir):
            return ExtractResult("skipped", old)

    started = time.monotonic()
    snapshot = dt.datetime.now(dt.UTC)
    pdir.mkdir(parents=True, exist_ok=True)
    manifest_path.unlink(missing_ok=True)
    data_path = pdir / DATA_NAME
    tmp_path = pdir / (DATA_NAME + ".tmp")
    stage = staging_dir / table / f"date={day.isoformat()}" if staging_dir else None
    extra: dict[str, Any] = {"mode": "download" if stage else "stream"}
    try:
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)
            items = [
                Download(source.url_for(f), f.size, stage / Path(f.path).name)
                for f in files
            ]
            t0 = time.monotonic()
            extra["download_bytes"] = download_all(items, connections)
            extra["download_seconds"] = round(time.monotonic() - t0, 2)
            extra["connections"] = connections
            local: list[str] | None = [str(i.dest) for i in items]
        elif isinstance(source.filesystem, pafs.LocalFileSystem):
            local = [f.path for f in files]
        else:
            local = None
        if local is not None:
            source_rows = sum(pq.read_metadata(p).num_rows for p in local)
            rows = _run(
                spec, tmp_path, limits, lambda con: _register_local(con, spec, local)
            )
        else:
            dataset = ds.dataset(
                [f.path for f in files], filesystem=source.filesystem, format="parquet"
            )
            source_rows = dataset.count_rows()
            rows = _run(
                spec, tmp_path, limits, lambda con: _register_remote(con, spec, dataset)
            )
        tmp_path.replace(data_path)
        commit, dirty = code_version()
        manifest = Manifest(
            table=table,
            date=day.isoformat(),
            snapshot_date=snapshot.date().isoformat(),
            extracted_at=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            source_uri=f"{source.uri}/{table}/date={day.isoformat()}",
            source_files=files,
            source_rows=source_rows,
            rows=rows,
            output_file=DATA_NAME,
            output_bytes=data_path.stat().st_size,
            spec_hash=current_hash,
            code_commit=commit,
            code_dirty=dirty,
            wall_seconds=round(time.monotonic() - started, 2),
            peak_rss_bytes=peak_rss_bytes(),
            extra=extra,
        )
        write_manifest(manifest_path, manifest)
    finally:
        tmp_path.unlink(missing_ok=True)
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)
    return ExtractResult("written", manifest)


def _register_local(
    con: duckdb.DuckDBPyConnection, spec: TableSpec, paths: list[str]
) -> None:
    """Local files: DuckDB's own Parquet reader streams them in small vectors (about
    0.6 GB peak on a traces day, against 3 to 5 GB through a pyarrow scanner, whose
    memory grows with AWS's very large row groups)."""
    cols = ", ".join(spec.source_columns)
    files = ", ".join("'" + p.replace("'", "''") + "'" for p in paths)
    con.execute(f"CREATE VIEW src AS SELECT {cols} FROM read_parquet([{files}])")


def _register_remote(
    con: duckdb.DuckDBPyConnection, spec: TableSpec, dataset: ds.Dataset
) -> None:
    """Remote files: a pyarrow scanner reads only the projected column chunks."""
    scanner = dataset.scanner(
        columns=list(spec.source_columns),
        batch_size=SCAN_BATCH_ROWS,
        batch_readahead=2,
        fragment_readahead=1,
        use_threads=True,
    )
    con.register("src", scanner.to_reader())


def _run(
    spec: TableSpec,
    out_path: Path,
    limits: Limits,
    register_src: Callable[[duckdb.DuckDBPyConnection], None],
) -> int:
    """Run the spec's SQL over the ``src`` view batch by batch; return rows written.

    The SQL sorts the day, which spills to a temp directory beside the output once it
    passes the memory limit (never DuckDB's default ``.tmp`` in the working directory,
    which could be the repo).
    """
    spill = out_path.parent / "duckdb_tmp"
    con = duckdb.connect(
        config={
            "threads": limits.duckdb_threads,
            "memory_limit": limits.duckdb_memory,
            "preserve_insertion_order": True,
            "temp_directory": str(spill),
        }
    )
    rows = 0
    try:
        con.execute("SET enable_progress_bar = false")
        con.execute(MACROS)
        register_src(con)
        reader = con.sql(spec.sql).to_arrow_reader(SCAN_BATCH_ROWS)
        with pq.ParquetWriter(
            out_path,
            spec.schema,
            compression="zstd",
            compression_level=ZSTD_LEVEL,
            write_statistics=True,
        ) as writer:
            buf: list[pa.RecordBatch] = []
            buf_rows = buf_bytes = 0
            for batch in reader:
                if batch.num_rows == 0:
                    continue
                buf.append(batch)
                buf_rows += batch.num_rows
                buf_bytes += batch.nbytes
                if buf_rows >= ROW_GROUP_ROWS or buf_bytes >= ROW_GROUP_BYTES:
                    rows += _flush(writer, buf, spec.schema)
                    buf, buf_rows, buf_bytes = [], 0, 0
            if buf:
                rows += _flush(writer, buf, spec.schema)
    finally:
        con.close()
        shutil.rmtree(spill, ignore_errors=True)
    return rows


def _flush(
    writer: pq.ParquetWriter, batches: list[pa.RecordBatch], schema: pa.Schema
) -> int:
    table = pa.Table.from_batches(batches)
    table = table.rename_columns(schema.names).cast(schema)
    writer.write_table(table, row_group_size=table.num_rows)
    return int(table.num_rows)


def peak_rss_bytes() -> int:
    """Peak resident memory of this process.

    ``ru_maxrss`` is in bytes on macOS and in KiB on Linux.
    """
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == "darwin" else peak * 1024)


@functools.cache
def code_version() -> tuple[str, bool]:
    """(commit, dirty) of the repository this package was imported from."""
    here = Path(__file__).resolve().parent
    try:
        commit = subprocess.run(
            ["git", "-C", str(here), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(here), "status", "--porcelain", "--untracked-files=no"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return "unknown", False
    return commit, bool(status.strip())
