"""Where data lives. All data is outside the repository, never in a worktree."""

from __future__ import annotations

import os
from pathlib import Path

DATA_DIR_ENV = "CRYPTOMODEL_DATA_DIR"
DEFAULT_DATA_DIR = Path("~/cryptomodel-data")


def data_dir() -> Path:
    """Root data directory: ``$CRYPTOMODEL_DATA_DIR``, else ``~/cryptomodel-data``.

    Raises ``ValueError`` if the directory is inside a git working tree, so chain data
    can never land in the repository or one of its worktrees.
    """
    raw = os.environ.get(DATA_DIR_ENV)
    path = (Path(raw) if raw else DEFAULT_DATA_DIR).expanduser().resolve()
    for parent in (path, *path.parents):
        if (parent / ".git").exists():
            raise ValueError(
                f"data directory {path} is inside the git working tree {parent}; "
                f"set {DATA_DIR_ENV} to a path outside the repository"
            )
    return path


def raw_filtered_dir() -> Path:
    """Root of the filtered AWS extract: ``<data_dir>/raw_filtered``."""
    return data_dir() / "raw_filtered"
