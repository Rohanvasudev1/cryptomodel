# Phase 0: data source survey

Date: 2026-11-24. Purpose: inform the fixed decisions table in `PLAN.md` (pretraining data window, pretraining cutoff, T1, T2) and the Phase 1 source choice.

Method: read vendor docs and pricing pages, listed the public AWS S3 bucket (object metadata only, no data files), and pulled counts from public charts and ClickHouse's free public CryptoHouse endpoint (read-only aggregate SQL). No accounts, keys, paid queries or chain-data downloads. Anything not confirmed on a primary page is marked **(unverified)**.

## Summary

- **Use AWS Public Blockchain Data (`s3://aws-public-blockchain/v1.0/eth/`) as the primary Ethereum source.** It is free, needs no account, is already Parquet, holds all five tables (blocks, transactions, logs, traces, token transfers) plus contracts from 2015-07-30, and is updated daily (latest partition 2026-11-23).
- **A raw year does not fit on 280 GB.** Nov 2025 to Oct 2026 is 1.86 TB on AWS (traces alone 0.98 TB). Phase 1 must stream each day, project columns and filter rows before writing locally. A filtered local copy should be about 100 to 180 GB (estimate below).
- **BigQuery is the fallback and cross-check, not the primary.** Scanning is cheap (about 5 TiB, about $25 for a year), but getting the data out costs about $0.12/GiB in egress (about $200+ for a full year) and needs a billed GCP project.
- **cryo plus a paid RPC is for gaps only**: BSC logs and traces, and receipts or traces AWS lacks. About $80 to $250 for a year of Ethereum. Self-hosted Erigon or Reth needs 535 GB to 2.8 TB and does not fit.
- **Paradigm's data portal is stale** (ends around March 2023, no logs or traces) and cannot be used for 2025 or 2026.
- **Proposed dates:** extraction window 2025-11-01 to 2026-10-31, T1 = 2026-03-31, T2 = 2026-06-30, pretraining cutoff = T2, test launches 2026-08-01 to 2026-09-30, with labels observed to 2026-10-30.

## Source comparison

| | AWS public data | BigQuery `crypto_ethereum` | BigQuery `goog_blockchain_ethereum_mainnet_us` | Paradigm data portal | cryo + RPC provider | Self-hosted Erigon or Reth |
|---|---|---|---|---|---|---|
| Latest data | 2026-11-23 (daily, about 04:00 UTC) | Not checked, needs a `MAX(block_timestamp)` query (unverified) | About 12 to 15 minutes behind head | About March 2023 (block 16.8M) | Chain head | Chain head |
| Logs | Yes | Yes | Yes, plus `decoded_events` | No | Yes | Yes |
| Traces | Yes, Parity-style | Yes, Parity-style | Yes, Parity-style | No | Yes, needs `trace_block` (Erigon or Reth backend) | Archive node only |
| Token transfers | ERC-20 only | ERC-20 and ERC-721 | ERC-20, 721 and 1155 | No | `erc20_transfers` dataset | Through cryo |
| Cost for one year | $0 | About $25 to scan plus about $200 egress (estimate) | Same as left | $0 | About $80 to $250 | Hardware only |
| Time to extract | About 6 to 12 h streaming at 50 to 100 MB/s (estimate) | Hours, mostly the download | Same as left | n/a | About 17 to 36 h at plan rate limits (estimate) | Days to sync, then fast |
| Parquet size per year | 1.86 TB raw (measured from listing) | 0.5 to 1 TB+ per year of traces alone (estimate) | Similar | n/a | Similar to AWS | n/a |
| Fits 280 GB raw | No, filtered yes | No, filtered yes | No, filtered yes | n/a | No, filtered yes | No (535 GB to 2.8 TB node) |
| Rate limits | None stated, normal S3 | 1 GB per export file, 50 TiB extract per day, 200 TiB query per day default | Same as left | None | Provider RPS or CU caps | None |
| License for data | Not stated; registry links an MIT code license; "experimental" | Not stated; code MIT | Pre-GA terms; data license not stated | CC0 | Provider ToS; Alchemy bans scraping and data mining | Your own node |
| BSC | Blocks and transactions only (BNB Chain maintains it) | None | None | None | Yes with a BSC trace node | Yes, but larger |
| Base | Full tables (SonarX), about a week behind | None | Separate listing `base-data-pdp.base_mainnet` (unverified) | None | Yes (unverified on traces) | Base archive 4.1 TB, 128 GB RAM |

## Per-source notes

### AWS Public Blockchain Data (recommended)

- **Layout:** `s3://aws-public-blockchain/v1.0/eth/{blocks,transactions,logs,token_transfers,traces,contracts}/date=YYYY-MM-DD/*.snappy.parquet`, region us-east-2. Read with `aws s3 --no-sign-request` or DuckDB `httpfs`. [Registry entry](https://registry.opendata.aws/aws-public-blockchain/), [registry YAML](https://github.com/awslabs/open-data-registry/blob/main/datasets/aws-public-blockchain.yaml), [AWS README](https://github.com/aws-samples/digital-assets-examples/blob/main/analytics/README.md).
- **Freshness:** daily. I listed `traces/date=2026-11-19` written 2026-11-20T04:01Z, and the research pass saw `date=2026-11-23`. History starts at `date=2015-07-30`. [Bucket listing](https://aws-public-blockchain.s3.us-east-2.amazonaws.com/?list-type=2&prefix=v1.0/eth/traces/date=2026-11).
- **Size, Nov 2025 to Oct 2026, summed from the bucket listing:**

  | Table | GB | GB per day |
  |---|---|---|
  | traces | 983 | 2.7 |
  | logs | 400 | 1.1 |
  | transactions | 297 | 0.8 |
  | token_transfers | 175 | 0.5 |
  | contracts | 7.4 | 0.02 |
  | blocks | 2.1 | 0.006 |
  | **Total** | **1,865** | **5.1** |

- **Schema caveats** ([eth schema](https://github.com/aws-samples/digital-assets-examples/blob/main/analytics/consumer/schema/eth.md)):
  - `token_transfers.value` and `traces.value` are `double`, which loses uint256 precision. Decode token amounts from `logs.data` instead and use `token_transfers` only as a cross-check.
  - `token_transfers` is ERC-20 only.
  - Traces carry `trace_type`, `call_type`, `trace_address`, `input`, `output` (creation bytecode for `create`), `error`, `status`, `gas_used`. This is enough for token-deployment detection, internal ETH transfers and failed-sell detection.
- **Cost:** none for anonymous reads. The [Open Data FAQ](https://aws.amazon.com/opendata/faqs/) says the sponsorship covers storage and distribution (egress) costs; the [sponsorship page](https://aws.amazon.com/opendata/open-data-sponsorship-program) only says storage. Anonymous `--no-sign-request` reads bill no account in any case.
- **Caveat:** AWS calls the data "experimental and not recommended for production use". Validate it against a second source (see the cross-check plan below).
- **License:** the registry's `License` field points to the [aws-samples MIT license](https://github.com/aws-samples/digital-assets-examples/blob/main/LICENSE), which covers code. No data license is stated (unverified). Contact is aws-blockchain-data@amazon.com. On-chain data itself is public; the open question is whether we may redistribute AWS's Parquet files, not the chain facts. Publishing labels, token addresses and derived features with our own code to regenerate them avoids the question.
- **Base:** `v1.1/sonarx/base/` (approvals, blocks, logs, receipts, traces, transactions, transactions_failed, transfers), from June 2023, about a week behind (latest 2026-11-17). Logs alone are about 4 GB per day, so take only the test window. SonarX terms not found (unverified). [Listing](https://aws-public-blockchain.s3.us-east-2.amazonaws.com/?list-type=2&prefix=v1.1/sonarx/base/&delimiter=/).
- **BSC:** `v1.1/bnb/` has blocks and transactions only, with no logs or traces (latest 2026-11-23). [Listing](https://aws-public-blockchain.s3.us-east-2.amazonaws.com/?list-type=2&prefix=v1.1/bnb/&delimiter=/).

### BigQuery `bigquery-public-data.crypto_ethereum` (blockchain-etl)

- **Tables:** blocks, transactions, receipts, logs, token_transfers (ERC-20 and ERC-721), traces (Parity-style), contracts, tokens. [ethereum-etl schema](https://ethereum-etl.readthedocs.io/en/latest/schema/), [traces schema](https://raw.githubusercontent.com/blockchain-etl/ethereum-etl-airflow/master/dags/resources/stages/raw/schemas/traces.json).
- **Partitioning:** daily on `block_timestamp`, with no clustering found in the [loader code](https://raw.githubusercontent.com/blockchain-etl/ethereum-etl-airflow/master/dags/ethereumetl_airflow/build_load_dag.py). A date filter prunes partitions, but `LIMIT` does not cut bytes scanned.
- **Freshness:** no deprecation notice and the repos are not archived ([ethereum-etl-airflow](https://github.com/blockchain-etl/ethereum-etl-airflow)), but sibling datasets went stale: Polygon after 2024-09-01 and Solana on 2025-03-31 ([Google forum thread](https://discuss.google.dev/t/public-solana-bigquery-dataset-crypto-solana-mainnet-us-stopped-updating-on-march-31-2025/185629)). Current Ethereum freshness is **unverified**; check with a dry-run-capped `MAX(block_timestamp)` before relying on it.
- **Size:** in early 2023 the traces table held 6.33B rows, 4.21 TB logical, 2.90 TB as Parquet export; transactions held 1.85B rows, 696 GB logical ([ClickHouse blog](https://clickhouse.com/blog/clickhouse-bigquery-migrating-data-for-realtime-queries)). That is about 665 logical bytes per trace row.
- **Other chains:** no BSC dataset (listed as "Needs help" in [blockchain-etl/public-datasets](https://github.com/blockchain-etl/public-datasets)), no Base.

### BigQuery `bigquery-public-data.goog_blockchain_ethereum_mainnet_us` (Google Blockchain Analytics)

- **Tables:** `accounts_state`, `blocks`, `decoded_events`, `logs`, `receipts`, `token_transfers` (ERC-20, 721, 1155), `traces` (Parity-style), `transactions`. Partitioned **monthly** on `block_timestamp`, so the smallest prunable unit is a month. [Schema](https://docs.cloud.google.com/blockchain-analytics/docs/schema).
- **Freshness:** about 64 slots (12 to 15 minutes) behind head, waiting for finality ([known issues](https://docs.cloud.google.com/blockchain-analytics/docs/known-issues?hl=en)). The older `goog-blockchain.ethereum_mainnet_us` listing stopped updating after 2026-10-31; the `bigquery-public-data` copy is the one to use ([schema page](https://docs.cloud.google.com/blockchain-analytics/docs/schema)).
- **Status:** Pre-GA Preview under the Pre-GA Offerings Terms ([overview](https://docs.cloud.google.com/blockchain-analytics/docs/overview)). Data license and republication terms are **unverified**.
- **Other chains:** traces exist for Ethereum only; no BSC ([supported datasets](https://docs.cloud.google.com/blockchain-analytics/docs/supported-datasets)). Base is listed as a separate `base-data-pdp.base_mainnet` (unverified).

### BigQuery pricing and quotas (both datasets)

- **Queries:** on-demand $6.25/TiB scanned, first 1 TiB per month free, 10 MB minimum per table referenced ([pricing](https://cloud.google.com/bigquery/pricing)).
- **Export:** `EXPORT DATA` bills the bytes its query scans, and extract jobs on the shared pool are free up to 50 TiB per day ([export statements](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/export-statements)). At most 1 GB per exported file, so use a wildcard URI, and the bucket must be in the same location (US) ([exporting data](https://docs.cloud.google.com/bigquery/docs/exporting-data), [quotas](https://docs.cloud.google.com/bigquery/quotas)).
- **Download:** the Storage Read API is $1.10/TiB with 300 TiB per month free, plus network egress at $0.12/GiB for the first 1 TiB. GCS internet egress is $0.12/GiB up to 10 TiB, with 100 GB per month free from North America ([GCS pricing](https://cloud.google.com/storage/pricing)).
- **Sandbox:** 1 TiB of queries per month, 10 GiB storage, 60-day table expiry, no billing account ([sandbox](https://docs.cloud.google.com/bigquery/docs/sandbox)). Enough for cross-checks, not for extraction.
- **Estimated cost for one year (estimate):** traces about 3 TB logical (4.6 to 5.3B rows at about 665 B), plus logs, transactions and transfers about 1.5 to 2 TB, so about 5 TiB, about $25 after the free TiB. Egress for a filtered 150 GB copy is about $18; for a full 1.9 TB copy about $220.

### Paradigm data portal

- Three Ethereum datasets only, all v1.0.0: `ethereum_contracts` (7.05 GB), `ethereum_native_transfers` (65.5 GB), `ethereum_slots` (41.2 GB). No blocks, transactions, logs or traces. [Repo](https://github.com/paradigmxyz/paradigm-data-portal), [manifest](https://raw.githubusercontent.com/paradigmxyz/paradigm-data-portal/main/datasets/global_manifest.json).
- `ethereum_contracts` ends at block 16,799,999 (about March 2023). `data.paradigm.xyz` did not resolve on 2026-11-24.
- CC0 license. Ethereum only. **Not usable** for a 2025 to 2026 window.

### cryo with an RPC provider

- **cryo:** extracts to Parquet (lz4 by default). Datasets include blocks, transactions, logs, traces, contracts, native_transfers, erc20_transfers, erc20_metadata and state diffs. `traces` and `contracts` call `trace_block`, which Erigon and Reth serve and Geth does not. Rate flags: `--requests-per-second`, `--max-concurrent-requests`, `--max-concurrent-chunks`; the README warns that defaults overload a node. MIT or Apache-2.0. Works on any ethers-rs chain, BNB named; Base (unverified). [cryo README](https://github.com/paradigmxyz/cryo). No published year-scale throughput numbers.
- **Cost for about 2.61M blocks**, three calls per block (block, receipts, trace). Logs and transfers come from receipts.

  | Provider | Units per block | Cost for the year | Time at plan limit | Notes |
  |---|---|---|---|---|
  | Alchemy pay-as-you-go | 60 CU | About $82 | About 36 h (unverified) | [Pricing](https://www.alchemy.com/pricing), [CU costs](https://www.alchemy.com/docs/reference/compute-unit-costs). [Terms](https://legal.alchemy.com/) allow "internal business purposes" only and ban scraping and data mining tools, a real risk for bulk extraction and redistribution. |
  | QuickNode | About 80 credits | About $130 to $249 | About 17.5 h at 125 RPS | [Pricing](https://www.quicknode.com/pricing), [credits](https://www.quicknode.com/api-credits/eth). Trace and debug on paid plans. ToS not reviewed. |
  | Infura | 1,380 credits | About $360 (Team, 2 months) | About 48 days at the 75M per day cap | [Pricing](https://www.infura.io/pricing), [credit costs](https://docs.infura.io/get-started/pricing/credit-cost/). No BSC. |
  | Chainstack | About 6 RU (unverified) | About $49 | Not estimated | [Pricing](https://chainstack.com/pricing/). Ethereum `trace_*` needs a dedicated Erigon archive node ([docs](https://docs.chainstack.com/docs/debug-and-trace-apis)). |

- **BSC and Base:** BSC is about 42M blocks per year at 0.75 s since Maxwell ([BNB Chain](https://docs.bnbchain.org/announce/maxwell-bsc/)), 16 times Ethereum's call count. Base is about 15.8M blocks per year (6 times). Pull only the test windows.

### Self-hosted Erigon or Reth

- **Reth:** Ethereum archive needs at least 2.8 TB, full at least 1.2 TB. A full node keeps only the last 10,064 blocks of history, so historical `trace_*` and `eth_getLogs` need an archive node. Base archive 4.1 TB with 128 GB RAM. [Requirements](https://reth.rs/run/system-requirements), [pruning](https://reth.rs/run/storage/pruning).
- **Erigon 3.8:** archive 2.25 TB (4 TB recommended, 32 GB RAM), full 535 GB, minimal 524 GB ([hardware](https://docs.erigon.tech/get-started/hardware-requirements)).
- **Does not fit** 280 GB or 16 GB RAM. Not an option on the Mac.

### Other options checked

- **Dune:** the free plan has no API. Results are capped at 32 GB, and Datashare is sales-quoted ([rate limits](https://docs.dune.com/api-reference/overview/rate-limits), [Datashare FAQ](https://docs.dune.com/datashare/datashare-faqs)). [Terms](https://dune.com/terms) say Dune "retains all rights" to its databases and ban scraping. Poor fit for a published benchmark.
- **Envio HyperSync:** fast logs, transactions and blocks for Ethereum, BSC and Base. Traces are a paid add-on for Ethereum and Base, with none for BSC. The free tier needs an API token ([overview](https://docs.envio.dev/docs/HyperSync/overview), [networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), [pricing](https://envio.dev/pricing)). **The best candidate for BSC logs.**
- **SQD Portal:** free public portal serving blocks, transactions, logs, traces and state diffs, limited to 20 requests per 10 s, JSON Lines output ([docs](https://docs.sqd.dev/en/portal/evm/overview)). Per-chain trace coverage and terms are unverified.
- **ClickHouse CryptoHouse:** free public SQL endpoint with Ethereum tables, but its data ends at 2026-04-30. Good for counting, not for the window. Used for the counts below.
- **Allium, Token Terminal ([raw EVM tables](https://tokenterminal.com/docs/catalog/chain-verticals/evm/ethereum/raw)), Goldsky, SonarX direct:** sales-priced warehouses. No free bulk Parquet.
- **HuggingFace and Kaggle:** only small transaction or contract subsets (for example `apehex/evm_contracts`). No full year with logs and traces.
- **Xatu (ethPandaOps):** public Parquet of mainnet blocks ([getting started](https://ethpandaops.io/data/xatu/getting-started/)), Ethereum only. The docs discourage bulk pulls, and the full table list is unverified.

## Event counts for one year of Ethereum

Sources: Etherscan chart CSVs (`etherscan.io/chart/{tx,blocks,tokenerc-20txns}?output=csv`) for Nov 2025 to Oct 2026. For logs, traces and pools, CryptoHouse aggregates over May 2025 to Apr 2026 (blocks 22,385,294 to 24,993,647), because CryptoHouse ends 2026-04-30.

| Item | Per day | Per year | Notes |
|---|---|---|---|
| Blocks | About 7,170 | 2.61M | About 0.75% missed slots |
| Transactions | 2.07M mean (1.12M to 3.63M) | 755M (Nov 25 to Oct 26) | 649M over May 25 to Apr 26. Gas limit went 45M to 60M around Fusaka on 2025-12-03 ([The Block](https://www.theblock.co/news/ecosystems/2026-01-02-ethereum-daily-transactions-all-time-high-384130)) |
| Event logs | About 5.1M (6.1M in Apr 2026) | 1.86B (May to Apr), about 2.2B scaled to Nov to Oct | 2.87 logs per transaction |
| Traces | About 12.6M | 4.61B (May to Apr), about 5.3B scaled | 99.5% `call`, 22.8M `create`. 7.1 per transaction |
| ERC-20 transfers | 3.50M | 1.27B | About 1.7 per transaction |
| Uniswap V2 pairs | 224 | 81.7K | Factory 0x5c69… |
| Uniswap V3 pools | 73 | 26.6K | Factory 0x1f98… |
| Uniswap V4 pools | 169, rising to about 600 in Apr 2026 | 61.8K | Likely launchpad or spam pools |
| New ERC-20 tokens | At least about 500, about 750 per [Dedaub](https://dedaub.com/blog/erc-20-on-ethereum-growth-risks-and-hidden-traps-in-2025/) | About 180K to 275K | Label population upper bound |

**Raw rows for one year:** about 8.3B (transactions, logs, traces and blocks).

**Decoded event table (estimate):** about 2.0 to 2.5B actions. This is transactions (0.75B) plus ERC-20 transfers (1.27B) plus DEX swap, mint and burn events plus value-bearing internal calls and creates. Most of the 5.3B traces are zero-value internal calls that the event table drops.

**After merging consecutive repeats (estimate):** about 1.5 to 2.3B.

- In a one-day sample of 5.88M logs, 27.1% share contract address and event signature with the previous log in the block, mostly Transfer runs. That is an upper bound on what merging removes from the log stream.
- Only 0.058% are exact duplicates of the previous log.
- How much merging removes per entity sequence is unknown until Phase 1 builds the views.
- The wallet view counts each transfer twice (sender and receiver), so token counts per view will be higher than the event count.

These figures are an order of magnitude below the plan's 20 billion estimate, which looks like full history or several chains. Phase 1 replaces it with the measured number.

### Fitting the year on 280 GB (estimate)

Stream each AWS daily partition through DuckDB, keep only the needed columns, store addresses and hashes as binary rather than hex strings, and write zstd Parquet:

| Table and filter | Rows | Estimated local size |
|---|---|---|
| transactions: hash, from, to, value, gas fields, status, 4-byte selector only (no full `input`) | 0.75B | 40 to 60 GB |
| logs: Transfer, Approval, Uniswap V2, V3 and V4 and fork pool, swap, mint, burn and sync topics | About 1.6B | 50 to 80 GB |
| traces: value-bearing calls, creates (with bytecode for token contracts only) and failed calls to token or pool contracts | 0.2 to 0.4B | 15 to 30 GB |
| blocks and contracts | Small | 10 GB |
| **Total** | | **About 115 to 180 GB** |

That leaves about 100 GB for derived tables. If it gets tight, drop Approval logs or the trace bytecode first. Keep the raw `input` only for token and pool contracts.

## Recommendation

### Sources

1. **Ethereum, primary:** AWS `v1.0/eth`, all six tables, streamed and filtered per day as above. Free, no account, current, and it covers traces.
2. **Ethereum, cross-check:** BigQuery `goog_blockchain_ethereum_mainnet_us` (or `crypto_ethereum` if fresh) in the free sandbox tier only. Compare daily counts of transactions, logs, Transfer events and creates for the window, and check a sample of traces. This catches gaps in AWS's "experimental" data. No egress needed, since only aggregates come back.
3. **Base, held-out:** AWS SonarX `v1.1/sonarx/base`, test window only.
4. **BSC, held-out:** no free bulk logs or traces. Defer to Phase 7 and choose between Envio HyperSync (logs, free tier needs a token) and cryo against a paid BSC trace RPC for the test window only.
5. **RPC:** Phase 2's honeypot simulator needs an archive RPC for `anvil --fork-url` anyway. One paid month of QuickNode or Alchemy, after reading their ToS, also covers spot-filling any AWS gaps with cryo.

### Fixed decisions (proposed)

A token belongs to the period that contains its first-liquidity time. Labels need 30 days after launch, and the snapshot needs a margin before today (2026-11-24) for late partitions.

| Decision | Proposed value |
|---|---|
| Extraction window (one year) | 2025-11-01 00:00 UTC to 2026-10-31 23:59 UTC |
| Pretraining data window | 2025-11-01 to 2026-06-30 (8 months) |
| Pretraining cutoff date | 2026-06-30 (= T2) |
| Train launches | 2025-11-01 to 2026-03-31 |
| Train period ends (T1) | 2026-03-31 |
| Embargo | 2026-04-01 to 2026-04-30 |
| Validation launches | 2026-05-01 to 2026-06-30 |
| Validation period ends (T2) | 2026-06-30 |
| Embargo | 2026-07-01 to 2026-07-31 |
| Test launches | 2026-08-01 to 2026-09-30 (2 months, about 18K V2 and V3 pools plus V4) |
| Test labels observed until | 2026-10-30 (inside the window) |
| Encoder B for the cutoff-leak test | Pretrained on the full window to 2026-10-31 |

Why these dates:

- **Every test label is observable.** Test launches end 2026-09-30 and their 30-day labels end 2026-10-30, inside the window, which is itself 3 weeks before today, so AWS has had time to land late partitions.
- **Five months of train launches** gives roughly 45K V2 and V3 pools and over 75K new tokens, which is enough for the baselines.
- **The Fusaka gas-limit change (2025-12-03) falls inside train**, so the model sees both regimes. Train volume (about 1.5M transactions per day in Nov 2025) is lower than val and test (about 2.1M per day).
- **Wallet histories start at 2025-11-01.** Older wallets get truncated sequences. Address context (creation block, type) comes from the AWS `contracts` table, which covers full history and is small.

### BigQuery cost-cap plan (cross-check use only)

1. **Isolate it.** Use a dedicated project that starts in the sandbox (no billing account), which hard-caps queries at 1 TiB per month and $0. The user creates it.
2. **Cap per day.** If billing is ever enabled, set `QueryUsagePerDay` to 1 TiB per project and `QueryUsagePerUserPerDay` to 500 GiB ([quotas](https://docs.cloud.google.com/bigquery/quotas)).
3. **Cap per query.** Set `maximum_bytes_billed` to 100 GB in `~/.bigqueryrc` (`--maximum_bytes_billed=107374182400`) and in every client job config. A query over the cap fails with no charge.
4. **Dry-run every query** and log the estimated bytes before running it.
5. **Always filter on `block_timestamp`** with literal bounds, select named columns, and never use `SELECT *`. The managed dataset partitions monthly, so filter whole months. Remember that `LIMIT` does not reduce bytes scanned.
6. **Alert, knowing alerts don't stop spend.** Budget alerts at $5, $20 and $50 notify only; the quotas above are what actually stop spend ([cost best practices](https://docs.cloud.google.com/bigquery/docs/best-practices-costs)).
7. **Expected spend:** $0. The planned cross-check is daily `COUNT`s over about 12 months of transactions, logs and traces, under 1 TiB scanned.

## Open questions for the user

1. **Window.** Is one year (2025-11 to 2026-10) right, or do you want more train history, for example 15 months from 2025-08? More history costs about 5 GB per day raw and about 0.4 GB per day filtered locally.
2. **Cross-check account.** May we create a BigQuery sandbox project for the cross-check? It needs a Google account and is free with no billing.
3. **RPC provider.** Which provider for the archive RPC Phase 2 needs anyway, and are you willing to pay for one month (about $50 to $250)? Alchemy's terms ban scraping and data mining, so QuickNode or Chainstack may be safer for bulk cryo pulls.
4. **Data license.** Should we email aws-blockchain-data@amazon.com about republishing derived Parquet, or plan to publish only labels, addresses and code that regenerates the data?
5. **BSC.** Is it acceptable to defer BSC extraction to Phase 7 and accept either Envio (needs a free token) or a paid BSC trace RPC for a two-month test window?
6. **Plan text.** The plan's 20B event estimate looks too high for one year of Ethereum (estimate 1.5 to 2.5B after merging). Should the compute plan be redone after Phase 1 measures it, as the gate already says?
