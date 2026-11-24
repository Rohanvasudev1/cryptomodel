# cryptomodel

Self-supervised foundation model over Ethereum token-launch events. Read `PLAN.md` (fixed decisions, decision log, phases) and `GLOSSARY.md` before changing anything.

## Commands

- Tests: `uv run pytest` (unit tests use no network)
- Network tests too: `CRYPTOMODEL_NET_TESTS=1 uv run pytest`
- Typecheck: `uv run mypy src` (strict)
- Lint and format: `uv run ruff check .` and `uv run ruff format .`
- Extract AWS data: `uv run python -m cryptomodel.extract --start 2025-11-01 --end 2025-11-03 [--tables ...] [--workers N]`

The code is a src-layout package in `src/cryptomodel/`; tests mirror it in `tests/`. Add dependencies with `uv add` (or `uv add --dev`).

## Data directory

- All data lives outside the repo, under `$CRYPTOMODEL_DATA_DIR` (default `~/cryptomodel-data`). Get the path from `cryptomodel.paths.data_dir()`, which refuses any path inside a git working tree.
- Never write chain data or derived tables into the repo or a worktree, and never commit them.
- Every written table records its snapshot date. The extractor writes a `_manifest.json` beside each `date=YYYY-MM-DD/` partition with the source files, row counts, bytes, extraction time and code commit.
