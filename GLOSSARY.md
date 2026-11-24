# Scam token detector

A self-supervised model over Ethereum on-chain events that scores newly launched tokens for rug pulls and honeypots at fixed times after launch.

## Launches and time

**Launch**:
The moment a token becomes tradable, which is its first liquidity. A token's launch decides which period (train, validation or test) it belongs to.
_Avoid_: Deployment (a token is deployed earlier than it launches), listing

**First liquidity**:
The first time liquidity is added to a pool that pairs the token with another asset.
_Avoid_: Pool creation (a pool can exist before it holds liquidity)

**Deployment**:
The block in which the token's contract is created. It decides whether a token counts as seen before the pretraining cutoff.

**Horizon**:
A fixed point after first liquidity at which a token is scored: 5, 15 or 60 minutes, 500 transfers, or 24 hours. A score may use only events before its horizon.
_Avoid_: Window, checkpoint

**T1**:
The end of the train period, 2026-03-31.

**T2**:
The end of the validation period, 2026-06-30. It is also the pretraining cutoff.

**Embargo**:
A 30-day gap between two periods in which no launch is used, so labels from one period cannot leak into the next.
_Avoid_: Gap, buffer

**Pretraining cutoff**:
The last date whose events the pretrained encoder may see (T2). Entities first seen after it are scored separately.
_Avoid_: Training cutoff, data cutoff

**Snapshot date**:
The date on which a stored table was read from its source. Every stored table records one.

## Labels

**Strict rug label**:
Within 30 days of launch, linked wallets remove 80% or more of the pool's liquidity, or the deployer or linked wallets dump the token. A price fall alone does not count. This is the headline label.
_Avoid_: Rug (unqualified)

**Broad rug label**:
The strict rug label, or a price fall of 90% or more within 30 days of launch. A secondary label.

**Honeypot**:
A token whose sells by unrelated wallets fail after the observation time.
_Avoid_: Scam token (too broad)

**Linked wallet**:
A wallet treated as the same actor as the deployer for the rug labels. The linking rule is set in Phase 2.

## Data

**Event**:
One decoded on-chain action, such as a transfer, swap, liquidity mint or burn, contract creation or internal ETH transfer.
_Avoid_: Transaction (one transaction holds many events), log

**Event table**:
The single table of all events, one row per event, from which every view is cut.

**Token view**:
The events that touch one token, in order, starting at its deployment.
_Avoid_: Token sequence (fine as an informal synonym), token history

**Wallet view**:
The events that touch one wallet, in order. A transfer appears in the views of both its sender and its receiver.

**Contract view**:
The events that touch one contract, in order.

**Filtered extract**:
The local copy of the source tables after dropping columns and rows the event table does not need. The raw source stays readable remotely.
_Avoid_: Raw data (the raw data is the unfiltered source)
