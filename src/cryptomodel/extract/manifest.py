"""The sidecar manifest written next to each extracted (table, day).

It records the snapshot date the PLAN requires for every stored table, plus enough
provenance to decide whether the day can be skipped on a re-run.
"""

from __future__ import annotations

import json
from collections.abc import Collection
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from cryptomodel.extract.source import SourceFile

MANIFEST_NAME = "_manifest.json"
DATA_NAME = "data.parquet"


@dataclass(frozen=True)
class Manifest:
    table: str
    date: str  # the AWS partition date, YYYY-MM-DD
    snapshot_date: str  # UTC date the source was read, YYYY-MM-DD
    extracted_at: str  # UTC ISO timestamp the write finished
    source_uri: str
    source_files: list[SourceFile]
    source_rows: int
    rows: int
    output_file: str
    output_bytes: int
    spec_hash: str
    code_commit: str
    code_dirty: bool
    wall_seconds: float
    peak_rss_bytes: int
    extra: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Manifest:
        d = dict(d)
        d["source_files"] = [SourceFile(**f) for f in d["source_files"]]
        return cls(**d)


def read_manifest(path: Path) -> Manifest | None:
    """The manifest at ``path``, or None if it is missing or unreadable."""
    try:
        return Manifest.from_dict(json.loads(path.read_text()))
    except (OSError, ValueError, TypeError, KeyError):
        return None


def write_manifest(path: Path, manifest: Manifest) -> None:
    """Write atomically: a reader sees the old manifest, no manifest, or the new one."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(manifest.to_json())
    tmp.replace(path)


def manifest_matches(
    manifest: Manifest,
    source_files: list[SourceFile],
    spec_hashes: Collection[str],
    part_dir: Path,
) -> bool:
    """True if the recorded extract is still valid for this source listing and one
    of the accepted spec hashes."""
    data = part_dir / manifest.output_file
    return (
        manifest.spec_hash in spec_hashes
        and manifest.source_files == source_files
        and data.is_file()
        and data.stat().st_size == manifest.output_bytes
    )
