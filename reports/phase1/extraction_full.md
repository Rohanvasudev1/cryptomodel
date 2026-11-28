# Phase 1: full-year AWS extraction

Run ID in `EXPERIMENTS.md`: P1-extract-full-001. Dates: 2026-11-24 21:20 UTC to 2026-11-28 12:03 UTC. Window: 2025-11-01 to 2026-10-31, all five tables.

**How it was run:**

- **Command:** `uv run python -m cryptomodel.extract` with the CLI defaults (download mode, 5 workers, 16 connections, DuckDB 1 GB per task), under `caffeinate -i`, with nohup and logs in `$CRYPTOMODEL_DATA_DIR/logs/`.
- **Code:** run from a clean detached checkout outside the repo, so every manifest records `code_dirty: false`.
  - Commit cb9a351 until a blocking bug was found in the second leg (see "Failures and retries").
  - The fix, commit 0814ce1, for the rest of the run.
- **Machine:** Mac, Apple M1, 8 cores, 16 GB RAM, home internet, reading from AWS us-east-2.

## Summary

- **Complete.** All 1,825 partitions (365 days × 5 tables) have a manifest whose output file exists with the recorded size. The Parquet footer row count equals the manifest's, the spec hash is accepted, `code_dirty` is false, and rows and source rows are above 0.
- **120.8 GB on disk** (manifest bytes; `du` shows 118 GiB), from 1,690 GB of source.
  - That is under the trial's 171 GB projection, because sorted output compresses logs better.
  - About 143 GiB of disk is still free.
- **Time: 86.5 h of run time at 5.4 MB/s on average.** Both miss the pre-registered thresholds (81 h and 6.3 MB/s). Two things account for the miss:
  - About 27 hours on 2026-11-25, when the network path to S3 ran at 1 to 3 MB/s.
  - A leg stopped after 12 h to fix a bug.
  - With the path back to normal, the main leg (1,462 GB in 59.4 h) ran at **6.8 MB/s**, the trial's rate.
- **Memory: 2.42 GB peak** for the whole process tree, sampled every 30 s. The highest single task was 2.40 GB.
- **One code fix was needed.** Some failed internal calls carry a value near 2^256 wei, which doesn't fit `decimal(38, 0)`, so those traces days could not be extracted. They now get a null value (98 rows over 46 days). It was fixed test-first in commit 0814ce1.

## Pass or fail against the pre-registered thresholds

The thresholds were committed in cb9a351 before the run started.

| # | Threshold | Result | Outcome |
|---|---|---|---|
| 1 | All 1,825 partitions complete and valid | 1,825 of 1,825; 0 problems | **Pass**, with one deviation (below) |
| 2 | Size ≤ 180 GB | 120.8 GB | **Pass** |
| 3 | Run time ≤ 81 h | 86.5 h | **Fail** |
| 4 | Average throughput ≥ 6.3 MB/s | 5.42 MB/s | **Fail** |
| 5 | Tree peak RSS ≤ 4 GB | 2.42 GB | **Pass** |

**The deviation on (1).** The threshold said "spec hash equal to the current spec". 55 traces partitions were written by cb9a351 and carry the earlier traces hash (`fae09a9ce8db1f56`); the current one is `830a72d2f3da613f`.

- They are accepted through `PRIOR_SPEC_HASHES`. The only difference between the two specs is `CAST` versus `TRY_CAST` on `value`, and a test pins that.
- Wherever `CAST` succeeded the output is identical, and `CAST` wrote nothing where it failed.
- Re-extracting those 55 partitions would have re-downloaded about 130 GB of traces for byte-identical output.
- All other partitions carry the current hash.

## Time and throughput

Throughput below is source bytes of partitions written ÷ wall time of the leg. It excludes bytes downloaded for tasks that later failed or were killed.

| Leg | Range | Commit | Wall | Partitions written | Source GB | MB/s |
|---|---|---|---|---|---|---|
| nov | 2025-11-01 to 11-30 | cb9a351 | 13.8 h | 148 | 101.4 | 2.04 |
| nov-retry | same, skips finished | cb9a351 | 0.9 h | 2 | 3.4 | 1.09 |
| rest | 2025-12-01 to 2026-10-31 | cb9a351 | 12.1 h (stopped for the fix) | 152 | 120.4 | 2.78 |
| rest2 | same, skips finished | 0814ce1 | 59.4 h | 1,520 | 1,461.9 | **6.84** |
| oomretry | 3 transactions days, 1 worker, 3 GB DuckDB | 0814ce1 | 0.5 h | 3 | 2.6 | 1.54 |
| **Total** | | | **86.5 h** (311,562 s) | **1,825** | **1,689.6** | **5.42** |

**The slow period, from 2026-11-25 00:00 to about 12:00 UTC:**

- Hourly throughput fell from 4 to 8.6 MB/s to 0 to 1.6 MB/s and stayed there.
- The Mac did not sleep and recorded no thermal events (`pmset` log).
- A single ranged GET to the bucket ran at 0.59 MB/s, as in the trial.
- Cloudflare on the same line gave only 6.3 MB/s, against 22.8 MB/s when the manager measured it before the trial.
- From 2026-11-26 on, every 12-hour window ran at 6.5 to 6.8 MB/s.
- So the limit is the network path, and it varies by day. The extractor is not the limit.

**The two retry legs are slow for another reason.** They run 1 to 2 large tasks, while 5 at once are needed to approach 7 MB/s.

**Source size.** The year's source is 1,690 GB. Phase 0 estimated 1,865 GB, and the trial used that for its 74 h projection. At the trial's 7 MB/s the measured source would have taken 67 h.

## Size on disk per table

| Table | Rows kept | Source rows | Output GB | Source GB | Output / source |
|---|---|---|---|---|---|
| blocks | 2,615,422 | 2,615,422 | 1.11 | 2.08 | 0.53 |
| contracts | 24,771,813 | 24,771,813 | 2.26 | 7.38 | 0.31 |
| logs | 1,559,167,075 | 2,192,460,211 | 51.23 | 400.08 | 0.128 |
| traces | 463,323,638 | 5,588,859,252 | 14.97 | 983.33 | 0.015 |
| transactions | 756,124,166 | 756,124,166 | 51.26 | 296.75 | 0.173 |
| **Total** | | | **120.82** | **1,689.62** | 0.072 |

Blocks are contiguous: 2,615,422 distinct block numbers spanning exactly 2,615,422 blocks. No block is missing or duplicated.

## Rows per table per month

Rows kept, in millions. Blocks and contracts are in thousands.

| Month | blocks (k) | contracts (k) | logs (M) | traces (M) | transactions (M) |
|---|---|---|---|---|---|
| 2025-11 | 214.2 | 2,747.6 | 95.0 | 25.3 | 45.7 |
| 2025-12 | 221.1 | 4,296.4 | 165.2 | 30.4 | 51.5 |
| 2026-01 | 222.2 | 2,719.9 | 122.2 | 37.9 | 70.0 |
| 2026-02 | 200.6 | 2,716.7 | 118.8 | 35.9 | 61.9 |
| 2026-03 | 222.2 | 2,285.6 | 132.9 | 40.8 | 68.5 |
| 2026-04 | 215.3 | 851.9 | 133.5 | 43.1 | 72.8 |
| 2026-05 | 222.4 | 683.9 | 128.7 | 40.0 | 67.5 |
| 2026-06 | 215.1 | 1,320.8 | 140.6 | 36.3 | 63.5 |
| 2026-07 | 222.4 | 1,990.0 | 123.7 | 44.3 | 72.4 |
| 2026-08 | 222.4 | 1,933.5 | 120.0 | 49.1 | 70.1 |
| 2026-09 | 215.0 | 974.2 | 126.0 | 48.6 | 56.9 |
| 2026-10 | 222.5 | 2,251.3 | 152.5 | 31.5 | 55.4 |

Source rows are kept in full for blocks, contracts and transactions. For logs, 71% of source rows are kept (the 16 events); for traces, 8.3%.

## Failures and retries

Every failure was rerun with the same command (resume skips finished partitions), and every rerun succeeded.

| Leg | Partition | Error | Fix |
|---|---|---|---|
| nov | 2025-11-27 logs, traces | `TimeoutError: The read operation timed out` (S3) | Rerun (nov-retry) |
| rest | 7 partitions in 2025-12-01 to 12-05 (logs and traces) | Same S3 timeout | Rerun (rest2) |
| rest | 2025-12-17, 12-19, 12-26, 12-30 traces | `ConversionException`: value about 1.16e77 (2^256) does not fit `DECIMAL(38,0)` | Code fix 0814ce1, then rerun (rest2) |
| rest2 | 2026-05-31, 06-09, 06-19 transactions | `OutOfMemoryException`: the 1 GB DuckDB limit ran out during the sort | Rerun with `--duckdb-memory 3GB --workers 1` (no code change; peak 1.83 GB) |

- **Stopping the rest leg** (SIGTERM) also killed up to 5 in-flight tasks. They wrote no manifest and were redone in rest2. The staging directory was cleared before the restart and is empty at the end.
- **The value fix (commit 0814ce1).**
  - Trace values of 10^38 wei or more now become null through `TRY_CAST`; every other value is unchanged.
  - 98 trace rows over 46 days have a null value. Every one is a failed call (`error` is set).
  - `PRIOR_SPEC_HASHES` lets the skip check accept the earlier traces hash, for the reason given under threshold (1).
  - Tests: `test_traces_value_beyond_decimal38_becomes_null`, `test_manifest_with_a_prior_equivalent_spec_hash_is_skipped` and `test_traces_prior_hash_differs_only_by_try_cast`.
- **Transactions memory.** Busier days need more than 1 GB of DuckDB memory for the sorted write. A future default of 2 GB with 5 workers would still stay under about 4 GB for the whole tree, judging by the peaks here.

## Days with anomalous counts

The pre-registered rule flags a day when its kept rows fall below 50% or above 200% of that table's median for the month. It flagged 163 table-days.

**Contracts: 157 days.**

- Daily contract deployments are heavy-tailed, from 6k to over 400k a day.
- Rows equal source rows on every day, so these are real deployment bursts, not filter faults.
- The 50% to 200% rule doesn't suit this table.

**Logs: 4 days.**

- **2025-12-07 (10.25M) and 2025-12-08 (9.15M), against a median of 4.24M.**
  - Two contracts emit about 3.6M to 4.1M ERC-20 Transfers each on each of these days: `0x609e0f0cb16e53878ba5e959a22fc7fcd81b124a`, and `0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852` (the Uniswap V2 USDT/WETH pair address).
  - This looks like a spam or address-poisoning burst. The source holds the rows.
- **2026-04-04 (8.81M) and 2026-04-05 (8.79M), against a median of 4.19M.**
  - `0x201c17cd5f3211c0b8f5f1e222b3f89898bc41d3` emits about 3.0M logs a day.
  - WETH emits about 1.2M.

**Traces: 2 days.**

- **2025-12-07 (0.52M, against a median of 1.05M):** the same day as the logs burst.
- **2026-08-08 (0.80M, against a median of 1.67M).**
  - All 7,148 blocks are present, and source rows (14.7M) are normal.
  - Internal value-moving calls fell to 0.55M (1.6M on neighbouring days), while creates and selfdestructs rose to 143k (about 49k).
  - So activity shifted that day. It is not missing data.

Blocks and transactions had no flagged day. Blocks run 6,765 to 7,177 a day.

## Where things are

- **Data:** `$CRYPTOMODEL_DATA_DIR/raw_filtered/<table>/date=YYYY-MM-DD/{data.parquet,_manifest.json}`.
- **Logs** in `$CRYPTOMODEL_DATA_DIR/logs/`:
  - `extract-<leg>.log` and `runs.log` for the run itself;
  - `mem-<leg>.log` for the 30-second tree RSS and disk samples;
  - `check-full.txt` and `check-full.json` for the completeness check.
- **Scripts:** the completeness checker and the leg runner are in `~/cryptomodel-runs/`, outside the repo.
