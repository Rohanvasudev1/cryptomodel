# Phase 0: downstream tasks and dataset availability

Checked 2026-11-24. Sources: arXiv pages, published abstracts, GitHub repo pages and the GitHub REST API, PyPI, Hugging Face, and provider terms pages. **No dataset was downloaded.** To confirm column names, the header rows of three small CSVs (SoK, Trapdoor ×2) were read with HTTP range requests under 1.5 KB.

**Markers:** **V** means checked directly on the paper, repo or terms page. **U** means unverified; the source relied on is named. Unmarked facts come from the paper's abstract or dataset section.

**Abbreviations:** EOA is an externally owned account (a key-controlled wallet, not a contract). LP is liquidity-provider tokens. FTM is Fantom. "*scan explorers" means Etherscan and its sister sites (BscScan, BaseScan, …). 4337 is the ERC-4337 smart-account standard.

## Summary

- **Plan counts.** The SoK figure is wrong for the public release. The other two match if the right version is cited.
  - SoK: the public release has **2,360** cases. The **2,391** figure is from the ISSTA 2025 version, which has no public release.
  - RPHunter: 645 is correct, but its data cannot be obtained.
  - TM-RugPull: 1,000 projects in v2/v3 matches the plan; v1 says **1,028**.
- **No public manual label set has usable Base coverage**: TM-RugPull has 2 Base projects. BSC coverage is a few hundred projects.
- **No public set gives launch, first-liquidity or rug timestamps.** Every horizon has to be rebuilt on-chain from the token or pool address.
- **Etherscan's terms now ban using its data, even data obtained through third parties, for ML training or testing.** B4E phishing labels, XBlock, SPN, eth-labels and most exchange labels come from Etherscan. This blocks or clouds the phishing probe and the exchange probe.
- **The "person" wallet class has no usable labels.** The only gold set is 133 humans and 137 bots (Niedermayer et al. 2024).
- **Baselines.**
  - Xia et al. released no code; it has to be reimplemented from the paper's 40-feature table.
  - CoLES runs on Python 3.12 from git main, but caps torch below 2.7, so it does not run on current torch (2.15) without a patch.
  - Official BERT4ETH is TF1-style and breaks on Python 3.12. Its first author's PyTorch port is the practical route.
- **Released weights.** One openly licensed Ethereum wallet-sequence foundation model has weights: **EWE-1-slim** (Apache-2.0, April 2026). It matters for the Phase 0 novelty gate.

---

## 1. Manual rug-pull and honeypot label sets

### 1.1 Plan figures against the papers

| Plan says | Sources say | Verdict |
|---|---|---|
| SoK rug-pull incidents, **2,391 validated cases** | **2,391** appears only in the ISSTA 2025 abstract (DOI 10.1145/3728900). The public arXiv paper (2403.16082) and its GitHub CSV describe **2,360** instances. Those are mostly merged earlier sets: Trapdoor 1,859, HoneyBadger 460 and Pied-Piper 189 (2,508 together), cut to 2,270 after de-duplication, plus **90** new cases from security-firm reports. The 238-row overlap is inferred from those totals; the paper does not itemize it. **V** | **Mismatch.** "Validated rug-pull incidents" overstates it: most rows are honeypots or backdoors, not liquidity rugs. |
| RPHunter, **645 tokens** | 645 rug-pull tokens, manually labeled from 1,048 incidents before May 2024, plus 1,675 benign tokens from TokenScout. **V** | **Count matches.** The data link is an anonymous figshare review link that returns HTTP 403, and TM-RugPull says the data is not public. |
| TM-RugPull, **1,000 projects** | arXiv v1 (Feb 2026) says **1,028**. v2 and v3 (May 2026) and the repo say **1,000**: 599 scam and 401 normal. **V** | **Matches v3.** Cite v3. |

### 1.2 Per-set details

#### SoK on DeFi rug pulls (Sun, Ma, Nie, Liu; NTU)

- **Papers:**
  - arXiv: "SoK: Comprehensive Analysis of Rug Pull Causes, Datasets, and Detection Tools in DeFi", [arXiv:2403.16082](https://arxiv.org/abs/2403.16082), March 2024.
  - Published: "SoK: A Taxonomic Analysis of DeFi Rug Pulls", ISSTA 2025, [10.1145/3728900](https://doi.org/10.1145/3728900).
- **Data:** [github.com/Dianxiang111/Rug-Pull-Dataset](https://github.com/Dianxiang111/Rug-Pull-Dataset). It holds `rugpull_dataset.csv` (10 MB), last pushed 2024-03-22, so it is the 2,360 arXiv version. **V** The row count was not checked; at 10 MB the file may contain padding. **U**
- **License:** none stated. **V**
- **Size:** 2,360 in the public release; 2,391 in the ISSTA version, which has no release found.
- **Chains:** Ethereum and BSC.
- **Dates:** not stated. The literature search runs to 30 September 2023, and the HoneyBadger rows are from 2017–2018. **U**
- **Label definition:** a root-cause taxonomy with labels such as LP drain, hidden mint, sale restriction, blacklist, high fee and fake LP lock. Rows inherit their source set's labeling, so the set is mixed automated and manual.
- **Columns:** `No., Chain, address, Losses, Type, Root Causes, Sources, URL`.
- **Token addresses:** yes. **Timestamps:** no.
- **Use:** filter to liquidity-rug root causes and to the 90 new cases. HoneyBadger rows are not ERC-20 tokens.

#### RPHunter (Wu et al.; Xi'an Jiaotong)

- **Paper:** "RPHunter: Unveiling Rug Pull Schemes in Crypto Token via Code-and-Transaction Fusion Analysis", [arXiv:2506.18398](https://arxiv.org/abs/2506.18398), 2025. **V**
- **Data:** an anonymous figshare link (HTTP 403). There is no GitHub repo. Treat as **unavailable**; the authors could be asked.
- **License:** unknown.
- **Size:** 645 rug-pull tokens and 1,675 benign tokens.
- **Chains:** Ethereum, BSC, Fantom, Base, Arbitrum and Polygon, with no per-chain counts. The paper's real-world test is Ethereum blocks 19,771,560–19,972,630 (May 2024).
- **Dates:** incidents before May 2024.
- **Label definition:** manual, by three experts using card sorting.
- **Token addresses:** presumably. **Timestamps:** not described. **U**

#### TM-RugPull / RugPull1K (Shoaei, Pishdar, Bag-Mohammadi, Karami, Lagaisse)

- **Paper:** "TMRugPull: A Temporally Sound Multimodal Dataset for Early RugPull Detection", [arXiv:2602.21529](https://arxiv.org/abs/2602.21529) v3, May 2026. **V**
- **Data:**
  - [github.com/mohamadpishdar/RugPull-Defender](https://github.com/mohamadpishdar/RugPull-Defender) `data/`: `dataset.xlsx` with 1,000 rows, Solidity zips and `fold_assignment.json`. Last push 2026-11-04. License: **none stated**.
  - [HF fati-80-Sho/RugPull1K](https://huggingface.co/datasets/fati-80-Sho/RugPull1K): **CC BY-NC 4.0**. The viewer shows only opcode text.
- **Size:** 1,000 projects: 599 rug pulls and 401 normal.
- **Chains:** Ethereum 633, BSC 321, Polygon 24, Arbitrum 12, Fantom 5, Cronos 2, **Base 2**, Avalanche 1.
- **Dates:** projects from 2016 to 2025.
- **Label definition:**
  - Rug pull: near-total liquidity withdrawal or an equivalent exit, no further activity and no meaningful price, within a 72-hour window. Confirmed against CertiK, De.Fi and Rekt.news, and reviewed by 2 experts.
  - Normal: projects with high CertiK ratings. These are well-known audited projects, so the negative class is easy.
- **Token addresses:** no explicit column. They are reachable through the `Smart Contract (online)` hyperlinks. **U**
- **Timestamps:** project start and end dates only, with no block numbers.

#### Xia et al. 2021, "Trade or Trick?"

- **Paper:** POMACS 5(3):39 / SIGMETRICS 2022, [arXiv:2109.00229](https://arxiv.org/abs/2109.00229), DOI 10.1145/3491051.
- **Data:** **not released.** The paper says the dataset "will be shared"; no link was found. **V**
- **License:** n/a.
- **Size:** 10,920 scam tokens out of 21,778 tokens (11,215 of 25,131 pools).
- **Chains:** Ethereum, Uniswap V2.
- **Dates:** 2020-05-05 to 2020-12-06.
- **Label definition:** mostly **counterfeit or impersonation** tokens. Seeds were 4,017 name or symbol copies plus 31 Etherscan tags, expanded by guilt-by-association and a random forest. Heuristic plus ML, not manual.
- **Token addresses / timestamps:** n/a.

#### CRPWarner (Lin, Chen, Zheng, Wu, Zhang, Wang; Sun Yat-sen)

The first author is Lin, not Lu.

- **Paper:** [arXiv:2403.01425](https://arxiv.org/abs/2403.01425), March 2024.
- **Data:** [github.com/CRPWarner/RugPull](https://github.com/CRPWarner/RugPull), last push 2024-09-22. **V**
- **License:** none stated.
- **Size:** 103 events in the text, but the paper's table sums to 93. 69 have open-source contracts.
- **Chains:** Ethereum, BSC, Fantom and others.
- **Dates:** up to January 2024.
- **Label definition:** manual card sorting into contract-related types (hidden mint, sell limit, leaking token) and transaction-related types (dump, withdraw liquidity, abandon).
- **Token addresses:** the events sheet is keyed by **project name**. Addresses or bytecode sit in `groundtruth/`. **U** **Timestamps:** no.

#### Trapdoor tokens (Huynh et al.; RMIT): the best public honeypot set

- **Paper:** "From Programming Bugs to Multimillion-Dollar Scams: An Analysis of Trapdoor Tokens on Uniswap", [arXiv:2309.04700](https://arxiv.org/abs/2309.04700), *Future Generation Computer Systems*.
- **Data:** [github.com/bsdp2023/trapdoor_data](https://github.com/bsdp2023/trapdoor_data), containing `trapdoor_list.csv` (`token_address,pool_address,type`) and `non_malicious_list.csv`. **V**
- **License:** none stated.
- **Size:** **1,859** manually verified trapdoor tokens, with a separate non-malicious list. The paper's larger set (11,943 trapdoor and 18,548 non-trapdoor) is probably not in the repo, which predates it. **U**
- **Chains:** Ethereum, Uniswap V2.
- **Dates:** May 2020 to January 2023.
- **Label definition:** a buy-then-sell simulation fails, plus a matching code indicator, then a manual check. This is the plan's honeypot definition, done statically.
- **Token addresses:** token and pool addresses. **Timestamps:** no.

#### HoneyBadger (Torres, Steichen, State)

- **Paper:** USENIX Security 2019, [arXiv:1902.06976](https://arxiv.org/abs/1902.06976).
- **Data:** [github.com/christoftorres/HoneyBadger](https://github.com/christoftorres/HoneyBadger).
- **License:** none stated.
- **Size:** 282 (arXiv) or 690 (published abstract); the SoK counts 460 after its own filtering. **U**
- **Chains:** Ethereum.
- **Dates:** 2017–2018.
- **Label definition:** symbolic execution plus manual checks.
- **Relevance: low.** These are ETH bait contracts that trap senders' ether, not ERC-20 tokens that can't be sold.
- **Addresses:** yes. **Timestamps:** no.

#### Pied-Piper (Ma et al.)

- **Paper:** "Pied-Piper: Revealing the Backdoor Threats in Ethereum ERC Token Contracts", TOSEM 2023, DOI 10.1145/3560264.
- **Data:** no standalone release found. The 189 appear inside the SoK CSV. **U**
- **License:** none found.
- **Size:** 189 developer-confirmed backdoor tokens among 13,484 contracts.
- **Chains:** Ethereum.
- **Dates:** not stated in the sources read. **U**
- **Label definition:** backdoor functions (for example, owner-only mint or transfer blocks) confirmed by developers. A backdoor does not mean the token was rugged.
- **Token addresses:** yes, via the SoK CSV. **Timestamps:** no.

#### Heuristic sets, not manual and mostly unreleased

| Set | Size | Chains, dates | Label rule | Released? | License | Addresses / timestamps |
|---|---|---|---|---|---|---|
| Cernera et al., "Token Spammers, Rug Pulls, and Sniper Bots", USENIX Sec 2023, [arXiv:2206.08202](https://arxiv.org/abs/2206.08202) | 272,349 BSC and 21,742 ETH pools | ETH and BSC, to 2022-03-07 | One-day rug: a pool with exactly one Mint and one Burn, where the creator burns at least 99% of LP | No link found **U** | n/a | n/a (not released) |
| Huynh et al., "Serial Scammers", WWW 2025, [arXiv:2412.10993](https://arxiv.org/abs/2412.10993) | 161,329 Uniswap and 470,712 PancakeSwap pools | ETH and BSC, to July 2024 | Same one-day rule | Code only ([repo](https://github.com/duyhuynhdev/serial-scammer-analyser)); no labels **V** | n/a | n/a (not released) |
| Mazorra et al., "Do not rug on me", 2022, [arXiv:2201.07220](https://arxiv.org/abs/2201.07220) | 26,957 rug and 631 benign | ETH Uniswap V2, April 2020 to September 2021 | Inactive more than 30 days with about a 100% price or liquidity drop | Not found **U** | n/a | n/a (not released) |
| Cernera et al., Telegram bait-and-trap honeypots, [arXiv:2610.10149](https://arxiv.org/abs/2610.10149) | 3,677 events | **BSC** and ETH, 2026 | Sell simulation | No link; a possible BSC honeypot source if requested | n/a | n/a (not released) |
| TrapHunter, ISSTA 2026, [arXiv:2607.18753](https://arxiv.org/abs/2607.18753) | 269 trap tokens | Not stated | Manual | No link | n/a | n/a (not released) |
| TokenScout, CCS 2024 | 214,084 ERC-20 tokens | ETH, 2015 to February 2023 | Scam vs benign | Repo not found **U** | n/a | n/a (not released) |

#### Unlabeled but useful

- **MemeChain** ([arXiv:2601.22185](https://arxiv.org/abs/2601.22185); [Zenodo 18246856](https://zenodo.org/records/18246856), **CC BY 4.0**): 31,811 meme tokens with `token_address` and `deploy_date`, including **827 on Base** and about 15k on BSC. It has no rug labels, so it is useful as a sampling frame for Base and BSC.
- **Forta labelled-datasets** (MIT): malicious contracts and phishing addresses, but no rug-pull or honeypot token labels.
- **Solana sets** (SolRPDS and others) are out of scope because Solana is not EVM.

### 1.3 Label sets at a glance

| Set | Public | License | Size | Chains | Manual | Token address | Timestamps |
|---|---|---|---|---|---|---|---|
| SoK (GitHub) | Yes | None | 2,360 (plan says 2,391) | ETH, BSC | Mixed | Yes | No |
| RPHunter | No (403) | ? | 645 + 1,675 benign | ETH, BSC, Base, … | Yes | Probably | Not described |
| TM-RugPull | Yes | None (GitHub) / CC BY-NC (HF) | 1,000 (599/401) | ETH 633, BSC 321, Base 2 | Yes | Via links | Start and end dates |
| Xia et al. | No | n/a | 10,920 | ETH | Heuristic + ML | n/a | n/a |
| CRPWarner | Yes | None | 93–103 events | ETH, BSC, FTM | Yes | Partly | No |
| Trapdoor | Yes | None | 1,859 + non-malicious list | ETH | Yes | Token + pool | No |
| HoneyBadger | Yes | None | 282–690 | ETH | Semi | Yes | No |
| MemeChain | Yes | CC BY 4.0 | 31,811 (no labels) | ETH, BSC, Base | No labels | Yes | Deploy date |

---

## 2. Phishing and wallet-type label sources

### 2.1 Etherscan terms: read this first

The Etherscan [Terms of Service](https://etherscan.io/terms), section 8, prohibit scraping and reproducing "public labels or name tags". They also prohibit using Etherscan data "whether accessed directly or indirectly for any AI, machine learning … including model training, testing … even if modified, scraped, or obtained through third parties." **V**

The [API terms](https://etherscan.io/apiterms) ban training, pre-training or fine-tuning on API data. Free, Lite and Standard plans are limited to non-commercial research, and the ML ban still applies. **V**

Every Etherscan-derived set below inherits this: B4E, XBlock, eth-labels, brianleect/etherscan-labels, the SNAP exchange list and Kaggle label dumps. Whether to use them under academic convention is the user's call (see Open questions).

### 2.2 Phishing

#### B4E (BERT4ETH)

- **Paper:** Hu et al., "BERT4ETH", WWW 2023, [arXiv:2303.18138](https://arxiv.org/abs/2303.18138).
- **Data:** Google Drive files linked from [git-disl/BERT4ETH](https://github.com/git-disl/BERT4ETH): phishing, normal, ENS, Tornado and an ERC-20 log file. "Labels are already included." **V**
- **License:** none stated, and the labels come from Etherscan.
- **Size (paper Table 2, V):**

  | Set | EOAs | Transactions |
  |---|---|---|
  | Phishing | 3,220 | 328,261 |
  | Normal | 594,038 | 11,350,640 |
  | ENS | 1,335 | 821,140 |
  | Tornado | 2,301 | 1,056,674 |

- **Chains:** Ethereum.
- **Dates:** 2017-01-01 to 2022-05-01. The paper gives no block range.
- **Label definition:**
  - Phishing: the Etherscan "Phish/Hack" tag (7,057 accounts), filtered to EOAs with 3 to 10,000 transactions.
  - Normal: a random sample of EOAs with labeled accounts removed. These are **unlabeled, not verified benign**.
- **Addresses and timestamps:** yes. Each account's transaction list carries timestamps.
- **Split:** none fixed. To compare with BERT4ETH, copy its account-level protocol: maximum sequence length 100, with chunk embeddings mean-pooled.

#### ZipZap

- **Paper:** Hu et al., "ZipZap: Efficient Training of Language Models for Large-Scale Fraud Detection on Blockchain", WWW 2024, DOI 10.1145/3589334.3645352.
- **Data:** one Google Drive tarball linked from [git-disl/ZipZap](https://github.com/git-disl/ZipZap).
- **License:** none stated.
- **Size, dates, label definition:** not stated in the README. It is believed to be B4E plus a larger pretraining corpus. **U**
- **Chains:** Ethereum.
- **Addresses / timestamps:** presumably as B4E. **U**

#### XBlock MulDiGraph

- **Papers:** Wu et al., "Who Are the Phishers?" (IEEE TSMC 2020) and Chen et al., "Phishing Scams Detection in Ethereum Transaction Network" (ACM TOIT 2020). **U**
- **Data:** [xblock.pro](http://xblock.pro), "Ethereum Phishing Transaction Network". The TLS certificate had expired, so neither the page nor its terms could be read.
- **License:** unknown; XBlock sets are usually academic-use, sometimes behind a request form. **U**
- **Size:** about 2.97M nodes, 13.55M edges and **1,165 phishers** (from [arXiv:2409.07494](https://arxiv.org/abs/2409.07494) Table 1).
- **Chains:** Ethereum.
- **Dates:** about 2015–2019. **U**
- **Label definition:** Etherscan "Phish/Hack" tags, with the graph built by a two-hop breadth-first search from known phishers.
- **Addresses / timestamps:** yes; edges carry a timestamp and amount. **U**
- Smaller derived sets: TSGN (1,050 phishers + 1,050 unlabeled) and TEGDetector (1,660 + 1,700).

#### SPN

- **Paper:** "Ethereum Fraud Detection via Joint Transaction Language Model and Graph Representation Learning", [arXiv:2409.07494](https://arxiv.org/abs/2409.07494).
- **Data:** no public link found. **U**
- **License:** none found.
- **Size:** 5,619 phishers and 491,121 normal accounts (496,740 nodes, 831,082 edges).
- **Chains:** Ethereum. **Dates:** up to 2024-06-07.
- **Label definition:** Etherscan phishing tags, with a two-hop crawl through the Etherscan API (first 100 transactions per node). The Etherscan API ML clause applies directly.
- **Addresses / timestamps:** yes, per the paper's construction. **U**

### 2.3 Wallet types: exchange, bot, MEV searcher, person

| Source | Link | License / terms | Size | Chains, dates | Label definition | Addresses / timestamps |
|---|---|---|---|---|---|---|
| Etherscan labels | etherscan.io/labelcloud; API `getaddresstag` and `exportaddresstags` (Pro Plus); bulk "Metadata CSV" (Enterprise) | ToS bans scraping and ML use (2.1) | Not published | Multichain; current snapshot | Etherscan's curated name tags | Address yes. The API gives a last-updated time, not an as-of block. |
| eth-labels | [dawsbot/eth-labels](https://github.com/dawsbot/eth-labels) | MIT on the repo, but the content is scraped from Etherscan, so the ToS still applies | About 115k accounts and 54k tokens (170k entries) | ETH, Base, Arbitrum, Optimism, BSC, Gnosis, Celo; updated 2026-09 | Copy of the *scan explorers' labels (exchange, phish-hack, mev-bot, …) | Address yes, timestamps no |
| brianleect/etherscan-labels | [repo](https://github.com/brianleect/etherscan-labels) | MIT, same caveat | 45,198 labels (29,945 ETH) | 7 chains; last scraped June 2023; scraper broken | Etherscan scrape | Address yes, timestamps no |
| Dune `labels.addresses`, `cex.addresses` | [docs](https://docs.dune.com/data-catalog/curated/labels/address-labels); seeds in [spellbook](https://github.com/duneanalytics/spellbook) | Spellbook is **BSL 1.1**; Dune ToS bans scraping and mirroring; no ML clause | Not published; CEX list covers 29 chains | Multichain; current | Community-contributed, static or query-based, by category (cex, mev, arbitrage_traders, …) | Address yes. `created_at` and `added_date`, but no as-of block for the label. |
| libMEV | libmev.com | Terms not found (the site needs JavaScript) | Unknown | ETH | Groups landed MEV-Boost bundles by searcher **U** | Unknown. Treat as unusable. |
| ZeroMEV | data.zeromev.org | No license found; docs returned HTTP 530 on 2026-11-24 | Every Ethereum block since about December 2019 **U** | ETH | Modified mev-inspect classes (arb, frontrun, backrun, sandwich victim, liquidation) per transaction | Transaction-level with block number. Searcher = `to` and `from` of arb, frontrun and backrun transactions. |
| Flashbots mev-inspect-py | [repo](https://github.com/flashbots/mev-inspect-py) | **MIT**, archived 2024-11-27 | Self-generated | ETH, any range with traces | Detects arbitrage, sandwich and liquidation from traces | Address and block. **The cleanest-licensed route to MEV labels.** |
| Flashbots datasets and APIs | datasets.flashbots.net (**410 Gone**); blocks API docs (**404**); Protect and MEV-Share tables on Dune | Dune ToS | n/a | ETH, 2021 to now | Bundles with `eoa_address`, `to_address` and `bundle_type` (historical) | Mostly gone outside Dune |
| Mempool Dumpster | [mempool-dumpster.flashbots.net](https://mempool-dumpster.flashbots.net) | **CC0** | All public mempool transactions since 2023 | ETH | No labels. A transaction never seen in the mempool suggests private orderflow (a weak bot signal). | First-seen timestamps |
| searcherbuilder.pics recipe | [ethresear.ch post](https://ethresear.ch/t/searcherbuilder-pics-an-open-source-dashboard-on-searcher-builder-relationship-searcher-dominance/17288); repo now 404 | No license | About 157 atomic searchers in 14 days | ETH, 2023-09/10 | Heuristics on ZeroMEV classes, plus CEX-DEX searcher rules | A recipe, not data |
| **Niedermayer et al.**, "Detecting Financial Bots on the Ethereum Blockchain", WWW'24 Companion | [arXiv:2403.19530](https://arxiv.org/abs/2403.19530); [repo](https://github.com/Tommel71/Ethereum-Bot-Detection) | No license file | **137 bots and 133 humans**; MEV multiclass of 111 each for arbitrage, sandwich, liquidation and non-MEV | ETH blocks 15.5M–15.6M (September 2022) | Two annotators (κ = 0.77) plus a tie-breaker; 7-category bot taxonomy | Address yes, fixed block window |
| Codatta Crypto-Address-Annotation-10K | [HF](https://huggingface.co/datasets/Codatta/Crypto-Address-Annotation-10K) | OpenRAIL sample; the full set is commercial | 10k-row sample | Multichain | Community, heuristic and ML (Exchange, Scam, DeFi user, …) | Address yes, timestamps no |
| OFAC SDN addresses | Treasury SDN list; GitHub extracts (e.g. 0xB10C) | US government work | About 1,075 addresses on all chains **U** | Multichain | Sanctions | Illicit class only |
| Arkham, Nansen, Allium, EigenPhi, Codex | Commercial | Paid; redistribution restricted **U** | Large | Multichain | Proprietary | Not usable for a public benchmark |

**Coverage by class:**

- **Exchange:** usable from Dune `cex.addresses` or eth-labels, but each carries the restrictions above. The cleanest option is to re-derive CEX hot wallets from public exchange disclosures, such as proof-of-reserves address lists.
- **MEV searcher:** no clean list exists. Generate labels with mev-inspect-py (MIT) or the searcherbuilder heuristics on our own traces.
- **Bot (general):** only the 270-address Niedermayer set.
- **Person:** **no usable labels at scale.** Options are a weak label (EOA not on any CEX, MEV, bot, sanctions or phishing list, plus human-like activity: diurnal gaps, public-mempool submission, wallet-default gas, ENS reverse record), with the Niedermayer 133 as the only gold evaluation. EIP-7702-delegated EOAs and 4337 smart accounts used by humans since May 2025 complicate the class.

---

## 3. Baseline code

The latest torch on PyPI is **2.15.0** (2026-10-28, wheels for Python 3.11–3.15). The latest TensorFlow is 2.21.0. Nothing below was installed or run.

| Baseline | Repo | License | Last commit / release | Python 3.12 + current torch? |
|---|---|---|---|---|
| **Xia et al. features + RF/XGBoost** | **None.** No code was released. | n/a | n/a | **Reimplement.** The paper's Appendix Table 4 lists 40 features. |
| **CoLES (pytorch-lifestream)** | [pytorch-lifestream/pytorch-lifestream](https://github.com/pytorch-lifestream/pytorch-lifestream) (moved from dllllb) | LICENSE file is **Apache-2.0**; pyproject and PyPI say MIT. Follow the file. | Last commit 2026-11-14. PyPI 0.7.0 released 2025-12-17. | **Not with current torch (2.15).** Python 3.12 is fine from git main (CI runs 3.10 and 3.13), but torch is capped below 2.7. It works with torch 2.6, or with the cap patched. Not run. |
| **BERT4ETH (official)** | [git-disl/BERT4ETH](https://github.com/git-disl/BERT4ETH) | **None** (all rights reserved) | 2024-06-21 | **No.** TF1-style code. |
| **BERT4ETH PyTorch port** | [Bayi-Hu/BERT4ETH_PyTorch](https://github.com/Bayi-Hu/BERT4ETH_PyTorch) (first author, linked from the official README) | **None** | 2025-09-18 | **Likely yes** with small patches; not run. |
| ZipZap | [git-disl/ZipZap](https://github.com/git-disl/ZipZap) | None | 2024-02-14 | No. Same TF1-style code, and no PyTorch port. |

### Xia et al. 40 features

From Appendix Table 4 of the paper:

- **Time series (7):** active period, time since last transaction, and the relative time positions of mint, swap, swap-from, swap-to and burn.
- **Transaction (24):** counts of each event type and of Uniswap and Ethereum transactions, distinct addresses per event type, and event and address shares.
- **Investor (4):** average pools per investor and average transactions per investor, each for mint/burn and for swap.
- **Uniswap-specific (5):** pool count, token volume, tracked and untracked USD volume, and liquidity count.

The paper's best model was a random forest with F1 96.6%, using features over each token's **whole lifetime**. For our horizons, recompute every feature over the same prefix window the sequence models see; otherwise the baseline leaks the label.

### CoLES on Python 3.12

- **PyPI 0.7.0** pins `spacy==3.7.4`, which forces numpy below 2. It works, but on an old stack.
- **Git main** (since 2026-09-24) requires Python ≥3.10 and has numpy 2, Lightning ≥2.5,<3, and CI on Python 3.10 and 3.13. It caps **`torch>=2.6,<2.7`**, only to keep the legacy ONNX exporter in `ONNXInferenceModule`. Two options:
  - (a) Use torch 2.6 in a separate environment.
  - (b) Override the cap and avoid `ONNXInferenceModule`. Run `ptls_tests` to check.

### BERT4ETH on Python 3.12

- The official code uses `tensorflow.compat.v1`, `tf.estimator.ModeKeys` and `tf.contrib`. TF wheels for Python 3.12 start at 2.16, which **removed `tf.estimator`**, so the code breaks.
- Use the PyTorch port. Its dependencies are torch, numpy, pandas, sklearn and tqdm. Full-checkpoint `torch.load` calls may need `weights_only=False`.
- Evaluate with **account-level** splits; issue #12 raised sequence-level leakage.
- The model config is small (8 layers, hidden size 64), so pretraining from scratch on the Mac is feasible.

---

## 4. Released weights

| Model | Weights | Trained on | Size | License | Fit |
|---|---|---|---|---|---|
| **EWE-1-slim** S/M/L, sistemalabs ([HF](https://huggingface.co/sistemalabs); [inference](https://github.com/0xideas/ewe-1-inference)) | **Yes, ONNX only** | Causal next-step transformer over per-wallet transaction sequences. 1.1B Ethereum mainnet transactions from 2024–2025, 31 features per transaction, a 64-transaction window, and a top-1000-per-month address vocabulary. | Small 384-d × 12 layers; medium 768-d × 16 layers (~110M); large 1536-d × 24 layers | **Apache-2.0** | **The one relevant prior.** A wallet view only, built on native transaction fields, with no explicit ERC-20 transfers or token-launch view. Inference pins `sequifier==1.1.1.3`. Its training window may overlap our evaluation period. No paper or evaluation found. **Check for the novelty gate.** |
| BlockScan / BlockFound ([repo](https://github.com/nuwuxian/BlockScan), [arXiv:2410.04039](https://arxiv.org/abs/2410.04039), NeurIPS'25) | Yes (Google Drive) | Masked LM over **individual transactions** (traces), Ethereum 2020–2023 and Solana. Small training sets: about 3.4k ETH transactions. | About 100M (ETH) | None | Poor fit: a per-transaction anomaly model |
| BERT4ETH, ZipZap | **No.** Only precomputed embeddings for the benchmark accounts are released. | Phishing / normal account sequences | 8 layers × 64 | None | Pretrain from scratch |
| BlockGPT ([arXiv:2304.12749](https://arxiv.org/abs/2304.12749)) | No; no official code either | EVM traces | n/a | n/a | n/a |
| LMAE4Eth, TLMG4Eth, KGBERT4Eth | Code at most; no weights | Phishing sets | n/a | None | n/a |
| nuFormer (Nubank), PRAGMA (Revolut) | **No** | Bank transactions | PRAGMA 10M / 100M / 1B | n/a | Method reference only |
| NVIDIA transaction-foundation-model blueprint ([repo](https://github.com/NVIDIA-AI-Blueprints/transaction-foundation-model)) | Recipe and code | Card transactions, not crypto | About 29M **U** | Apache-2.0 | Method reference |
| SmartBERT v2/v3 ([HF](https://huggingface.co/web3se/SmartBERT-v3)) | Yes | Solidity **code** (80k contracts) | About 125M **U** | MIT | Candidate for the Phase 7 contract-code encoder, not a transaction model |

---

## 5. Proposed task list

The plan's horizons are 5, 15 and 60 minutes after first liquidity; 500 transfers; and 24 hours. "Daily launches" means tokens whose first liquidity falls on that UTC day. Task IDs are R (rug pull), H (honeypot), P (phishing) and W (wallet type); they are not the plan's T1/T2 period cut-offs.

R2 is **not in the plan**. It is proposed as a secondary task with a published label rule and needs sign-off. The wallet probes (W1) use a fixed history window, not the token-launch horizons, because a wallet has no launch time.

| # | Task | Input view | Label source | Horizon(s) | Metric | Expected class balance | Status |
|---|---|---|---|---|---|---|---|
| R1 | Rug pull | Token sequence from deployment, cut at the horizon | **Our on-chain labeler** (plan definition: "Linked wallets remove 80% or more of pool liquidity, or price falls 90% or more, within 30 days"). Agreement checked against the SoK liquidity-rug rows (ETH/BSC) and TM-RugPull (599 rug pulls, 401 normal as negatives). | All 5 | Precision at the top 1% of daily launches; PR-AUC | **Likely majority positive.** Xia et al. labeled 50% of Uniswap V2 tokens (45% of pools) as scams in 2020. Mazorra's 30-day inactivity rule labels 98% of tokens. The 90%-price clause will catch most meme coins. Measure in Phase 2. | Labels usable (self-made). Manual sets are validation only and have no timestamps. |
| R1-BSC, R1-Base | Rug pull, cross-chain | Token sequence | Same labeler run on BSC and Base logs. Base has **no manual validation set** (TM-RugPull has 2). The BSC check uses 321 TM-RugPull projects plus SoK BSC rows. | All 5 | Same | As R1 | **Base: no manual labels.** Only the self-made label exists. |
| H1 | Honeypot | Token sequence, optionally plus contract sequence | **Our anvil sell simulator.** Validated against Trapdoor (1,859 manual, ETH, 2020–2023, token and pool addresses). | All 5. The label is fixed after the observation time. | PR-AUC; precision at the top 1% | **Unknown; measure.** Trapdoor's large set is 39% trapdoor, but that set is pre-filtered. On all launches, likely 5–30%. **U** | Usable (self-made). The manual check covers ETH Uniswap V2 only. BSC labels could come from Cernera et al. 2026 if they share. |
| R2 | One-day rug (secondary) | Token sequence | The Cernera and Huynh rule: a pool with one Mint and one Burn, where the creator burns ≥99% of LP. Reproducible on every chain from logs. | 5, 15 and 60 minutes. 500 transfers and 24 hours are dropped because most one-day rugs finish before either. | PR-AUC | High: Cernera et al. flag 272k BSC and 21.7k ETH pools to March 2022. As a share of all launches it is not reported; measure it. **U** | Usable. It gives a published-definition task for comparison. |
| P1 | Phishing on B4E | Wallet sequence (up to 100 transactions per chunk, as in BERT4ETH) | B4E: 3,220 phishing vs 594,038 normal | Whole history to 2022-05-01; account-level split | F1 and PR-AUC, matching BERT4ETH | **0.54% positive** | **License-blocked** under the Etherscan ML clause. Technically available. |
| W1a | Wallet type: exchange | Wallet sequence | Dune `cex.addresses` or eth-labels, or a re-derived list from proof-of-reserves disclosures | Fixed window, such as 30 days of history | Macro-F1 and per-class PR-AUC (shared with W1b–W1d) | Rare: thousands of addresses among millions of EOAs | Restricted (Etherscan or Dune terms). A clean source needs work. |
| W1b | Wallet type: MEV searcher | Wallet sequence (EOA) and contract sequence (searcher contract) | Self-generated with mev-inspect-py (MIT) on our traces, plus the searcherbuilder heuristics | As W1a | As W1a | Rare: hundreds of active searchers | Usable once Phase 1 has traces |
| W1c | Wallet type: bot (non-MEV) | Wallet sequence | Niedermayer et al.: 137 bots | As W1a | As W1a | About 50/50 in the gold set | **Too small to train on**; evaluation only |
| W1d | Wallet type: person | Wallet sequence | **No usable labels.** Only a weak label is possible (2.3), with 133 gold humans for evaluation. | As W1a | As W1a | Unknown | **No usable labels.** Either drop it, or report it as weak-label only. |

**Splits for every task:** a time split at the plan's train end (T1) and validation end (T2), with the 30-day embargo, plus a deployer split for R1, R2 and H1. Score tokens and wallets first seen after the pretraining cutoff on their own, as the plan requires.

---

## Risks

1. **Labels may be circular.** The rug label (liquidity removal or price drop) is visible in the same event stream the model reads. At the 24-hour horizon many rugs have already happened, so the label leaks into the input. Mitigations: exclude tokens already rugged before the horizon, or report them separately; and report agreement with the manual sets first, as the plan says.
2. **Base rate.** If most launches are positive under the 30-day / 90%-price definition, "precision at the top 1%" is near-trivially high. PR-AUC then needs the base rate reported next to it.
3. **No manual ground truth for Base**, and little for BSC. Cross-chain claims will rest on self-made labels.
4. **No public set has timestamps.** Matching manual sets to on-chain first-liquidity times needs Phase 1 data, and address matching may fail for TM-RugPull, which has no address column.
5. **Licensing.**
   - The Etherscan ToS covers B4E, XBlock, eth-labels and SPN, which affects the phishing comparison and the exchange probe.
   - Most academic sets have no license (all rights reserved by default).
   - TM-RugPull on HF is non-commercial.
   - Republishing any of these in the Phase 8 benchmark needs care.
6. **Validation sets differ from our task.** SoK rows are mostly honeypots and backdoors from 2017–2023. TM-RugPull's negatives are audited, famous projects, which makes them easy. Agreement numbers will look better than real-world performance.
7. **Baselines need porting or reimplementing.** Xia must be reimplemented. BERT4ETH official is TF1 and needs the unlicensed PyTorch port. CoLES needs torch 2.6 or a patch.
8. **EWE-1-slim** is an openly released Ethereum wallet-sequence foundation model. It does not model token launches, so contribution 1 probably stands, but the novelty write-up must cite it and probably benchmark it as a frozen-embedding baseline.

## Open questions for the user

1. **Etherscan-derived labels.** Do we use B4E (and an eth-labels or Dune exchange list) under academic convention despite the ToS ML clause, ask Etherscan for permission, or drop the phishing comparison with BERT4ETH?
2. **Rug-pull definition.** The 90%-price clause probably makes most launches positive. Should it be tightened (for example, require linked-wallet liquidity removal or a deployer dump, or a shorter window), or should we keep it and report the base rate?
3. **Person class.** Drop the "person" probe, or keep it as a weak-label probe evaluated only on the 133 Niedermayer humans?
4. **Requesting data.** Should we email the RPHunter, Xia et al. and Cernera et al. (2023 and 2026) authors for their labeled sets? RPHunter includes Base, and Cernera 2026 includes BSC honeypots.
5. **EWE-1-slim.** Add it as a frozen baseline on the wallet probes? Its 2024–2025 training data may overlap our test period.
6. **CoLES environment.** Run it in a separate torch 2.6 environment, or patch the cap in the project's Python 3.12 environment?
