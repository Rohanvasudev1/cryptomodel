"""Make `cryptomodel` importable before the package-setup PR adds a build backend.

Until `pyproject.toml` declares the src layout, uv does not install the package,
so fall back to putting `src/` on the path. Once the package is installed this
does nothing.
"""

import importlib.util
import sys
from pathlib import Path

if importlib.util.find_spec("cryptomodel") is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
