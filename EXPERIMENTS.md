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
