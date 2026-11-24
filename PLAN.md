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

## How we run experiments

The project is experiment-led. These rules apply to every phase and every session.

- **Pre-register each gate.** Before a phase's work starts, its gate states a hypothesis, a metric, a pass threshold, and the action on pass and on fail. Each gate below uses that form.
- **Thresholds change only through the decision log.** A change needs a dated entry in the decision log, written before the results it affects are seen. A threshold marked "proposed" is in force until such an entry changes it.
- **Log every run.** Every session that runs anything (a trial, labeling, training or evaluation) adds an entry to `EXPERIMENTS.md` in the same PR. Failed runs count. The manager rejects a PR that runs something without logging it.
- **State the comparison.** Every result names its baseline, its split (the train, validation and test periods in the fixed decisions unless stated otherwise) and its seeds (at least 5, per the fixed decisions). Every metric, and every precision figure in particular, has the label's base rate next to it.
- **Kill ideas cheaply.** Run the cheapest experiment that can kill an idea before building the expensive one. Phase 1.5 is the first example.
- **Report negative results.** A failed gate or a null result goes in `EXPERIMENTS.md` and, where it bears on a contribution, in the paper.

Terms used in the gates:

- **Significant:** a one-sided paired t-test over the 5 seeds at p < 0.05, with a bootstrap 95% interval reported next to it, resampled by deployer so one deployer's tokens move together. When one gate tests several comparisons at once (such as the Phase 4 objective ablations), apply a Holm correction across them.
- **Seed SD:** the standard deviation of a model's PR-AUC across its 5 seeds, measured in the phase the gate names.
- **Finding:** a gate part marked as a finding is measured and reported either way; it does not block the next phase.

The thresholds are proposed round numbers. No published tool reports agreement on these manual sets or effect sizes on these tasks, so the first measurements may show some are too loose or too strict; change them only through the decision log, before the results they affect.

## Where each phase runs

| Phase | Machine |
|---|---|
| 0 to 5, including 1.5 | Mac |
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

Decisions made on 2026-11-24, before any Phase 1 results were seen:

- **The plan is experiment-led.** Added "How we run experiments", rewrote every gate in pre-registered form, and set proposed thresholds for Phases 1 to 8. Reason: the old gates said what to check but not what passes, so the goalposts could move after results.
- **Phase 1.5 (signal check) added.** Reason: the two biggest risks, no signal at 5 or 15 minutes and a rug label that is nearly all positive, were first tested in Phase 2 or later. One month of data can test both before the tokenizer and pretraining are built.

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

Gate (status: **passed**, see [novelty.md](reports/phase0/novelty.md)):

- **Hypothesis:** no published paper or released model pretrains a self-supervised model on token-launch sequences and fine-tunes it for rug pulls or honeypots (contribution 1).
- **Metric:** count of papers or releases found that do contribution 1.
- **Pass threshold:** zero.
- **Pass action:** keep the goal and start Phase 1.
- **Fail action:** rewrite the goal before writing code.
- **Outcome:** pass. The two close papers that kept it provisional were checked, and neither pretrains on token-launch sequences. Hunting in the Dark Forest (WWW 2025) pretrains per transaction. DeFiTrust (2024) is a token-level classifier trained with labels only, per its released code (its full text is paywalled).

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

Gate (thresholds proposed, set 2026-11-24):

- **Hypothesis:** the filtered local copy is complete and correct for the extraction window, and the merged event count is close enough to the Phase 0 estimate of 1.5 to 2.3 billion that the compute plan holds.
- **Metric:** (a) days in the window with no local data; (b) per-day difference against BigQuery in counts of transactions, logs, Transfer events and creates; (c) total events after merging.
- **Pass threshold:** (a) zero missing days after gap-filling; (b) every day within 0.1% of BigQuery on every count; (c) between 0.75 and 4.6 billion (half the low estimate to twice the high one); the measured value is recorded either way.
- **Pass action:** replace the estimate in the compute plan with the measured count and start Phase 2 (once Phase 1.5 has also passed).
- **Fail action:** for (a) or (b), fill or re-extract the failing days with cryo and re-check; do not label or train on days that still fail. For (c) outside the band, redo the compute plan for Phases 4 and 6 before Phase 3, and record the change in the decision log.

Phase 1.5 runs during Phase 1, as soon as its first month is decoded.

## Phase 1.5: signal check

The cheapest experiment that can kill the project's early-detection claim. It runs on one month of data, before the tokenizer or any pretraining.

- [ ] Take the first fully extracted and decoded month (expected 2025-11), plus the first 7 days of the next month so late launches can be labeled.
- [ ] Build rough labels from the fixed definitions, with a 7-day observation window instead of 30 days (rough labels only; Phase 2 builds the real ones):
  - [ ] Strict rug label
  - [ ] Broad rug label
- [ ] At each horizon, drop tokens already rugged before the horizon, and count them separately.
- [ ] Measure each label's base rate, overall and at each horizon after the drop.
- [ ] Build simple hand-built features at each horizon (5, 15 and 60 minutes, 500 transfers, 24 hours), computed only from events before the horizon. For example: swap, buyer and seller counts; buy and sell volume; liquidity added; time from deployment to first liquidity; deployer age, balance and prior launches; deployer and top-10 holder shares; whether LP tokens were burned or sent to a lock contract. Deployer history before 2025-11-01 is not in the local copy, so deployer features are truncated in the first month; read them from S3 for this check, or note the truncation in the log.
- [ ] Time split within the month: train on launches from days 1 to 16, purge days 17 to 23 (the purge matches the 7-day label window, so train labels end before test launches start; the full benchmark keeps the 30-day embargo), test on launches from day 24 to the month's end.
- [ ] Train LightGBM with 5 seeds for each label and horizon.
- [ ] Record PR-AUC and precision at the top 1% of daily launches against the base rate, with bootstrap 95% intervals, in `EXPERIMENTS.md`.

Gate (thresholds proposed, set 2026-11-24):

- **Hypothesis:** (a) hand-built features carry usable signal for the strict label at 15 minutes; (b) the strict label is neither nearly all positive nor too rare to learn.
- **Metric:** on the test days, for the strict label at 15 minutes: PR-AUC, precision at the top 1% of daily launches, and the base rate *b* of the same test tokens (after the horizon drop). For (b): the strict label's 7-day base rate *b*₀ among all launches in the month (before the horizon drop).
- **Pass threshold:**
  - (a) mean PR-AUC at least 1.5 × *b*, with the bootstrap lower bound above *b*; and mean precision at the top 1% at least min(2*b*, *b* + (1 − *b*)/2). For example, *b* = 10% needs PR-AUC ≥ 0.15 and precision ≥ 20%; *b* = 40% needs PR-AUC ≥ 0.60 and precision ≥ 70%.
  - (b) *b*₀ between 5% and 50%. Xia et al. labeled about 50% of 2020 Uniswap V2 tokens as scams with a broad definition, so the strict label should fall below that; below 5%, a week of launches holds too few positives to learn from. The 7-day rate is a lower bound on the 30-day rate, so a value near 50% already warns that Phase 2's 30-day label may leave the band.
  - Inconclusive if the test days have fewer than 100 strict positives at 15 minutes: add the next month and rerun before deciding.
- **Pass action:** continue to Phase 2 once the Phase 1 gate has also passed, with all five horizons. Apply the same test to every other horizon and record the results; if 5 minutes alone fails, keep it as a secondary horizon and say so in the paper.
- **Fail action:**
  - (b) fails: revise the strict label (above 50%: tighten the liquidity-removal share or the linked-wallet rule; below 5%: check the linking heuristic for misses), log the revision in the decision log, and rerun this check.
  - (a) fails but the same test passes at 60 minutes: drop 5 and 15 minutes from the headline (5 minutes is also tested and recorded, for the paper), record the change in the decision log, and continue.
  - (a) fails at 60 minutes too, with (b) passing: do not start Phase 2. Inspect the labels against a sample of tokens by hand, revise them or the features, and rerun. If a second run also fails, write up the no-signal result and decide in the decision log whether to continue with the benchmark and leak contributions only.

Also record the broad label's 7-day base rate (a finding). If it is above 80%, the broad label is near-trivial for precision at the top 1%; propose dropping or tightening it in the decision log before Phase 2.

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

The manual sets predate the extraction window (Trapdoor covers 2020 to 2023), so the agreement check runs the labelers on those tokens' own history, read from S3 or an archive RPC.

Gate (thresholds proposed, set 2026-11-24):

- **Hypothesis:** (a) the strict rug label matches manual rug-pull labels; (b) the honeypot simulator matches manual honeypot labels; (c) baselines score higher under a random split than under the time split, so the leakage-free benchmark matters.
- **Metric:**
  - (a) strict-label F1 on the Ethereum rows of TM-RugPull (599 rug pulls, 401 normal across all chains; 633 projects on Ethereum, whose class split is recorded first), with recall on its rug pulls and the false-positive rate on its normals; recall on the SoK rows typed as liquidity rugs.
  - (b) honeypot recall on Trapdoor's 1,859 manual trapdoor tokens, the false-positive rate on its non-malicious list, and F1 (recorded).
  - (c) for each baseline, random-split PR-AUC minus time-split PR-AUC on the strict label at 15 minutes, over 5 seeds.
  - The strict label's base rate on the full train period, with the 30-day window.
- **Pass threshold:**
  - (a) F1 ≥ 0.80, with the false-positive rate on TM-RugPull normals ≤ 5% (those normals are audited, well-known projects, so they should be easy); SoK liquidity-rug recall ≥ 0.70.
  - (b) recall ≥ 0.85 and false-positive rate ≤ 5%.
  - The strict base rate stays between 5% and 50%, the Phase 1.5 band.
  - (c) is a finding. A gap of at least 0.05 PR-AUC that is significant counts as large.
  - The manual sets are easier than live launches (TM-RugPull's normals are well-known projects), so passing agreement is necessary, not sufficient; report it as an upper bound on label quality.
- **Pass action:** freeze the labelers, record the label version in `EXPERIMENTS.md`, and start Phase 3. If (c) is large, the benchmark alone is a publishable result; note it in the paper outline.
- **Fail action:** for (a) or (b), inspect the disagreeing tokens, revise the labeler, log the revision in the decision log, and rerun. After two failed revisions, demote the failing label to a secondary task, report its agreement as a limitation, and decide the headline label in the decision log before Phase 3.

Also record, as the baseline numbers later phases must beat: the LightGBM hand-built-feature model from Phase 1.5, retrained on the full train period, and each baseline's seed SD. The Phase 4 threshold uses the CoLES GRU's seed SD.

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

Gate (thresholds proposed, set 2026-11-24):

- **Hypothesis:** the tokenizer covers the data without drifting badly between train and test, and fits sequences in a context the S model can afford.
- **Metric:** (a) out-of-vocabulary rate for counterparty addresses, by event, in each month (a launch's own token address is excluded, since every new token is out of vocabulary by design); (b) rise in that rate from the train period to the test period; (c) share of token sequences truncated by the chosen context length at the 60-minute horizon; (d) tokens per event.
- **Pass threshold:** (a) ≤ 20% in every test month; (b) ≤ 5 percentage points; (c) ≤ 5%; (d) recorded, and the S model's compute estimate updated with it.
- **Pass action:** freeze the tokenizer and vocabulary, record their version, and start Phase 4.
- **Fail action:** for (a) or (b), grow the vocabulary or move more counterparties to the hashed or context-feature path, and remeasure. For (c), raise the context length or merge more event types, and update the compute plan. Log each change in the decision log.

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

Gate (thresholds proposed, set 2026-11-24):

- **Hypothesis:** the S model's pretrained embeddings carry more rug-pull signal than the CoLES GRU's.
- **Metric:** frozen linear-probe PR-AUC on the strict rug label at 15 minutes, on the validation period, 5 probe seeds each. Probe seeds miss pretraining variance, so the S model is pretrained twice with different seeds and each run is probed. Also recorded: the same at every other horizon and for honeypots, and the gap to the Phase 2 LightGBM baseline.
- **Pass threshold:** for both S pretraining runs, mean PR-AUC beats the CoLES GRU's by at least the Phase 4 margin, max(0.02, 2 × the CoLES GRU's seed SD from Phase 2), and the difference is significant. Each objective in the ablation stays only if it adds at least 0.01 PR-AUC, significantly after the Holm correction; otherwise drop it for simplicity. The difference between the two S runs' mean PR-AUC is recorded as the S pretraining spread, which Phase 6 uses.
- **Pass action:** keep the best objective set and start Phase 5.
- **Fail action:** do not scale. Fix the data or the objectives and rerun, logging each round. After two failed rounds, write up the negative result, and decide in the decision log whether to continue with contributions 2 and 3 only.

The gap to LightGBM is not a gate here, since Relvas and Bernardo (2611.18914) and MELT (2602.13480) find frozen sequence embeddings rarely beat it. It is the bar for Phase 7.

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

Gate (thresholds proposed, set 2026-11-24):

- **Hypothesis:** (a) the Phase 4 result holds on the test period; (b) it holds for entities first seen after the pretraining cutoff; (c) pretraining on data from the test period inflates scores (the cutoff-leak test for contribution 3).
- **Metric:** strict rug label at 15 minutes on the test period, 5 seeds, for both frozen probes and LoRA:
  - (a) S model PR-AUC minus CoLES GRU PR-AUC on all test tokens;
  - (b) the same difference on tokens whose deployer was first seen after the cutoff;
  - (c) Encoder B PR-AUC minus Encoder A PR-AUC, and the same for precision at the top 1%. EWE-1-slim is scored alongside and reported, not gated.
- **Pass threshold:**
  - (a) the difference meets the Phase 4 margin and is significant.
  - (b) the difference is positive, at least half of its size in (a), and significant.
  - (c) is a finding. Leakage is **material** if B beats A in PR-AUC by at least the leak margin, max(0.01, 2 × Encoder A's seed SD from this phase), and the difference is significant. The precision-at-1% difference is reported next to it with the base rate, not gated.
- **Pass action:** start Phase 6.
- **Fail action:** if (a) fails, the Phase 4 result was a validation-period effect; report it, and revisit Phase 4 before scaling. If only (b) fails, scale anyway but report that the gain does not reach new deployers; Phase 7's new-deployer test then becomes the main question.
- **Either outcome of (c)** is reported for contribution 3: material leakage supports the cutoff rule as a headline finding; no material leakage is reported as a negative result, and the rule is kept as cheap insurance.

## Phase 6: scaling

Expected time: a few days of rented GPU compute.

- [ ] Train the M model, about 100 million parameters.
- [ ] Train the L model, about 300 million parameters.
- [ ] Train at three data sizes for at least one model size.
- [ ] Plot pretraining loss against model size and data size.
- [ ] Plot downstream PR-AUC against model size and data size.

Gate (thresholds proposed, set 2026-11-24):

- **Hypothesis:** downstream performance still improves with model size or data size at the largest point trained.
- **Metric:** frozen-probe PR-AUC on the strict rug label at 15 minutes, validation period, 5 probe seeds per pretrained model (one pretraining run per size, for cost). Pretraining loss is plotted but not gated.
- **Pass threshold:** "the curves still rise" means the last step on at least one axis (L over M for model size, or the largest data size over the next for data size) gains at least the scaling margin, significantly. The scaling margin is max(0.01, 2 × the larger model's seed SD from this phase, the S pretraining spread from Phase 4), so it covers pretraining noise as well as probe noise. It is fixed by this rule now and needs no later decision.
- **Pass action:** use the largest model in Phase 7, and note in the paper that scaling has not saturated.
- **Fail action:** report the flat curves as a finding, do not train larger models, and use the smallest model within the scaling margin of the best in Phase 7.

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

Gate (thresholds proposed, set 2026-11-24):

- **Hypothesis:** pretraining helps the detector most at the earliest horizons and for new deployers, and the detector beats the LightGBM baseline.
- **Metric:** on the test period, split by deployer, strict rug label, 5 seeds:
  - (a) lift = PR-AUC of the detector with the pretrained sequence encoder minus the same detector with that encoder trained from scratch, at 5 and 15 minutes, with the matching lift in precision at the top 1%;
  - (b) the same lift at 24 hours;
  - (c) the same lift on tokens from deployers first seen after the cutoff;
  - (d) detector PR-AUC minus the Phase 2 LightGBM baseline at 15 minutes;
  - (e) the lift at 1% of labels.
- **Pass threshold:**
  - The Phase 7 margin is max(0.02, the scaling margin from Phase 6).
  - (a) PR-AUC lift of at least the Phase 7 margin, significant, at both 5 and 15 minutes; the precision-at-1% lift is reported next to it with the base rate.
  - (b) the 5- and 15-minute lifts are each at least the 24-hour lift. The paper says pretraining helps *most* early only if the paired difference is also significant; otherwise it says "at least as much".
  - (c) lift of at least the Phase 7 margin, significant;
  - (d) at least the Phase 7 margin, significant;
  - (e) is a finding; a lift of at least 0.05 supports the label-efficiency claim.
- **Pass action:** these are the headline results; start Phase 8.
- **Fail action:** report each failed part as a negative result. If (a), (b) or (c) fails, the paper does not make the matching claim (helps early detection, helps most early, helps new deployers); if (a) and (c) both fail, it leads with contributions 2 and 3. If (d) fails, the paper reports that LightGBM remains the bar, in line with Relvas and Bernardo (2611.18914) and MELT (2602.13480).

## Phase 8: release

Expected time: 2 weeks.

- [ ] Publish the benchmark and the label code.
- [ ] Publish the model weights under a clear license.
- [ ] Publish the experiment log.
- [ ] Write the core paper on contributions 1 to 3.
- [ ] Report results per token and per contract only. Publish nothing that links a wallet to a person.

Gate (thresholds proposed, set 2026-11-24):

- **Hypothesis:** the released code, labels and weights reproduce the paper's headline numbers, and the release exposes no wallet-to-person links.
- **Metric:** (a) difference between each headline number and the same number rerun from a clean checkout of the release; (b) count of released fields or files that link a wallet to a person.
- **Pass threshold:** (a) every headline number within one seed standard deviation of the paper's value (or exact, for deterministic numbers such as base rates and label counts); (b) zero.
- **Pass action:** publish.
- **Fail action:** fix the release, or correct the paper's numbers, and rerun the check before publishing.

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
- The strict rug label may be nearly all positive, and there may be no signal at 5 or 15 minutes. Phase 1.5 tests both on one month of data.
- Distribution shift between chains and launch platforms can be large. Every cross-chain claim needs its own held-out chain.
- BigQuery bills per byte scanned. Filter every query by date or block number and set a cost cap.
- Most paper figures in the research report come from search snippets. Check the numbers you depend on against the papers.
