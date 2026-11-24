"""Download mode, against a local HTTP server with Range support (no internet)."""

from __future__ import annotations

import http.server
import re
import threading
import urllib.error
from collections.abc import Iterator
from email.message import Message
from functools import partial
from pathlib import Path

import pyarrow.fs as pafs
import pyarrow.parquet as pq
import pytest

from cryptomodel.extract import download
from cryptomodel.extract.constants import EVENT_TOPICS
from cryptomodel.extract.download import Download, download_all, split_ranges
from cryptomodel.extract.pipeline import extract_table_day
from cryptomodel.extract.source import LocalSource, S3Source, Source, SourceFile

from .conftest import DAY, WriteAws, addr, h32


class RangeHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        path = Path(self.translate_path(self.path))
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        m = re.fullmatch(r"bytes=(\d+)-(\d+)", self.headers.get("Range", ""))
        if m is None:
            self.send_response(200)
            body = data
        else:
            a, b = int(m[1]), int(m[2])
            body = data[a : b + 1]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {a}-{b}/{len(data)}")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture
def http_root(aws_root: Path) -> Iterator[str]:
    handler = partial(RangeHandler, directory=str(aws_root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_split_ranges_cover_exactly() -> None:
    assert split_ranges(10, 4) == [(0, 3), (4, 7), (8, 9)]
    assert split_ranges(8, 4) == [(0, 3), (4, 7)]
    assert split_ranges(0, 4) == []


def test_download_all_reassembles_ranges(
    aws_root: Path, http_root: str, tmp_path: Path
) -> None:
    payload = bytes(range(256)) * 41  # 10,496 bytes, many uneven ranges
    (aws_root / "blob.bin").write_bytes(payload)
    dest = tmp_path / "dl" / "blob.bin"
    n = download_all(
        [Download(f"{http_root}/blob.bin", len(payload), dest)], 8, chunk=333
    )
    assert n == len(payload)
    assert dest.read_bytes() == payload


def test_download_failure_removes_partial_file(http_root: str, tmp_path: Path) -> None:
    dest = tmp_path / "missing.bin"
    with pytest.raises(OSError):
        download_all([Download(f"{http_root}/missing.bin", 100, dest)], 2)
    assert not dest.exists()


def test_download_mode_matches_stream_mode(
    write_aws: WriteAws, aws_root: Path, http_root: str, tmp_path: Path
) -> None:
    transfer = EVENT_TOPICS["ERC20_TRANSFER"].topic0
    rows = [
        {"address": addr(i), "topics": [transfer, h32(i)], "data": "0x" + f"{i:064x}"}
        for i in range(50)
    ]
    write_aws("logs", rows, part=0)
    write_aws("logs", rows[:7], part=1)
    source = LocalSource(aws_root, base_url=http_root)
    staging = tmp_path / "staging"

    streamed = extract_table_day(source, "logs", DAY, tmp_path / "a")
    downloaded = extract_table_day(
        source, "logs", DAY, tmp_path / "b", staging_dir=staging
    )

    rel = Path("logs") / f"date={DAY.isoformat()}" / "data.parquet"
    assert pq.read_table(tmp_path / "a" / rel).equals(
        pq.read_table(tmp_path / "b" / rel)
    )
    assert downloaded.manifest.source_files == streamed.manifest.source_files
    assert downloaded.manifest.extra["mode"] == "download"
    assert streamed.manifest.extra["mode"] == "stream"
    assert downloaded.manifest.extra["download_bytes"] == sum(
        f.size for f in downloaded.manifest.source_files
    )
    assert not any(staging.rglob("*.parquet"))  # raw files deleted after the write


def test_s3_source_urls() -> None:
    f = SourceFile(
        "aws-public-blockchain/v1.0/eth/logs/date=2025-11-01/p.parquet", 1, None
    )
    assert S3Source().url_for(f) == (
        "https://aws-public-blockchain.s3.us-east-2.amazonaws.com/v1.0/eth/logs/date=2025-11-01/p.parquet"
    )


@pytest.mark.parametrize(
    "table", ["logs", "transactions", "traces", "blocks", "contracts"]
)
def test_remote_reader_matches_local_reader(
    table: str, write_aws: WriteAws, aws_root: Path, tmp_path: Path
) -> None:
    # A non-LocalFileSystem forces the remote (pyarrow scanner) path used against S3.
    transfer = EVENT_TOPICS["ERC20_TRANSFER"].topic0
    rows: dict[str, list[dict[str, object]]] = {
        "logs": [
            {"topics": [transfer, h32(i)], "data": "0x" + f"{i:064x}"} for i in range(9)
        ]
        + [{"topics": [h32(5)]}],
        "transactions": [
            {"hash": h32(i), "input": "0xa9059cbb", "value": 1e18} for i in range(5)
        ],
        "traces": [
            {"trace_type": "call", "trace_address": "0", "value": 2e18},
            {"trace_type": "create", "trace_address": "None", "input": "0x6080"},
            {
                "trace_type": "call",
                "trace_address": "1",
                "error": "Reverted",
                "input": "0x70a08231",
            },
            {"trace_type": "call", "trace_address": "2"},
        ],
        "blocks": [{"number": 1, "hash": h32(1), "logs_bloom": "0x" + "00" * 256}],
        "contracts": [{"address": addr(1), "bytecode": "0x60"}],
    }
    write_aws(table, rows[table])
    local = LocalSource(aws_root)
    remote = Source(
        pafs.SubTreeFileSystem("/", pafs.LocalFileSystem()),
        str(aws_root).lstrip("/"),
        "test://remote",
    )
    a = extract_table_day(local, table, DAY, tmp_path / "local")
    b = extract_table_day(remote, table, DAY, tmp_path / "remote")
    rel = Path(table) / f"date={DAY.isoformat()}" / "data.parquet"
    assert a.manifest.rows == b.manifest.rows > 0
    assert a.manifest.source_rows == b.manifest.source_rows
    assert pq.read_table(tmp_path / "local" / rel).equals(
        pq.read_table(tmp_path / "remote" / rel)
    )


def test_server_error_is_retried(
    aws_root: Path, http_root: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = b"x" * 1000
    (aws_root / "flaky.bin").write_bytes(payload)
    calls = {"n": 0}
    real_get = download._get

    def flaky_get(url: str, start: int, end: int) -> Iterator[bytes]:
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(url, 503, "slow down", Message(), None)
        if calls["n"] == 2:
            yield payload[start : start + 10]  # short read, then the connection drops
            return
        yield from real_get(url, start, end)

    monkeypatch.setattr(download, "_get", flaky_get)
    monkeypatch.setattr(download.time, "sleep", lambda s: None)
    dest = tmp_path / "flaky.bin"
    assert download_all([Download(f"{http_root}/flaky.bin", 1000, dest)], 1) == 1000
    assert dest.read_bytes() == payload and calls["n"] == 3


def test_client_error_is_not_retried(
    http_root: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(download.time, "sleep", sleeps.append)
    with pytest.raises(urllib.error.HTTPError):
        download_all([Download(f"{http_root}/nope.bin", 10, tmp_path / "n.bin")], 1)
    assert sleeps == []
