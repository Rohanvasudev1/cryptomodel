# Experiment log

Add one entry per run, newest first. Record failed runs too. The ablation tables in the paper come from this file.

**Rule.** Every session that runs anything (a trial, labeling, training or evaluation) adds an entry here in the same PR; the manager rejects a PR that runs something without one. Write the hypothesis and pass threshold before looking at the results, copying them from the phase gate where one applies. The full rules are in "How we run experiments" in `PLAN.md`.

## Template

```text
Run ID:
Date:
Phase:
Question this run answers:
Hypothesis (pre-registered, written before the results):
Pass threshold (from the PLAN.md gate, or set here before the run):

Data snapshot date:
Pretraining cutoff date:
Train, validation and test periods:
Split (time split by default; say if not):
Label and label version:
Base rate (per label and horizon):
Code commit:
Config file:
Seeds:
Machine:

Model size:
Objectives:
Wall-clock time:

Results:
  Metric, value (mean and 95% interval over seeds), base rate, compared with which baseline

What changed from the previous run:
Outcome (pass, fail or inconclusive, against the threshold above):
Conclusion:
Decision taken (and the decision-log entry, if any):
Next step:
```

## Runs

```text
Run ID: P1-extract-full-001
Date: 2026-11-24 (started; results filled in when the run finishes)
Phase: 1 (full-year AWS extraction with the extractor merged in PR #8)
Question this run answers: Can this Mac produce the filtered AWS extract for the
  whole window (2025-11-01 to 2026-10-31) within the trial's measured envelope
  (about 7 MB/s, about 74 h, under 180 GB on disk, peak memory under 4 GB), with
  complete, valid manifests for every day and table?
Hypothesis (pre-registered, written before the results): The year extracts in
  download mode at about the trial's 7 MB/s average, in about 74 h of run time,
  to about 171 GB, with the whole process tree under 4 GB. Every one of the
  365 days x 5 tables gets a manifest that matches its output file.
Pass threshold (set here before the run, from the trial's envelope; no PLAN.md
  gate number applies):
  (1) Completeness: all 1,825 (day, table) partitions have a _manifest.json
      whose output file exists with the recorded size, spec hash equal to the
      current spec, code_dirty false, and rows > 0 and source_rows > 0.
  (2) Size: total raw_filtered output <= 180 GB.
  (3) Time: summed run wall time (excluding any stopped interval between
      restarts) <= 81 h (74 h + 10%).
  (4) Throughput: average raw MB/s (source bytes / summed run wall time)
      >= 6.3 MB/s (7 MB/s - 10%).
  (5) Memory: peak RSS of the whole extractor process tree, sampled every 30 s,
      <= 4 GB.
  Stop rule: if the projected total size passes about 170 GB, stop and ask the
  manager before changing columns.
  Anomalies (reported, not pass/fail): any day whose kept rows for a table are
  below 50% or above 200% of that table's median for the month.

Data snapshot date: AWS Public Blockchain Data (s3://aws-public-blockchain/v1.0/eth/)
  as read from 2026-11-24 on (each manifest records its own snapshot date)
Pretraining cutoff date: n/a
Train, validation and test periods: n/a
Split: n/a
Label and label version: n/a
Base rate: n/a
Code commit: the commit adding this entry (run from a clean detached checkout of
  it, so every manifest records it with code_dirty false)
Config file: none; CLI defaults: --mode download --workers 5 --connections 16.
  Run in two legs: 2025-11-01..2025-11-30, then 2025-12-01..2026-10-31.
Seeds: n/a (deterministic)
Machine: Mac, Apple M1, 8 cores, 16 GB RAM, home internet, AWS us-east-2

Model size: n/a
Objectives: n/a
Wall-clock time: (pending)

Results: (pending)

What changed from the previous run: full window instead of 3 trial days; sorted
  output and whitespace-insensitive spec hash (PR #8 review), so the 3 trial
  days are re-extracted.
Outcome: (pending)
Conclusion: (pending)
Decision taken: (pending)
Next step: (pending)
```

```text
Run ID: P1-decode-001
Date: 2026-11-24
Phase: 1 (decode Uniswap V2/V3/V4, fork and ERC-20 events; PR #7)
Question this run answers: Does the decoder handle real AWS logs at scale: no crash,
  few decode errors, and every error explained?
Hypothesis (pre-registered, written before the results): Not pre-registered. An
  identical exploratory run (same file, same rows) happened before the experiment
  rules (PR #6) existed. The hypothesis and threshold below were written after
  that run, so read the outcome as a smoke test, not a gate.
  Hypothesis: on real logs, almost every log with a known topic0 decodes, and the
  only failures are contracts that reuse a signature with a different indexed layout.
Pass threshold (set here, no PLAN.md gate applies): (1) no crash; (2) decode errors
  below 0.1% of logs with a known topic0; (3) every error message names a layout
  mismatch, not a decoder bug.

Data snapshot date: AWS Public Blockchain Data as read on 2026-11-24, partition
  s3://aws-public-blockchain/v1.0/eth/logs/date=2026-11-20/, file
  part-00000-0701f83b-acb5-4c41-b379-0f9ed95ccbde-c000.snappy.parquet (6,268,618 rows),
  first 500,000 rows in file order (DuckDB LIMIT; the rows span blocks
  26,452,578 to 26,459,749, 2026-11-20 00:00:11 to 23:59:59 UTC; the file is not
  sorted by block)
Pretraining cutoff date: n/a
Train, validation and test periods: n/a
Split: n/a
Label and label version: n/a
Base rate: n/a
Code commit: f2c9a5c (branch claude/p1-decode-cf7322)
Config file: none (decode_logs called with defaults, no prior pool registry)
Seeds: n/a (deterministic)
Machine: Mac, Apple M1, 8 cores, 16 GB RAM, macOS 27.2.1; data read remotely
  from S3 us-east-2

Model size: n/a
Objectives: n/a
Wall-clock time: 89.0 s for the remote read (DuckDB httpfs), 3.66 s for decode_logs

Results:
  Rows in: 500,000 logs; 363,399 have a known topic0.
  Decoded rows per event type:
    erc20_transfer 298,459   erc20_approval 23,880
    v2_pair_created 2   v2_mint 52   v2_burn 13   v2_swap 5,414   v2_sync 5,505
    v3_pool_created 0   v3_initialize 2   v3_mint 394   v3_burn 1,015
    v3_swap 12,307   v3_collect 963
    v4_initialize 106   v4_modify_liquidity 638   v4_swap 10,819
  Ignored on purpose: 3,823 ERC-721 Transfer/Approval logs (4 topics).
  dex_action: 31,723 rows
    v2: create 2, swap 5,414, mint 52, burn 13
    v3: swap 12,307, mint 394, burn 1,015, collect 963
    v4: create 106, swap 10,819, mint 280, burn 279, collect 79
  Pool resolution (non-create rows): 161 resolved, 31,454 unresolved, across
    3,439 distinct unresolved pools. Expected: the registry held only the 108
    pools created inside this slice, and no prior registry was passed.
  Creates by dex: uniswap v4 106, uniswap v2 2; no unknown_fork factories in
    this slice.
  Decode errors: 7 of 363,399 (0.002%). Messages: 6 x "V2Mint: expected 2
    topics, got 1" and 1 x "Erc20Transfer: expected 3 topics, got 1". All 7
    are contracts that reuse the signature with no indexed params.
  Decode throughput: about 137,000 logs per second (500,000 / 3.66 s), single
    process.

What changed from the previous run: only lint formatting (commit f2c9a5c against
  e454767); the counts match the exploratory run exactly.
Outcome: pass on all three conditions (no crash; 0.002% errors, under 0.1%; all
  errors are layout mismatches). Not pre-registered (see above).
Conclusion: The decoder handles real AWS logs. The remote read costs about 24x
  the decode time, so I/O, not decoding, limits throughput. Without a registry
  built from history, pools mostly stay unresolved.
Decision taken: none; no threshold or plan change.
Next step: build the pool registry from the full history of creation events
  (V2 PairCreated, V3 PoolCreated, V4 Initialize from the factories in
  decode/registry.py), then rerun on a full day and measure the share of
  resolved pools. Add V2 LP amounts from pair Transfers to and from 0x0.
```

```text
Run ID: P1-extract-001
Date: 2026-11-24
Phase: 1 (AWS extraction pipeline; this PR)
Question this run answers: Does a filtered year of AWS eth data fit on the Mac's
  280 GB, how long will the full extraction take, and where is the bottleneck?
Hypothesis (pre-registered, written before the results): Written after seeing only
  the first result (2025-11-01 logs: 2.52M rows, 159 MB, 620 s, 1.7 GB RSS); all
  other results came after. The filtered year is 115 to 180 GB of zstd Parquet
  (the Phase 0 estimate), and the full extraction finishes in a few days on the Mac
  with bounded memory.
Pass threshold (set here, no PLAN.md gate applies): (1) projected year size
  <= 180 GB, leaving >= 100 GB for derived tables; (2) projected year time <= 72 h;
  (3) peak RSS of the whole process tree <= 8 GB. The manager later asked for
  about 24 h; that was not pre-registered and is reported against separately.

Data snapshot date: AWS Public Blockchain Data (s3://aws-public-blockchain/v1.0/eth/)
  as read on 2026-11-24. Trial days 2025-11-01, 2026-03-15, 2026-09-15 (all five
  tables); throughput runs also on 2025-11-02 and 2025-11-03.
Pretraining cutoff date: n/a
Train, validation and test periods: n/a
Split: n/a
Label and label version: n/a
Base rate: n/a
Code commit: trial runs from the uncommitted tree on 669caca (manifests say
  code_dirty: true); the 2-day download run at b2008ec (rebased as 1a2e239);
  final code in this PR
  (branch claude/p1-extract-0fc8f0). The filters are the same throughout.
Config file: none (CLI flags below)
Seeds: n/a (deterministic)
Machine: Mac, Apple M1, 8 cores, 16 GB RAM, home internet, AWS us-east-2

Model size: n/a
Objectives: n/a
Wall-clock time: stream mode 1,097 s, 1,520 s and 2,075 s for the three trial days;
  download mode 749 s (2026-09-15) and 935 s for 2025-11-02 to 2025-11-03 together

Results:
  Rows kept / output MB / stream s per table (2025-11-01; 2026-03-15; 2026-09-15):
    transactions 1.36M/96/259; 1.78M/147/894; 1.89M/133/946
    logs         2.52M/159/620; 4.11M/266/570; 4.57M/295/745  (of 3.8M; 5.6M; 6.3M)
    traces       0.84M/31/1,093; 1.25M/44/1,516; 1.49M/45/2,070 (of 10.5M; 13.5M; 17.1M)
    blocks       7,153/3.2; 7,175/3.1; 7,170/2.9
    contracts    174,909/8.6; 185,468/9.1; 23,061/7.1
  Output per day: 299, 470 and 482 MB from 2.89, 4.23 and 5.27 GB raw.
  Projected year size: 171 GB (per-table output/raw ratios times the year's raw
    sizes: logs 97, transactions 53, traces 16, contracts 3, blocks 1).
  Throughput (raw bytes / wall):
    stream mode, 2 or 4 workers: 2.2 to 2.3 MB/s -> year about 8 days
    download mode, 1 day, 5 tasks x 16 connections: 7.0 MB/s -> year about 74 h
    download mode, 2 days, 10 tasks x 16 connections: 7.1 MB/s -> year about 73 h
    one object, 64 connections: 6.2 MB/s
  Bottleneck: the network path to us-east-2. One ranged GET gets 0.7 to 1.3 MB/s,
    and the aggregate tops out at about 7 MB/s on average (16 MB/s in 15-second
    peaks). Cloudflare on the same line gets 7.7 to 22.8 MB/s. Projection reads 85%
    of raw bytes, because the needed `input` columns dominate. Row filters can't be
    pushed down (topic0 is in a list). Local filtering is cheap: 2.1 s for a full
    traces day.
  Peak memory, whole tree: 3.8 GB in stream mode (4 workers); 1.7 GB in download
    mode with 10 tasks, after switching local reads to DuckDB read_parquet (a
    pyarrow scanner peaked at 5.4 GB per traces task).
  Correctness: stream and download outputs have the same rows on 2026-09-15 (row
    order differs; AWS files are not sorted by block either). Resume re-ran only
    the 2 failed tables of day 1 and skipped the 3 done (8 s).

What changed from the previous run: first extraction run. Download mode and the
  DuckDB local reader were added during this run, after stream mode proved slow.
Outcome: (1) pass, 171 GB; (2) fail, about 74 h in the best mode against 72 h
  (stream mode about 8 days); the 24 h target is not reachable from this Mac;
  (3) pass, 1.7 GB.
Conclusion: The filtered year fits with about 110 GB to spare. Extraction is
  network-bound at about 7 MB/s to us-east-2. Download mode is 3x faster than
  streaming and becomes the default; the year takes about 3 days on the Mac.
Decision taken: CLI default is download mode (--workers 5 --connections 16);
  stream mode stays as an option. No PLAN.md change.
Next step: the manager either starts the year on the Mac (about 3 days,
  resumable), or runs the extractor on an EC2 instance in us-east-2 (a few hours;
  needs an AWS account, the user's call). Optional speedups: fetch only the
  projected column chunks (15% fewer bytes), and decide whether to drop
  traces.input (35 to 40% fewer bytes, loses init code). If disk gets tight, drop
  logs.transaction_hash first (about 35 GB).
```
