"""Where the AWS-layout Parquet is read from: the public S3 bucket or a local mirror."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import pyarrow.fs as pafs

from cryptomodel.extract.constants import AWS_BUCKET, AWS_PREFIX, AWS_REGION


@dataclass(frozen=True)
class SourceFile:
    path: str
    size: int
    mtime_ns: int | None


class Source:
    """A tree laid out as ``<root>/<table>/date=YYYY-MM-DD/*.parquet``."""

    def __init__(
        self,
        filesystem: pafs.FileSystem,
        root: str,
        uri: str,
        base_url: str | None = None,
        url_root: str | None = None,
    ) -> None:
        self.filesystem = filesystem
        self.root = root.rstrip("/")
        self.uri = uri
        self.base_url = base_url.rstrip("/") if base_url else None
        self.url_root = (url_root or self.root).rstrip("/")

    def url_for(self, file: SourceFile) -> str:
        """Plain HTTPS (or HTTP) URL of a listed file, for whole-object download."""
        if self.base_url is None:
            raise ValueError(f"{self.uri} has no HTTP endpoint; use stream mode")
        prefix = self.url_root + "/"
        if not file.path.startswith(prefix):
            raise ValueError(f"{file.path} is not under {prefix}")
        return f"{self.base_url}/{file.path[len(prefix) :]}"

    def list_files(self, table: str, day: dt.date) -> list[SourceFile]:
        """Parquet files of one daily partition, sorted by path.

        Raises ``FileNotFoundError`` if the partition is missing or empty.
        """
        prefix = f"{self.root}/{table}/date={day.isoformat()}"
        infos = self.filesystem.get_file_info(
            pafs.FileSelector(prefix, allow_not_found=True)
        )
        files = [
            SourceFile(i.path, int(i.size), i.mtime_ns)
            for i in infos
            if i.type == pafs.FileType.File and i.path.endswith(".parquet")
        ]
        if not files:
            raise FileNotFoundError(
                f"no parquet files under {self.uri}/{table}/date={day}"
            )
        return sorted(files, key=lambda f: f.path)


class S3Source(Source):
    """The public AWS bucket, read anonymously."""

    def __init__(self) -> None:
        fs = pafs.S3FileSystem(
            anonymous=True,
            region=AWS_REGION,
            connect_timeout=30,
            request_timeout=120,
            retry_strategy=pafs.AwsDefaultS3RetryStrategy(max_attempts=10),
        )
        super().__init__(
            fs,
            f"{AWS_BUCKET}/{AWS_PREFIX}",
            f"s3://{AWS_BUCKET}/{AWS_PREFIX}",
            base_url=f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com",
            url_root=AWS_BUCKET,
        )


class LocalSource(Source):
    """A local directory with the AWS layout (tests, or a pre-downloaded mirror).

    ``base_url``, if given, is an HTTP server that serves ``root`` (used in tests of
    download mode).
    """

    def __init__(self, root: Path, base_url: str | None = None) -> None:
        root = root.resolve()
        super().__init__(
            pafs.LocalFileSystem(), str(root), root.as_uri(), base_url=base_url
        )
