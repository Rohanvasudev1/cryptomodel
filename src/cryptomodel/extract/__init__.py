"""Stream AWS Public Blockchain Data (Ethereum) into a filtered local Parquet copy.

One task is one (table, day): list the day's AWS partition, project and filter it in
DuckDB, write
``$CRYPTOMODEL_DATA_DIR/raw_filtered/<table>/date=YYYY-MM-DD/data.parquet`` (zstd),
then a ``_manifest.json`` beside it. A day whose manifest matches the current
source listing, filter spec and output file is skipped.
"""
