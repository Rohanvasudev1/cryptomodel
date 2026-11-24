# Phase 0 novelty check

Date: 2026-11-24. Scope: work from 2024 to 2026, plus older papers that later work builds on.

## Summary

- **Contribution 1 (token-launch foundation model): novel.** No paper pretrains a self-supervised model on unlabeled token-launch sequences and fine-tunes it for rug pulls or honeypots. Several papers come close. TokenScout (CCS 2024) scores the first 500 transfers of ERC-20 tokens with a temporal GNN, but it trains with labels. BlockScan, BERT4ETH and its successors, and EWE-1 pretrain on transactions, accounts or wallets, not on token launches.
- **Contribution 2 (leakage-free benchmark): partly covered.** Since 2026, Solana papers use chronological splits, embargoes and minute-level cutoffs. Early Rug Pull Detection on Solana (2611.13342) is the closest. No benchmark covers EVM chains, honeypots, multiple fixed horizons (5, 15 and 60 minutes, 500 transfers, 24 hours) and a ranking metric at once.
- **Contribution 3 (pretraining-cutoff rule): partly covered.** The idea is established for LLMs (Time Machine GPT, DatedGPT), and time-series foundation-model papers raise it. No paper measures it for transaction or event-sequence foundation models, on-chain or off.
- **Released weights:** one blockchain transaction foundation model has public weights: EWE-1 (Apache-2.0, Ethereum wallets, trained on all 2024–2025 transactions). BlockScan links a code and model repo. BERT4ETH-line models release code only.
- **Phase 0 gate: pass.** No published paper does contribution 1.

## Method

Searches ran from 2026-11-24 through a general web search engine, with queries aimed at arXiv, Semantic Scholar, Google Scholar, OpenReview, the ACM Digital Library and IEEE venues. Queries covered: pretrained or self-supervised blockchain transaction models; BERT4ETH successors; CoLES on wallets; token-launch, rug-pull, honeypot and memecoin detection; early detection after launch; time-split blockchain benchmarks; pretraining-cutoff leakage in foundation models; and released weights on Hugging Face.

"Opened" means the abstract page and, where noted, the full text were read by this session or a fetch subagent. "Snippet" means only search results were seen.

Limits:

- The ACM DL and ScienceDirect returned HTTP 403, so ACM-only and Elsevier-only papers were judged from other copies or from snippets. TokenScout was read from the authors' PDF.
- Google Scholar and OpenReview were not queried through their own search pages. Coverage of those comes through the web search engine.
- Several abstract-page answers rest on partly truncated HTML. Each entry says so where it matters.
- Workshop papers that are not on arXiv are likely under-covered.

## Overlap key

For each paper, C1, C2 and C3 refer to the three contributions. Overlap is **none**, **partial** or **overlapping**.

## 1. Pretrained or self-supervised models over blockchain data

### TokenScout: Early Detection of Ethereum Scam Tokens via Temporal Graph Learning — opened (full PDF)

- Authors: Cong Wu, Jing Chen, Ziming Zhao, Kun He, Guowen Xu, Yueming Wu, Haijun Wang, Hongwei Li, Yang Liu, Yang Xiang
- Venue: ACM CCS 2024, October 2024. DOI [10.1145/3658644.3690234](https://doi.org/10.1145/3658644.3690234). [Authors' PDF](https://wu-yueming.github.io/Files/CCS2024_TokenScout.pdf)
- What it does: models the earliest 500 transfers of each ERC-20 token as a temporal attributed multigraph and learns it with a temporal GNN. A *supervised* contrastive refiner then classifies the token as rug pull, honeypot, Ponzi or trustworthy. Data: 214,084 tokens from 2015 to February 2023, labeled by auditors over about 800 hours. The split is a random 70/15/15. A forward deployment ran from March to May 2023. The paper says it did not evaluate accuracy at different stages of a token's life.
- C1 **partial**: it learns token-level representations from early transfers, but with labels and no unlabeled pretraining.
- C2 **partial**: it uses a 500-transfer window, the same as one of our horizons, but scores from a random split, uses no other fixed horizons, and its 2023 forward test is a deployment, not a benchmark.
- C3 **none**.

### BlockScan (first released as BlockFound): Detecting Anomalies in Blockchain Transactions — opened (abstract and partial full text)

- Authors: Jiahao Yu, Xian Wu, Hao Liu, Wenbo Guo, Xinyu Xing
- arXiv [2410.04039](https://arxiv.org/abs/2410.04039). v1 October 2024, v5 October 2025. The search snippet said NeurIPS 2025, but the arXiv page lists no venue.
- What it does: a RoBERTa-style masked-LM transformer pretrained on benign Ethereum transactions (Oct 2020 to Apr 2023) and Solana transactions (Sep to Dec 2023). The unit is one transaction. Anomalies are flagged by reconstruction error. Splits are sequential by block time, per application. Code, model and data are linked at [github.com/nuwuxian/tx_fm](https://github.com/nuwuxian/tx_fm) (repo not opened).
- C1 **partial**: a self-supervised transaction foundation model, but per transaction, for DeFi attacks, with no token-launch task.
- C2 **none**.
- C3 **none**: it uses time-ordered splits but does not measure cutoff leakage.

### EWE-1 (Ethereum Wallet Embeddings), Sistema Labs — opened (Hugging Face model card)

- Link: [huggingface.co/sistemalabs/EWE-1-slim-large](https://huggingface.co/sistemalabs/EWE-1-slim-large). Inference code at [github.com/0xideas/ewe-1-inference](https://github.com/0xideas/ewe-1-inference) (not opened). No paper.
- What it does: a 488M-parameter causal transformer (24 layers, 1536-dimensional embeddings) trained with next-step prediction on about 1.1B Ethereum mainnet transactions from 2024 and 2025. Each transaction has 31 features and the window is 64 transactions per wallet. It is Apache-2.0 and ships in ONNX format. The exact weight filenames were not checked. Intended uses: phishing, malicious contracts and Sybils. The card gives no benchmark results.
- C1 **partial**: a released Ethereum foundation model, but over wallets, with no token-launch or scam-token evaluation.
- C2 **none**.
- C3 **none**, but it matters for C3: its pretraining window covers all of 2024–2025. Any downstream test in that period would leak, so it can serve as a natural "leaky" baseline.

### Hunting in the Dark Forest: A Pre-trained Model for On-chain Attack Transaction Detection in Web3 — opened (aggregator summary only)

- Authors: Zhiying Wu, Jiajing Wu, Hui Zhang, Zibin Zheng, Weiqiang Wang
- Venue: The Web Conference (WWW) 2025. Read via [chatpaper.com/paper/130086](https://chatpaper.com/paper/130086). [OpenReview forum](https://openreview.net/forum?id=vo7EHT3iBs) (not opened).
- What it does: pretrains a transaction encoder by reconstruction, weakly supervised by function comments, then detects attack transactions with few or no labels. Reports finding 1,692 address-poisoning attacks.
- C1 **partial**: pretrained on unlabeled transactions, but per transaction, for attacks, not token launches.
- C2 **none**. C3 **none**.

### KGBERT4Eth — opened (abstract and partial full text)

- Authors: Yifan Jia, Ye Tian, Liguo Zhang, Yanbin Wang, Jianguo Sun, Liangliang Song
- arXiv [2509.03860](https://arxiv.org/abs/2509.03860), September 2025, submitted to an IEEE venue.
- What it does: account-level BERT pretraining (BM25-biased masking plus knowledge-graph link prediction) on about 3.25M Ethereum transactions. Tasks are phishing and de-anonymization. The split is a random 70/10/20.
- C1 **partial**: account-level pretraining, no token task. C2 **none**. C3 **none**.

### LMAE4Eth — opened (abstract and partial full text)

- Authors: Yifan Jia, Yanbin Wang, Jianguo Sun, Ye Tian, Peng Qian
- arXiv [2509.03939](https://arxiv.org/abs/2509.03939), September 2025.
- What it does: a transaction-token contrastive language model plus a masked graph autoencoder, over Ethereum accounts, for phishing and fraud. Splits are random or connected-component, not time-based.
- C1 **partial**: account-level, no token task. C2 **none**. C3 **none**.

### Older and adjacent work in this group — snippet only

| Paper | Link | What it does | C1 | C2 | C3 |
|---|---|---|---|---|---|
| BERT4ETH (Hu et al., WWW 2023) | [2303.18138](https://arxiv.org/abs/2303.18138) | Account-level masked transformer, phishing and de-anonymization; the base the plan builds on | partial: account-level | none | none |
| ZipZap (WWW 2024) | [doi 10.1145/3589334.3645352](https://doi.org/10.1145/3589334.3645352) | Efficiency successor to BERT4ETH | partial: account-level | none | none |
| TLMG4Eth (2024, IEEE TIFS 2025) | [2409.07494](https://arxiv.org/abs/2409.07494) | Transaction language model plus graph, fraud detection | partial: account-level | none | none |
| IGT4ETH (AAAI 2026) | [AAAI proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/39536/43497) | Ethereum account classification with contrastive pretraining | partial: account-level | none | none |
| DeFiTrust (Expert Systems with Applications, 2024) | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0957417424007796) (403) | Supervised transformer over token event logs plus social sentiment, classifies scam tokens | partial: sequences of token events, but supervised and no pretraining | none known | none |
| Blockchain Large Language Models / BlockGPT (Gai et al., 2023) | [2304.12749](https://arxiv.org/abs/2304.12749) | GPT-style model over transaction traces for attack detection | partial: per-transaction | none | none |
| TRM Labs Blockchain Foundation Model (blog) | [trmlabs.com](https://www.trmlabs.com/trm-tech-blog/foundation-models-for-blockchain-intelligence-in-the-ai-arms-race) | Proprietary address-behavior foundation model, no paper or weights | partial: address-level, closed | none | none |

### Off-chain transaction foundation models (context for the plan's sources)

| Paper | Link | Status | Note | C1 | C2 | C3 |
|---|---|---|---|---|---|---|
| TREASURE (Yeh et al., Visa; KDD 2026) | [2511.19693](https://arxiv.org/abs/2511.19693) | opened | Decoder-only model over about 6B card transactions, time-based train/val/test, no weights | none: not blockchain | none | none |
| How Much Do Foundation Models Add to Gradient Boosting on Financial Event Sequences? (Relvas, Bernardo; Nov 2026) | [2611.18914](https://arxiv.org/abs/2611.18914) | opened | Frozen self-supervised embeddings rarely beat LightGBM. Finds point-in-time and test-period leakage in public AML and fraud benchmarks. Code public | none | partial: shows leakage in public transaction benchmarks, not crypto | partial: leakage in evaluation, but not from the pretraining cutoff |
| Towards a Foundation Purchasing Model (2024) | [2401.01641](https://arxiv.org/abs/2401.01641) | snippet | Generative pretraining on card transactions | none | none | none |

## 2. Rug-pull and scam-token benchmarks with time splits or fixed horizons

### Early Rug Pull Detection on Solana — opened (abstract and full text)

- Authors: Saba Heydaridoost, Kasra Kashani, Mohammad Mowlavi Sorond, Behnam Bahrak
- arXiv [2611.13342](https://arxiv.org/abs/2611.13342), 9 November 2026.
- What it does: on SolRPDS tokens, compares GNNs on transfer graphs (GCN, GraphSAGE, GAT) with XGBoost, FT-Transformer and AutoInt. The split is chronological 70/15/15 by creation time, with a label-availability embargo. It reports that a random split scores higher. Cutoffs are 12.5, 35.5 and 93 minutes, set at lifespan quartiles. Code and features are at [github.com/Saba-Heydaridoost/rugpull_detector](https://github.com/Saba-Heydaridoost/rugpull_detector).
- C1 **none**: supervised, no pretraining.
- C2 **overlapping** on method: a time split, an embargo and fixed minute-level cutoffs. It differs from ours in chain (Solana), in horizons set by quartiles rather than fixed clock times, in having no honeypot label and no ranking metric.
- C3 **none**.

### MELT: A Behavioral Trace Dataset for High-Risk Memecoin Launch Detection (v1 titled "MemeTrans") — opened (abstract and v2 full text)

- Authors: Sihao Hu, Selim Furkan Tekin, Yichang Xu, Ling Liu
- arXiv [2602.13480](https://arxiv.org/abs/2602.13480). v1 February 2026, v2 May 2026. Code and data at [github.com/git-disl/MELT](https://github.com/git-disl/MELT).
- What it does: about 41k Pump.fun launches that migrated to a DEX (December 2024 to March 2025), with 122 pre-migration features. The split is chronological 7:3. Supervised baselines include a transformer, LSTM, GRU and TCN on per-token time series, and a tabular MLP wins. Labels use a 20-minute window after migration.
- C1 **partial**: sequence models over launch traces, but supervised and with no pretraining. It also reports that transformers underperform on these short, noisy sequences, which is a risk for us.
- C2 **partial**: a time split with features from before migration only. It scores at migration, not at fixed times after first liquidity, and covers Solana only.
- C3 **none**.

### Catching the Rug: Early Prediction of Fraudulent Memecoins on Solana via Machine Learning — opened (abstract and partial full text)

- Authors: Jianghai Li, Pavel Kuznetsov, Yury Yanovich, Konstantin Nott-Whaley, Igor Vodolazov (the HTML also lists Pattapon Tanankakorn)
- arXiv [2608.20271](https://arxiv.org/abs/2608.20271). v1 August 2026, v2 November 2026.
- What it does: tabular models (XGBoost wins) on features from the first 5 minutes of Pump.fun and Raydium tokens, predicting the outcome at 1 hour. It describes forward rolling-window cross-validation by issue time. Whether the reported results follow it could not be fully confirmed.
- C1 **none**.
- C2 **partial**: one fixed horizon (5 minutes), a forward split, Solana only.
- C3 **none**.

### TM-RugPull: A Temporally Sound Multimodal Dataset for Early RugPull Detection — opened (abstract and full text)

- Authors: Fatemeh Shoaei, Mohammad Pishdar, Mozafar Bag-Mohammadi, Mojtaba Karami, Bert Lagaisse
- arXiv [2602.21529](https://arxiv.org/abs/2602.21529). February 2026, v3 May 2026. Presented as a poster. Data at [github.com/mohamadpishdar/RugPull-Defender](https://github.com/mohamadpishdar/RugPull-Defender).
- What it does: a multichain dataset (Ethereum, BSC, Polygon, Arbitrum, Fantom). Features come from before a per-project midpoint and labels from a 72-hour window. Its main claim is avoiding post-collapse signals. There is no train/test split and no fixed horizons.
- C1 **none**.
- C2 **partial**: it makes the same leakage argument on EVM chains, but defines no time split and no scoring horizons.
- C3 **none**.

### Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain — opened (abstract and full text)

- Authors: Dmitry Yaremus, Jianghai Li, Alisa Kalacheva, Igor Vodolazov, Yury Yanovich
- arXiv [2509.01168](https://arxiv.org/abs/2509.01168), September 2025.
- What it does: gradient boosting on features from the first 5 minutes of TON DEX pools, with labels within 1 hour. The split is a stratified random 8:2.
- C1 **none**. C2 **partial**: a fixed early horizon, but a random split. C3 **none**.

### From Viral to Void: Multi-Dimensional Behavioral and Contractual Analysis for Rug Pull Identification — opened (abstract and full text)

- Authors: Jinyin Song, Hongping Wang, Xiaoqi Li
- arXiv [2608.01609](https://arxiv.org/abs/2608.01609), August 2026.
- What it does: an MLP on 11 hand-built features, with a random 7:1:2 split. Some features may use outcomes after launch.
- C1 **none**. C2 **none**: its random split is the leakage our benchmark guards against. C3 **none**.

### ETH-TraceBench: A Large-Scale Event-Stream Benchmark for Ethereum DeFi under Temporal, Protocol, and Contract Shift — opened (abstract and partial full text)

- Authors: Kemal Kirtac, Carsten Maple
- arXiv [2609.23659](https://arxiv.org/abs/2609.23659), September 2026, under review at TMLR.
- What it does: Ethereum receipt-log event streams for swap classification and liquidation detection. Train 2021–2024, validate January–June 2025, test July–December 2025, with protocol and pool novelty holdouts. It explicitly uses no unlabeled pretraining.
- C1 **none**.
- C2 **partial**: a forward time split on Ethereum event streams, but no scam, rug-pull or token-launch task.
- C3 **none**.

### Other scam-token and launch work — snippet only

| Paper | Link | Note | C1 | C2 | C3 |
|---|---|---|---|---|---|
| Pump-and-Dump meets Honeypot Tokens: Telegram Bait-and-Trap Schemes (2026) | [2610.10149](https://arxiv.org/abs/2610.10149) | Labels honeypots by simulating buy, approve and sell; useful for our honeypot label | none | partial: honeypot labeling | none |
| Why Trick Me: The Honeypot Traps on Decentralized Exchanges (2023) | [2309.13501](https://arxiv.org/abs/2309.13501) | Uniswap honeypot detection by simulation | none | none | none |
| Predicting the success of new crypto-tokens on Pump.fun (2026) | [2602.14860](https://arxiv.org/abs/2602.14860) | Early-trading signals for token success | none | partial: early window | none |
| MemeChain: multimodal cross-chain meme-coin dataset (2026) | [2601.22185](https://arxiv.org/abs/2601.22185) | Cross-chain meme-coin forensics dataset | none | partial: dataset | none |
| SoK: DeFi Rug Pulls: Types, Dataset, and Tool Assessment (2025) | [doi 10.1145/3728900](https://doi.org/10.1145/3728900) | Rug-pull taxonomy and tool comparison | none | partial: dataset | none |
| Characterizing Transfer Graphs of Suspicious ERC-20 Tokens (Josenhans et al., 2025) | [2501.11668](https://arxiv.org/abs/2501.11668) (abstract opened) | Per-token transfer graphs, simple classifier, about 88.7% accuracy | none | none | none |
| Do not rug on me (Mazorra et al., 2022) | [2201.07220](https://arxiv.org/abs/2201.07220) | FT-Transformer on tabular Uniswap features | none | none | none |
| Trade or Trick? Scam tokens on Uniswap (Xia et al., 2021) | [2109.00229](https://arxiv.org/abs/2109.00229) | Feature-based scam-token classifier | none | none | none |
| FinSurvival (WWW Companion 2026) | snippet only | Aave v3 time-to-event benchmark with temporal splits | none | partial: time splits, DeFi lending | none |

## 3. Leakage from the pretraining cutoff

| Paper | Link | Status | What it shows | C1 | C2 | C3 |
|---|---|---|---|---|---|---|
| DatedGPT: Preventing Lookahead Bias in LLMs with Time-Aware Pretraining (Yan, Tang, Gao, Jiang, Lu; March 2026) | [2603.11838](https://arxiv.org/abs/2603.11838) | opened (abstract) | Twelve 1.3B LLMs with annual cutoffs from 2013 to 2024. Models that see the future earn a measurable "lookahead premium" (26.4 basis points per standard deviation) in return prediction | none | none | **partial**: measures cutoff leakage, but for text LLMs and with no rule for choosing the cutoff |
| Time Machine GPT (Drinkall, Rahimikia, Pierrehumbert, Zohren; NAACL Findings 2024) | [2404.18543](https://arxiv.org/abs/2404.18543) | opened (abstract) | Point-in-time LLMs for backtesting | none | none | **partial**: same idea for text, no measured size in the abstract |
| Rethinking Evaluation in the Era of Time Series Foundation Models: (Un)known Information Leakage Challenges (Meyer, Kaltenpoth, Zalipski, Müller; Oct 2025) | [2510.13654](https://arxiv.org/abs/2510.13654) | opened (abstract) | Position paper on train/test overlap and temporal overlap in time-series foundation-model evaluation | none | none | **partial**: names the problem, proposes no rule |
| Rethinking Multimodal Time-Series Forecasting Evaluation / TimesX (Liu, Zhou, Sen, Prakash, Das; ICML 2026) | [2607.06973](https://arxiv.org/abs/2607.06973) | opened (abstract) | Recommends evaluating after a model's knowledge cutoff | none | none | partial |
| SkinAdvisor (Fan et al.; AAAI 2027 IAAI; Nov 2026) | [2611.15023](https://arxiv.org/abs/2611.15023) | opened (abstract) | Pretrained embeddings leak temporal information into a downstream forecast, so it splits by season | none | none | **partial**: the closest example of leakage through a frozen encoder, but a single anecdote in game sales |
| GIFT-Eval (2024) | [2410.10393](https://arxiv.org/abs/2410.10393) | snippet | Overlap between pretraining and test data inflates time-series foundation-model scores | none | none | partial |

No paper found measures cutoff leakage for a transaction, event-sequence or blockchain foundation model, or proposes a rule for choosing the cutoff from the downstream test periods.

## 4. Released weights for blockchain transaction foundation models

| Model | Weights | Data | Note |
|---|---|---|---|
| EWE-1 (Sistema Labs) | **Yes**: Hugging Face, Apache-2.0, ONNX | Ethereum mainnet, all of 2024–2025 | Wallet-level, no paper, no benchmarks |
| BlockScan / BlockFound | Code, model and data linked on GitHub (repo not opened, weights unconfirmed) | Ethereum 2020–2023, Solana 2023 | Per transaction |
| BERT4ETH, ZipZap, KGBERT4Eth, LMAE4Eth | Code only, as far as seen; no weights confirmed | Ethereum accounts | Phishing-focused |
| TRM Labs foundation model | No (proprietary) | Multi-chain | Blog post only |
| TREASURE (Visa) | No | Card payments | Off-chain |

## Verdicts

| Contribution | Verdict | Reason |
|---|---|---|
| 1. Token-launch foundation model pretrained on unlabeled token sequences | **Novel** | The pretrained on-chain models found are per transaction (BlockScan, Dark Forest), per account (BERT4ETH line) or per wallet (EWE-1). The token-level early-detection models found (TokenScout, MELT, the Solana papers) are supervised. None combines self-supervised pretraining on token-launch sequences with rug-pull or honeypot fine-tuning. |
| 2. Leakage-free benchmark with time splits and fixed horizons | **Partly covered** | Chronological splits, embargoes and minute-level cutoffs are now standard on Solana (2611.13342, MELT, Catching the Rug). TM-RugPull makes the leakage argument on EVM chains, and TokenScout uses a 500-transfer window. No benchmark yet combines Ethereum plus held-out EVM chains, rug-pull and honeypot labels, all five horizons and precision at the top 1% of daily launches. |
| 3. Pretraining-cutoff rule tested by measuring leakage | **Partly covered** | The idea is established for LLMs (DatedGPT measures its size), and time-series foundation-model papers raise it. It has not been measured for transaction or event-sequence foundation models, and no paper proposes a cutoff rule tied to downstream splits. |

## Phase 0 gate: **pass**

No published paper does contribution 1. The closest, TokenScout, scores a token from its first 500 transfers but learns only from labels. It has no unlabeled pretraining, no transfer across tasks or chains and no random-vs-time split analysis. Phase 1 may start.

Watch TokenScout's authors and the Solana early-detection groups (Bahrak; Yanovich and Vodolazov). A pretrained successor from either would close the gap. Re-run this search before submission.

## How to reposition threatened contributions

**Contribution 1 (novel but crowded).** Do not frame it as "the first blockchain foundation model". BlockScan, BERT4ETH and EWE-1 take that claim. Frame it as **the first foundation model whose unit is a token launch**: pretrained on the first events after first liquidity, scored at fixed horizons. Required comparisons:

- TokenScout or a temporal-GNN equivalent.
- EWE-1 and BlockScan embeddings pooled per token, as off-the-shelf foundation-model baselines.
- A LightGBM model on hand-built early features. 2611.18914 and MELT both find that sequence models struggle to beat it, so this is the bar that matters.

**Contribution 2 (partly covered).** Credit 2611.13342, MELT and TM-RugPull for time splits and post-collapse leakage. Claim what they lack:

- EVM chains, with BSC and Base held out.
- Honeypot and rug-pull labels at the same horizons.
- Clock-time horizons (5, 15 and 60 minutes, 24 hours) next to an event-count horizon (500 transfers, matching TokenScout).
- An operational ranking metric: precision at the top 1% of daily launches.
- A random-vs-time split gap measured on one dataset, extending 2611.13342's single comparison.

**Contribution 3 (partly covered).** Cite DatedGPT and Time Machine GPT as the LLM version. Claim the first *measurement* for event-sequence foundation models, and the first *rule*. Pretrain a family of models with staggered cutoffs, then report how downstream PR-AUC and precision at 1% move as the cutoff passes T1 and T2. EWE-1, trained on all 2024–2025 data, is a ready-made leaky baseline for any 2024–2025 test window. 2611.18914 already shows evaluation leakage in public transaction benchmarks, which supports the motivation.

## Papers not opened, worth a later check

- ZipZap, TLMG4Eth, IGT4ETH: account-level models, which should not change contribution 1.
- DeFiTrust: blocked by ScienceDirect. It is a supervised transformer over token event logs, so check it has no pretraining.
- Hunting in the Dark Forest: read only through an aggregator. Check the OpenReview or ACM version.
- The GitHub repos for BlockScan and BERT4ETH: confirm whether weights are released.
