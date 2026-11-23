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
| Pretraining data window | |
| Pretraining cutoff date | |
| Train period ends (T1) | |
| Validation period ends (T2) | |
| Embargo between periods | 30 days |
| Scoring horizons | 5, 15 and 60 minutes after first liquidity; 500 transfers; 24 hours |
| Rug-pull label | Linked wallets remove 80% or more of pool liquidity, or price falls 90% or more, within 30 days |
| Honeypot label | Sells by unrelated wallets fail after the observation time |
| Headline metric | Precision at the top 1% of daily launches, plus PR-AUC |
| Minimum seeds per result | 5 |

The label thresholds are design choices. Phase 2 tests them against the manual datasets.

## Phase 0: novelty check and task definition

Expected time: 1 week.

- [ ] Search arXiv for 2025 and 2026 papers on pretrained models for token launches or rug pulls.
- [ ] Search for any released weights of a blockchain transaction foundation model.
- [ ] List the downstream tasks:
  - [ ] Rug pull at each scoring horizon
  - [ ] Honeypot
  - [ ] Phishing on B4E, to compare with BERT4ETH
  - [ ] Wallet type probes, such as exchange, bot, MEV searcher and person
- [ ] Fill in the fixed decisions table.
- [ ] Set up the experiment log in `EXPERIMENTS.md`.

Gate: no published paper already does contribution 1. If one does, rewrite the goal before writing code.

## Phase 1: data platform

Expected time: 2 to 4 weeks.

- [ ] Choose the data source: BigQuery `crypto_ethereum`, Paradigm's data portal, or cryo with an RPC provider.
- [ ] Extract one year of blocks, transactions, logs, traces and token transfers to Parquet.
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

Gate: the event count is known. Replace the 20 billion estimate in the compute plan with the real number.

## Phase 2: labels and baselines

Expected time: 2 weeks.

- [ ] Build the rug-pull labeler from the fixed definition.
- [ ] Build the honeypot simulator on a local fork with Foundry's `anvil`.
- [ ] Measure label agreement against manual datasets:
  - [ ] SoK rug-pull incidents, 2,391 validated cases
  - [ ] RPHunter, 645 tokens
  - [ ] TM-RugPull, 1,000 projects
- [ ] Train the baselines:
  - [ ] XGBoost on the Xia et al. features
  - [ ] CoLES GRU from pytorch-lifestream
  - [ ] BERT4ETH embeddings from its public code
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

## Risks to check early

- Labels built from liquidity removal can measure the same behavior as the features. Report label agreement with the manual sets before any headline number.
- Distribution shift between chains and launch platforms can be large. Every cross-chain claim needs its own held-out chain.
- BigQuery bills per byte scanned. Filter every query by date or block number and set a cost cap.
- Most paper figures in the research report come from search snippets. Check the numbers you depend on against the papers.
