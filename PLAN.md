# Scam token detector: project plan

## Goal

Build a self-supervised foundation model over Ethereum on-chain events. Use it to score new tokens for rug pulls and honeypots at fixed times after launch.

The core paper makes three contributions:

1. A token-launch foundation model pretrained on unlabeled token sequences.
2. A leakage-free benchmark with time splits and fixed scoring horizons.
3. A pretraining-cutoff rule, tested by measuring how much later data leaks into scores.

Background and sources are in `reports/Crypto transaction foundation model.md`.

## How this plan is built

The phases follow the order the published models use:

- PRAGMA and EBES fix tasks and the test protocol first.
- Revolut treats the model as "a data platform first, and a model second".
- nuFormer measures its tokenizer and beats a LightGBM baseline.
- PRAGMA ablates its masking objectives and reports frozen probes next to LoRA.
- TREASURE and PRAGMA scale only after small models work.
- nuFormer fuses the model with tabular features for the final task.

Every phase ends with a gate. Do not start the next phase until the gate passes.

## Where each phase runs

| Phase | Machine |
|---|---|
| 0 to 5 | Mac |
| 6 | Rented GPU |
| 7 | Mac for development, rented GPU for final runs |
| 8 | Mac |

## Fixed decisions

Fill these in during phase 0. Do not change them later without writing down why.

| Decision | Value |
|---|---|
| Chain for pretraining | Ethereum mainnet |
| Held-out chains | BSC, Base |
| Extraction window | 2025-11-01 00:00 UTC to 2026-10-31 23:59 UTC (one year) |
| Pretraining data window | 2025-11-01 to 2026-06-30 (8 months) |
| Pretraining cutoff date | 2026-06-30 (= T2) |
| Train launches | 2025-11-01 to 2026-03-31 |
| Train period ends (T1) | 2026-03-31 |
| Embargo after train | 2026-04-01 to 2026-04-30 |
| Validation launches | 2026-05-01 to 2026-06-30 |
| Validation period ends (T2) | 2026-06-30 |
| Embargo after validation | 2026-07-01 to 2026-07-30 |
| Test launches | 2026-07-31 to 2026-09-30 |
| Test labels observed until | 2026-10-30 |
| Embargo between periods | 30 days |
| Period assignment | A token belongs to the period that contains its first-liquidity time |
| Encoder B (Phase 5 cutoff-leak test) | Pretrained on the full extraction window, to 2026-10-31 |
| Scoring horizons | 5, 15 and 60 minutes after first liquidity; 500 transfers; 24 hours |
| Rug-pull label, strict (headline) | Linked wallets remove 80% or more of pool liquidity, or the deployer or linked wallets dump the token, within 30 days. A price fall alone does not count. |
| Rug-pull label, broad (secondary) | The strict label, or price falls 90% or more, within 30 days |
| Base rates | Report each label's base rate next to every metric |
| Honeypot label | Sells by unrelated wallets fail after the observation time |
| Headline metric | Precision at the top 1% of daily launches, plus PR-AUC |
| Minimum seeds per result | 5 |

The label thresholds are design choices. Phase 2 tests them against the manual datasets.

## Decision log

Decisions made on 2026-11-24 after the Phase 0 reports:

- **Dates.** The table above uses the dates proposed in [data_sources.md](reports/phase0/data_sources.md#fixed-decisions-proposed). Reason: every test label is observable inside the window, which ends three weeks before the decision date so late AWS partitions have landed; train has five months of launches; and the Fusaka gas-limit change (2025-12-03) falls inside train.
- **Two rug-pull labels.** A strict headline label (liquidity removal or deployer dump) and the broad original label (adds a 90% price fall) as a secondary task. Reason: a price fall alone also catches failed but honest launches, and the manual sets check liquidity rugs. See [tasks_and_datasets.md](reports/phase0/tasks_and_datasets.md#5-proposed-task-list).
- **Phishing on B4E is pending Etherscan's permission.** Reason: Etherscan's terms ban ML use of its data, including data obtained through third parties, and B4E's labels come from Etherscan ([tasks_and_datasets.md](reports/phase0/tasks_and_datasets.md#21-etherscan-terms-read-this-first)). The user asks Etherscan (draft in [docs/drafts/etherscan_ml_permission_email.md](docs/drafts/etherscan_ml_permission_email.md)). If Etherscan refuses or does not answer, drop the phishing task. BERT4ETH stays as an embedding baseline on our own tasks either way.
- **Exchange labels come from non-Etherscan sources**, such as exchanges' proof-of-reserves disclosures. Reason: the same Etherscan terms cover eth-labels and most public exchange lists ([tasks_and_datasets.md](reports/phase0/tasks_and_datasets.md#23-wallet-types-exchange-bot-mev-searcher-person)).
- **The "person" wallet probe is dropped.** Reason: no usable labels exist; the only gold set is 133 humans and 137 bots ([tasks_and_datasets.md](reports/phase0/tasks_and_datasets.md#23-wallet-types-exchange-bot-mev-searcher-person)). The wallet probes are exchange, MEV searcher and bot.
- **Primary source is AWS Public Blockchain Data** (`s3://aws-public-blockchain/v1.0/eth/`), with BigQuery as a cross-check only. Reason: AWS is free, needs no account, is already Parquet, has all five tables including traces and is updated daily. BigQuery egress would cost about $200 or more for a year, so it only runs aggregate count checks in the free sandbox. See [data_sources.md](reports/phase0/data_sources.md#summary).

## Phase 0: novelty check and task definition

Expected time: 1 week.

- [x] Search arXiv for 2025 and 2026 papers on pretrained models for token launches or rug pulls. See `reports/phase0/novelty.md`.
- [x] Search for any released weights of a blockchain transaction foundation model. EWE-1-slim is the one relevant release.
- [x] List the downstream tasks (`reports/phase0/tasks_and_datasets.md`):
  - [x] Rug pull at each scoring horizon, strict label (headline)
  - [x] Rug pull at each scoring horizon, broad label (secondary)
  - [x] Honeypot
  - [x] Phishing on B4E, to compare with BERT4ETH: pending Etherscan's permission, dropped if refused or unanswered
  - [x] Wallet type probes: exchange, MEV searcher and bot. The "person" probe is dropped.
- [x] Survey data sources and propose dates (`reports/phase0/data_sources.md`).
- [x] Fill in the fixed decisions table.
- [x] Set up the experiment log in `EXPERIMENTS.md`.

Gate: no published paper already does contribution 1. If one does, rewrite the goal before writing code.

Gate status: passes. The two close papers that kept it provisional were checked, and neither pretrains on token-launch sequences. Hunting in the Dark Forest (WWW 2025) pretrains per transaction. DeFiTrust (2024) is a token-level classifier trained with labels only. See `reports/phase0/novelty.md`.

## Phase 1: data platform

Expected time: 2 to 4 weeks.

- [x] Choose the data source: AWS Public Blockchain Data (`s3://aws-public-blockchain/v1.0/eth/`). BigQuery is a cross-check in the free sandbox only. cryo with a paid RPC fills gaps. Paradigm's portal ends in 2023 and is not usable. See `reports/phase0/data_sources.md`.
- [ ] Stream the AWS daily partitions for the extraction window. Keep only the needed columns and rows, and write a filtered local copy of about 115 to 180 GB of zstd Parquet, as sized in `reports/phase0/data_sources.md`. The raw data stays re-readable from S3.
  - Decode token amounts from `logs`. The AWS `token_transfers.value` and `traces.value` columns are lossy doubles. Use `token_transfers` only as a cross-check.
- [ ] Cross-check daily counts of transactions, logs, Transfer events and creates against BigQuery.
- [ ] Decode events for Uniswap V2 and V3 and their forks:
  - [ ] Pool creation
  - [ ] Swap
  - [ ] Liquidity mint
  - [ ] Liquidity burn
- [ ] Build one event table. Each row is one decoded action.
- [ ] Join USD prices at block time.
- [ ] Attach address context: type, creation block and public labels.
- [ ] Cut three views from the event table:
  - [ ] Wallet sequences
  - [ ] Token sequences, starting at deployment
  - [ ] Contract sequences
- [ ] Store every derived table with its snapshot date.
- [ ] Count total events after merging consecutive repeats.

Gate: the event count is known. The compute plan uses about 1.5 to 2.3 billion events after merging (Phase 0 estimate; Phase 1 measures it). Replace it with the real number.

## Phase 2: labels and baselines

Expected time: 2 weeks.

- [ ] Build the rug-pull labeler from the fixed definitions: the strict label and the broad label.
- [ ] Build the honeypot simulator on a local fork with Foundry's `anvil`.
- [ ] Measure label agreement against manual datasets:
  - [ ] SoK rug-pull incidents, 2,360 cases in the public release (2,391 is the ISSTA 2025 version, which has no release)
  - [ ] RPHunter, 645 tokens: its data cannot be obtained (the link returns HTTP 403), so skip it unless the authors share it
  - [ ] TM-RugPull, 1,000 projects
- [ ] Train the baselines:
  - [ ] XGBoost on the Xia et al. features. No code was released, so reimplement the paper's 40 features.
  - [ ] CoLES GRU from pytorch-lifestream. It needs torch below 2.7, so run it in a separate environment.
  - [ ] BERT4ETH embeddings, through its first author's PyTorch port (the official code is TF1-style and breaks on Python 3.12)
  - [ ] EWE-1-slim frozen embeddings (Apache-2.0, ONNX), pooled per token and per wallet
- [ ] Run each baseline under a random split and a time split. Record the gap.

Gate: labels agree with the manual sets well enough to use. If the time-split gap is large, the benchmark alone is a publishable result.

## Phase 3: tokenizer study

Expected time: 1 week.

- [ ] Implement the field tokens:
  - [ ] Event type
  - [ ] Direction
  - [ ] Amount: log quantile bin plus a sine and cosine embedding
  - [ ] Token and counterparty: hybrid address vocabulary
  - [ ] Method selector
  - [ ] Gas price and gas used
  - [ ] Time gap
  - [ ] Block position and same-block flag
  - [ ] Counterparty context: type, age, degree and label
- [ ] Measure tokens per event.
- [ ] Measure the out-of-vocabulary address rate by month.
- [ ] Measure sequence length distributions for each view.
- [ ] Choose the address vocabulary size. Start at the top one million addresses.

Gate: the tokenizer and vocabulary are frozen.

## Phase 4: small pretraining and objective ablations

Expected time: 2 to 4 weeks.

- [ ] Train the S model, about 10 million parameters, on a data subset.
- [ ] Run one ablation per objective:
  - [ ] Masked event modeling alone
  - [ ] Plus CoLES contrastive loss
  - [ ] Plus next-event head
  - [ ] Plus block-ordering auxiliary labels
- [ ] Compare a bidirectional encoder with a causal variant.
- [ ] Log every run in `EXPERIMENTS.md`.

Gate: the S model beats the CoLES GRU on frozen probes. If it does not, fix the data or the objectives before scaling.

## Phase 5: evaluation protocol

Expected time: 1 week.

- [ ] Run frozen linear probes on every task.
- [ ] Run LoRA fine-tuning on every task.
- [ ] Use at least 5 seeds and test significance.
- [ ] Score entities first seen after the pretraining cutoff on their own.
- [ ] Run the cutoff-leak test:
  - [ ] Encoder A pretrained on data before T2
  - [ ] Encoder B pretrained on data that includes the test period
  - [ ] Report the score difference
  - [ ] Also score EWE-1-slim, an external encoder pretrained without our cutoff rule. Its data covers 2024 to 2025, which overlaps our train launches but ends before our test launches; confirm its exact data cutoff first.

Gate: results hold under the time split and under new-entity scoring.

## Phase 6: scaling

Expected time: a few days of rented GPU compute.

- [ ] Train the M model, about 100 million parameters.
- [ ] Train the L model, about 300 million parameters.
- [ ] Train at three data sizes for at least one model size.
- [ ] Plot pretraining loss against model size and data size.
- [ ] Plot downstream PR-AUC against model size and data size.

Gate: the curves still rise. If they are flat, report that as a finding and do not train larger models.

## Phase 7: multimodal detector

Expected time: 3 to 4 weeks.

- [ ] Add the five encoders:
  - [ ] Transaction sequence: the pretrained model
  - [ ] Wallet graph: directed multigraph GNN with reverse message passing
  - [ ] Contract code: bytecode encoder, SmartBERT when source is verified
  - [ ] Time series: temporal convolution over price, liquidity and holder counts
  - [ ] Tabular: DCNv2 over scanner flags and deployer history
- [ ] Add the fusion transformer with a risk token.
- [ ] Train with modality dropout.
- [ ] Pretrain code and behavior alignment with a contrastive loss.
- [ ] Split by deployer so one deployer's tokens never appear in both train and test.
- [ ] Run label-efficiency curves at 1%, 10% and 100% of labels.
- [ ] Compare with the same detector using a sequence encoder trained from scratch.
- [ ] Remove each modality at test time and record the drop.
- [ ] Test transfer to BSC and Base.

Gate: pretraining helps most at the earliest horizons and for new deployers. If it does not, report that as a negative result.

## Phase 8: release

Expected time: 2 weeks.

- [ ] Publish the benchmark and the label code.
- [ ] Publish the model weights under a clear license.
- [ ] Publish the experiment log.
- [ ] Write the core paper on contributions 1 to 3.
- [ ] Report results per token and per contract only. Publish nothing that links a wallet to a person.

## Open questions

Still undecided after Phase 0. Move each item to the decision log once it is settled.

- **BigQuery sandbox project.** The cross-check needs a dedicated BigQuery project in the free sandbox tier (no billing account). The user creates it. See the cost-cap plan in `reports/phase0/data_sources.md`.
- **Paid archive RPC.** Which provider to use, and whether to pay for one month (about $50 to $360). Phase 2 needs it for `anvil --fork-url`, and it also fills AWS gaps with cryo. Alchemy's terms ban scraping and data mining, so read each provider's terms first.
- **Author data requests.** Whether to email the RPHunter, Xia et al. and Cernera et al. (2023 and 2026) authors for their labeled sets. RPHunter includes Base; Cernera 2026 includes BSC honeypots.
- **AWS data license.** AWS states no license for the data itself. Either email AWS about republishing derived Parquet, or publish only labels, addresses and code that regenerates the data.
- **BSC extraction is deferred to Phase 7.** AWS has no BSC logs or traces. Choose then between Envio HyperSync (needs a free token) and cryo against a paid BSC trace RPC, for the test window only.
- **Etherscan's answer.** The phishing task waits on it (see the decision log).
- **One-day rug task.** `reports/phase0/tasks_and_datasets.md` (task R2) proposes an extra secondary task: the Cernera and Huynh rule, a pool with one mint and one burn where the creator burns 99% or more of the LP tokens. It is not yet accepted.

## Risks to check early

- Labels built from liquidity removal can measure the same behavior as the features. Report label agreement with the manual sets before any headline number.
- Distribution shift between chains and launch platforms can be large. Every cross-chain claim needs its own held-out chain.
- BigQuery bills per byte scanned. Filter every query by date or block number and set a cost cap.
- Most paper figures in the research report come from search snippets. Check the numbers you depend on against the papers.
