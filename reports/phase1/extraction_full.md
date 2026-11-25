# Phase 1: full-year AWS extraction

Run ID in `EXPERIMENTS.md`: P1-extract-full-001. Code: commit cb9a351, run from a clean detached checkout so every manifest records it with `code_dirty: false`. Command: `uv run python -m cryptomodel.extract` with the defaults (download mode, 5 workers, 16 connections), under `caffeinate -i`.

**Status: in progress.** November 2025 is complete and verified. December 2025 to October 2026 is running. This file becomes the full report when the run finishes.

## November 2025 (ready for Phase 1.5)

Output is under `$CRYPTOMODEL_DATA_DIR/raw_filtered/<table>/date=2025-11-DD/`.

**Completeness:** all 150 partitions (30 days × 5 tables) pass every check:

- the manifest is present;
- the output file exists with the recorded size;
- the Parquet footer row count equals the manifest's row count;
- the spec hash is current;
- `code_dirty` is false and the commit is cb9a351;
- `rows` and `source_rows` are both above 0.

| Table | Rows kept | Source rows | Rows per day (min / median / max) | Output GB | Source GB |
|---|---|---|---|---|---|
| blocks | 214,154 | 214,154 | 7,098 / 7,142 / 7,162 | 0.10 | 0.18 |
| contracts | 2,747,550 | 2,747,550 | 6,383 / 37,998 / 444,544 | 0.16 | 0.50 |
| logs | 94,989,318 | 134,289,077 | 2.52M / 3.04M / 4.17M | 3.17 | 24.72 |
| traces | 25,329,578 | 367,025,254 | 0.69M / 0.79M / 1.31M | 0.93 | 61.94 |
| transactions | 45,672,422 | 45,672,422 | 1.27M / 1.52M / 1.89M | 3.22 | 17.42 |
| **Total** | | | | **7.57** | **104.76** |

- **Counts look plausible.** Blocks are about 7,140 a day, close to the 7,200 maximum for 12-second slots. Logs, traces and transactions all stay within a factor of 1.7 of their monthly median.
- **Contracts are the exception: 21 of 30 days are flagged.** They fall outside 50% to 200% of the month median (6k to 445k a day). The source holds the same counts (`rows == source_rows`), so this is real deployment activity, not a filter fault: bursts of factory or proxy deployments on some days. The trial day 2025-11-01 had 174,909 too.

**Failures and retries:**

- 2025-11-27 logs and traces failed on `TimeoutError: The read operation timed out`, reading from S3.
- A rerun of the same command skipped the 148 finished partitions and wrote those two.

**Time and throughput:**

- First pass: 49,668 s (13.8 h). Retry: 3,107 s. Together 52,775 s for 104.8 GB of source, an average of **2.0 MB/s**. The trial measured 7 MB/s.
- By hour:
  - The first 2.5 hours ran at 4 to 8.6 MB/s, as in the trial.
  - From 00:00 UTC on 2026-11-25 it fell to 0 to 1.6 MB/s and stayed there.
  - The retry, with 2 tasks, ran at 1.1 MB/s.
- The Mac did not sleep and recorded no thermal events (`pmset` log). A single ranged GET from the bucket afterwards ran at 0.59 MB/s, about the trial's 0.7. Cloudflare gave 6.3 MB/s on the same line (22.8 MB/s when the manager measured it before the trial).
- So the limit is the network path, and it varies over the day. The code is not the limit.

**Memory:**

- The peak for the whole process tree, sampled every 30 s, was **2.27 GB**.
- The highest single task was 2.09 GB.

**Size:**

- November's output-to-source ratios applied to the year's raw sizes project **about 125 GB**: logs 51, transactions 55, traces 15, contracts 2, blocks 1.
- That is lower than the trial's 171 GB, because sorted output compresses logs better.
