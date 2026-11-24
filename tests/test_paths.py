from pathlib import Path

import pytest

from cryptomodel import paths


def test_data_dir_defaults_to_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(paths.DATA_DIR_ENV, raising=False)
    assert paths.data_dir() == (Path.home() / "cryptomodel-data").resolve()


def test_data_dir_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(paths.DATA_DIR_ENV, str(tmp_path / "d"))
    assert paths.data_dir() == (tmp_path / "d").resolve()
    assert paths.raw_filtered_dir() == (tmp_path / "d" / "raw_filtered").resolve()


def test_data_dir_inside_repo_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = Path(__file__).resolve().parents[1]
    monkeypatch.setenv(paths.DATA_DIR_ENV, str(repo / "data"))
    with pytest.raises(ValueError, match="outside the repository"):
        paths.data_dir()
