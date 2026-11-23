# cryptomodel

Self-supervised foundation model over Ethereum token-launch events, for scoring rug pulls and honeypots. See `PLAN.md` and `EXPERIMENTS.md`.

## Setup (macOS, Apple Silicon)

1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. `uv sync` (creates `.venv` with Python 3.12 and all packages)
3. xgboost and lightgbm need `libomp.dylib`. Without Homebrew, copy the one torch ships:
   `cp .venv/lib/python3.12/site-packages/torch/lib/libomp.dylib ~/.local/share/uv/python/cpython-3.12.*-macos-aarch64-none/lib/`
4. Check: `uv run python -c "import torch; print(torch.backends.mps.is_available())"`
