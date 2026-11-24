# Phase 1: AWS extraction trial

Date: 2026-11-24. Run ID in `EXPERIMENTS.md`: P1-extract-001. Code: `src/cryptomodel/extract/`, run as `uv run python -m cryptomodel.extract`.

Purpose: before the full-year run, measure what the filtered extract of AWS Public Blockchain Data (`s3://aws-public-blockchain/v1.0/eth/`) costs on this Mac (Apple M1, 8 cores, 16 GB RAM, about 280 GB free): local size, run time and memory. Then project the extraction window (2025-11-01 to 2026-10-31).

## Summary

- **The filtered year fits.** Measured output-to-raw ratios project **about 171 GB** for the year, inside the Phase 0 estimate of 115 to 180 GB. That leaves about 110 GB for derived tables.
- **Throughput is the bottleneck, and it is the network path to S3, not the code.** Reading Parquet remotely (stream mode) ran at **2.2 to 2.4 MB/s**. Downloading whole objects with parallel ranged GETs, then filtering locally (download mode), ran at **7.0 to 7.1 MB/s**, about 3x faster. Download mode is now the default.
- **Full-year time:**
  - Download mode, best setting: **about 74 hours (3.1 days)**.
  - Stream mode: **about 8 days**.
  - Neither meets the 24-hour target. Reaching it from this Mac needs about 22 MB/s sustained to us-east-2. We measured at most 16 MB/s in 15-second peaks and about 7 MB/s on average, so no setting tried gets there.
- **Memory is small.** The peak for the whole process tree is **1.7 GB** in download mode with 10 tasks at once, and 3.8 GB in stream mode with 4.
- **Precision:** AWS stores `transactions.value` (not only `traces.value`) as a double. ETH values are therefore approximate at the source; token amounts in `logs.data` are exact.

## What the extractor keeps

Every table is written to `$CRYPTOMODEL_DATA_DIR/raw_filtered/<table>/date=YYYY-MM-DD/data.parquet` (zstd level 3), with a `_manifest.json` beside it. The manifest holds the snapshot date, the source files (path, size, mtime), source and output row counts, output bytes, the filter-spec hash, the code commit, the wall time, the peak memory and the mode. A day is skipped when its manifest matches the current source listing, the spec hash and the output file size.

| Table | Rows kept | Columns kept |
|---|---|---|
| blocks | all | all except `date` and `last_modified`; hex as binary |
| transactions | all | hash, block, time, index, from, to, value, nonce, gas fields, status, created contract, type, 4-byte selector, input size. The full `input` is dropped. |
| logs | topic0 is one of 16 events: ERC-20 Transfer and Approval; Uniswap V2 PairCreated, Swap, Mint, Burn and Sync; V3 PoolCreated, Initialize, Swap, Mint, Burn and Collect; V4 Initialize, ModifyLiquidity and Swap | block, time, tx index, log index, tx hash, address, topic0 to topic3, data |
| traces | creates (with init code) and selfdestructs; internal calls that move ETH; calls that errored and carry calldata | block, time, tx index, tx hash, trace address, type, call type, from, to, value, gas, gas used, status, error, selector, input size, init code (creates only) |
| contracts | all | address, bytecode, block, block hash, time |

Notes on the filters:

- **Fixed-size binary.** Addresses are `binary(20)`, and hashes and topics are `binary(32)`.
- **Source quirks.** AWS writes nulls as the string `'None'` (all of `traces`, and `transactions.to_address`) or as `''` (`transactions.receipt_contract_address`). The extractor turns both into real nulls.
- **Value.** `value_wei_approx` is `decimal(38,0)` holding the source double's exact integer, so nothing downstream loses more precision. Values above 2^53 wei (about 0.009 ETH) are already rounded by AWS to about 16 significant digits. In a sample of 371,206 transactions, 73,304 (20%) were above 2^53. If exact ETH amounts are ever needed, they must come from another source (an RPC or BigQuery).
- **Token or pool contracts can't be identified at this stage.** So the failed-call filter keeps every failed call with calldata, not only calls to token and pool contracts. Failed calls without calldata (a plain ETH send to a reverting fallback or receive) are dropped. At the top level they still show as failed transactions. Top-level value calls are dropped because they duplicate the transaction row. Reverted children that have no error of their own are also dropped.
- **Each day is sorted on its natural key** (added after the trial, in review): blocks by number; transactions by (block_number, transaction_index); logs by (block_number, log_index); traces by (block_number, transaction_index, trace_address as a list of integers, top-level frame first); contracts by (block_number, address). AWS files are not sorted by block, and without the sort DuckDB's multithreaded scan made row order vary from run to run. Keys are unique in all 15 trial table-days except 3 contracts rows that are exact duplicates, so the output is byte-identical across runs. The sort adds under 1 s per table-day and raises one task's peak memory to 1.45 GB (logs, 2 threads, 1 GB DuckDB limit). The trial outputs on disk predate the sort; the full run re-extracts them.

## Trial: three days

The days were chosen to span the window: the start, around T1, and the test period. These runs used stream mode, 2 workers on day 1 and 4 on days 2 and 3. The outputs are identical to download mode (checked on 2026-09-15: same rows in every table).

| Day | Table | Source rows | Rows kept | Raw MB | Output MB | Stream s | Peak RSS MB |
|---|---|---|---|---|---|---|---|
| 2025-11-01 | transactions | 1,360,364 | 1,360,364 | 460 | 96.4 | 259 | 1,650 |
| | logs | 3,797,518 | 2,522,900 | 707 | 159.3 | 620 | 1,685 |
| | traces | 10,485,259 | 843,223 | 1,695 | 31.4 | 1,093 | 2,797 |
| | blocks | 7,153 | 7,153 | 6 | 3.2 | 2 | 196 |
| | contracts | 174,909 | 174,909 | 22 | 8.6 | 3 | 371 |
| 2026-03-15 | transactions | 1,777,105 | 1,777,105 | 772 | 146.9 | 894 | 1,607 |
| | logs | 5,590,415 | 4,108,487 | 1,038 | 266.3 | 570 | 1,743 |
| | traces | 13,470,762 | 1,247,810 | 2,394 | 44.2 | 1,516 | 2,870 |
| | blocks | 7,175 | 7,175 | 6 | 3.1 | 19 | 199 |
| | contracts | 185,468 | 185,468 | 23 | 9.1 | 5 | 394 |
| 2026-09-15 | transactions | 1,894,453 | 1,894,453 | 868 | 132.6 | 946 | 1,969 |
| | logs | 6,315,207 | 4,571,776 | 1,212 | 294.7 | 745 | 1,686 |
| | traces | 17,055,894 | 1,490,690 | 3,166 | 44.8 | 2,070 | 3,225 |
| | blocks | 7,170 | 7,170 | 5 | 2.9 | 17 | 199 |
| | contracts | 23,061 | 23,061 | 18 | 7.1 | 4 | 285 |

| Day | Raw GB | Output MB | Wall s (stream) | Tree peak RSS MB |
|---|---|---|---|---|
| 2025-11-01 (2 workers) | 2.89 | 299 | 1,097 | 3,594 |
| 2026-03-15 (4 workers) | 4.23 | 470 | 1,520 | 3,386 |
| 2026-09-15 (4 workers) | 5.27 | 482 | 2,075 | 3,753 |

Day 1's run lost contracts and blocks to a bug introduced mid-run (a DuckDB option set the wrong way). A resume run re-extracted only those two tables in 10 s, and skipped the three finished ones. That doubles as a real-data test of resume.

## Projecting the year

### Size

Each table's measured output-to-raw ratio, applied to that table's raw size for the year from `reports/phase0/data_sources.md`:

| Table | Raw GB (year) | Output / raw | Projected GB |
|---|---|---|---|
| logs | 400 | 0.244 | 97.4 |
| transactions | 297 | 0.179 | 53.2 |
| traces | 983 | 0.017 | 16.3 |
| contracts | 7.4 | 0.393 | 2.9 |
| blocks | 2.1 | 0.536 | 1.1 |
| **Total** | **1,865** | | **about 171** |

The simple per-day average (416 MB × 365 days) gives 152 GB. That method underweights later, busier days, so 171 GB is the figure to plan with.

**If space gets tight, tighten in this order:**

1. Drop `logs.transaction_hash`, which is 36% of the logs output, about 35 GB. It can be joined back from `transactions` on `(block_number, transaction_index)`. Do the same for `traces.transaction_hash`, which is 24% of traces, about 4 GB.
2. Drop Approval logs: 9% of kept log rows, up to about 8 GB.
3. Drop the trace init code: 17% of traces, about 3 GB.

### Time

| Mode and setting | Measured | MB/s (raw bytes ÷ wall) | Year (1,865 GB) |
|---|---|---|---|
| Stream, 2 workers (day 1) | 2.46 GB read in 1,097 s | 2.2 | about 8 days |
| Stream, 4 workers (days 2, 3) | 8.28 GB read in 3,595 s | 2.3 | about 8 days (1,585 GB read at 85%) |
| Download, 1 day, 5 tables at once, 16 connections each | 5.27 GB in 749 s | 7.0 | **about 74 h** |
| Download, 2 days at once (10 tasks), 16 connections each | 6.62 GB in 935 s | 7.1 | about 73 h |

The 2025-11 days are smaller than later days, so the year projection uses raw bytes, not day counts.

## Finding the bottleneck

1. **Projection pushdown works, but saves little.** Footer metadata shows the projected columns are 85% of each raw file (2.46 of 2.89 GB on day 1, 4.60 of 5.27 GB on 2026-09-15). The big columns are needed: `traces.input` alone is 49 to 58% of the traces bytes, and `transactions.input` is 56 to 68% of the transactions bytes. These are needed for the selector and for init code.
2. **Row filters can't be pushed into the remote read.** The logs filter is on `topics[1]`, inside a list, and every row group holds Transfers. Traces need `trace_type`, `value` and `error` together. So every projected byte is downloaded and the filter runs locally. Filtering is cheap. Once a file is local, DuckDB filters a full traces day (2.4 GB raw, 13.5M rows) in 2.1 s and logs in a few seconds. CPU is not the limit.
3. **The network path to S3 is the limit.** Measured from this Mac:

   | Test | Throughput |
   |---|---|
   | Single HTTPS GET from speed.cloudflare.com | 7.7 MB/s (this session); the manager measured 22.8 MB/s |
   | Single ranged GET from the AWS bucket | 0.7 MB/s (this session); 1.27 MB/s (manager) |
   | 8 parallel ranged GETs, 10 MB each | 2.8 MB/s total |
   | 16 parallel ranged GETs, 8 MB each | 3.9 MB/s total |
   | Download mode, 64 connections on one 2.4 GB object | 6.2 MB/s |
   | Download mode, 4 to 10 objects at once (16 connections each), interface counter | 7 to 16 MB/s in 15-second samples, 7.0 to 7.1 MB/s on average |

   Each connection to us-east-2 gets about 0.3 to 1.3 MB/s. Adding connections helps up to an aggregate of about 7 MB/s on average, which is well below what the same line gets from Cloudflare. The remote Parquet reader (pyarrow's S3 filesystem) is slower still, because it issues one request per column chunk and waits on each.
4. **Memory.**
   - **Stream mode:** about 1.7 GB per logs or transactions task and about 2.8 to 3.2 GB per traces task.
   - **Download mode with a pyarrow scanner:** a traces task peaked at 5.4 GB, because AWS row groups are about 1M rows.
   - **The fix:** reading local files with DuckDB's own `read_parquet` cut that to 0.6 to 0.9 GB per task. The tree peak was 1.7 GB with 10 tasks at once.

## Recommendation

- **Run the year in download mode**, which is the CLI default: `--mode download --workers 5 --connections 16`. Expect about 3 days.
  - **Resumable.** The run can be stopped and restarted at any time; finished days are skipped.
  - **Staging.** Raw files sit in `$CRYPTOMODEL_DATA_DIR/tmp/extract/` only while their task runs, so the most on disk at once is the files of `--workers` tasks (under 10 GB at 5 workers).
  - **Memory** stays under 2 GB.
- **To go faster:**
  - **Run the extractor in AWS us-east-2.** An EC2 instance next to the bucket gets in-region S3 bandwidth (hundreds of MB/s) at no transfer cost, so the year would take a few hours. Its output (about 171 GB) would then be copied to the Mac at the home-line rate, about 2 to 8 hours. This needs an AWS account, so it is the user's call.
  - **Read less (not built yet).** Download mode fetches whole objects. Fetching only the byte ranges of the projected column chunks, which are listed in each file's footer, would skip the 15% of bytes not used (about 11 h saved). Also dropping `traces.input` would cut the bytes read by another 35 to 40%, to about 45 h in total. The cost is losing init code and selectors on internal failed calls; top-level failed calls keep their selector in `transactions`. Dropping it is a filter-design decision for the manager.
- **The trial outputs will be redone.** The trial manifests say `code_dirty: true`, because the trial ran from uncommitted code. The spec hash now ignores SQL whitespace, which changed every table's hash although the filters are the same. So the full run re-extracts the three trial days, about 30 minutes.

## Pass or fail against the pre-registered thresholds

The thresholds were written down after seeing only the first logs result (see `EXPERIMENTS.md`, P1-extract-001):

1. **Projected size ≤ 180 GB: pass** (171 GB).
2. **Projected time ≤ 72 h: fail.** Download mode projects 74 h, just over; stream mode about 8 days. The manager's later 24-hour target is not reachable from this Mac.
3. **Peak memory ≤ 8 GB: pass** (1.7 GB in download mode, 3.8 GB in stream mode).
