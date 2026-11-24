"""Download whole source objects with many parallel ranged HTTPS GETs.

Remote Parquet readers (pyarrow S3, DuckDB httpfs) issue one request per column chunk
and wait on each, so they are latency-bound: about 2.4 MB/s from this Mac to us-east-2.
Large ranges over many connections at once go much faster, so the default extraction
mode downloads each day's files to a staging directory, filters them locally and
deletes them.
"""

from __future__ import annotations

import os
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

CHUNK_BYTES = 32 * 1024 * 1024
READ_BYTES = 1024 * 1024
RETRIES = 6


@dataclass(frozen=True)
class Download:
    url: str
    size: int
    dest: Path


def split_ranges(size: int, chunk: int = CHUNK_BYTES) -> list[tuple[int, int]]:
    """Inclusive byte ranges covering ``size`` bytes, each at most ``chunk`` long."""
    return [(start, min(start + chunk, size) - 1) for start in range(0, size, chunk)]


def download_all(
    items: list[Download], connections: int, chunk: int = CHUNK_BYTES
) -> int:
    """Download every item, ``connections`` ranges at a time. Returns bytes fetched.

    Each destination is preallocated and filled in place, so ranges can land in any
    order; every range checks it received exactly its length. On the first range
    that fails for good, queued ranges are cancelled and all destinations removed.
    """
    jobs: list[tuple[Download, int, int]] = []
    for item in items:
        item.dest.parent.mkdir(parents=True, exist_ok=True)
        with item.dest.open("wb") as f:
            f.truncate(item.size)
        jobs.extend((item, a, b) for a, b in split_ranges(item.size, chunk))
    pool = ThreadPoolExecutor(max_workers=connections)
    try:
        futures = [pool.submit(_fetch_range, *job) for job in jobs]
        fetched = sum(f.result() for f in futures)
    except BaseException:
        pool.shutdown(wait=True, cancel_futures=True)
        for item in items:
            item.dest.unlink(missing_ok=True)
        raise
    pool.shutdown()
    return fetched


def _fetch_range(item: Download, start: int, end: int) -> int:
    want = end - start + 1
    for attempt in range(RETRIES):
        try:
            got = 0
            fd = os.open(item.dest, os.O_WRONLY)
            try:
                for block in _get(item.url, start, end):
                    os.pwrite(fd, block, start + got)
                    got += len(block)
            finally:
                os.close(fd)
            if got != want:
                raise OSError(f"short read {got} of {want} bytes")
            return got
        except (OSError, urllib.error.URLError) as e:  # HTTPError is a URLError
            client_error = isinstance(e, urllib.error.HTTPError) and e.code < 500
            if client_error or attempt == RETRIES - 1:  # a 4xx will not get better
                raise
            time.sleep(min(2**attempt, 30))
    raise AssertionError("unreachable")


def _get(url: str, start: int, end: int) -> Iterator[bytes]:
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        if resp.status != 206 and not (start == 0 and resp.status == 200):
            raise OSError(f"HTTP {resp.status} for range {start}-{end} of {url}")
        while block := resp.read(READ_BYTES):
            yield block
