"""Decode a table of raw logs into typed event tables and one `dex_action` table.

Input is a pyarrow Table or polars DataFrame shaped like the AWS Public
Blockchain Data logs table (`s3://aws-public-blockchain/v1.0/eth/logs/`),
checked on 2026-11-24 with DuckDB `DESCRIBE`:

    address VARCHAR, topics VARCHAR[], data VARCHAR, transaction_index BIGINT,
    log_index BIGINT, transaction_hash VARCHAR, block_number BIGINT,
    block_hash VARCHAR, block_timestamp TIMESTAMP, date DATE, last_modified TIMESTAMP

Hex values there are lowercase with a `0x` prefix. Tables with `topic0` to
`topic3` columns instead of a `topics` list are accepted too.

Rows whose topic0 is not a known event are filtered out in polars; the rest are
decoded one by one with the pure decoders in `events.py`, so batch and single-log
decoding cannot disagree. Logs with a known topic0 that do not fit the layout go
to the `errors` table, never silently to zero.

Amounts that can exceed 63 bits are stored as base-10 strings (polars has no
256-bit integer, and Decimal stops at 38 digits); ticks and fees are Int64.
Nothing passes through float.

## dex_action

One row per pool creation, swap, liquidity mint, liquidity burn or fee collect.

- `pool`: pair or pool address for V2 and V3; the 32-byte pool id for V4.
- `emitter`: the contract that emitted the log (pool, factory or V4 PoolManager).
- `action`: `create`, `swap`, `mint`, `burn` or `collect`. V4 ModifyLiquidity is
  `mint` for positive liquidity delta, `burn` for negative, `collect` for zero.
- `amount0`, `amount1`: for swaps, the signed change in the pool's balance
  (positive = into the pool) for all versions; V2 is `in - out` and V4 is negated
  from its swapper-side sign. For mint, burn and collect, the unsigned amounts in
  the event. Null for creates and for V4 ModifyLiquidity, which has no amounts.
- `liquidity_delta`: signed liquidity change for V3 mint and burn and V4 modify;
  null for V2 (V2 LP tokens are ERC-20 Transfers, not in these events).
- `fee`: on create rows the pool's configured fee (for V4 this may be the
  0x800000 dynamic-fee flag); on V4 swap rows the fee charged by that swap;
  on other rows the configured fee from the registry.
- `version`: from the event layout (`v2`, `v3`, `v4`), so it is known even for
  unresolved pools.
- `token0`, `token1`, `factory`, `dex`, `fee`: on create rows they come from the
  event. Other rows get them from the pool registry (`attach_pool_info`); if the
  pool's creation event has not been seen they stay null and `pool_resolved` is
  false. (`unknown_fork` means the creating factory is known to be unlisted;
  a null `dex` means the pool's creation has not been seen at all.)
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields
from typing import Any

import polars as pl
import pyarrow as pa  # type: ignore[import-untyped]

from cryptomodel.decode import events as ev
from cryptomodel.decode.events import (
    DECODERS,
    EVENT_CLASSES,
    DecodedEvent,
    DecodeError,
    canonical_topic0,
    decode_log,
)
from cryptomodel.decode.registry import KNOWN_FACTORIES, UNKNOWN_FORK, factory_label

__all__ = [
    "EVENT_KINDS",
    "LOG_COLUMNS",
    "POOL_REGISTRY_SCHEMA",
    "DecodedLogs",
    "attach_pool_info",
    "build_pool_registry",
    "decode_logs",
    "merge_pool_registries",
]

LOG_COLUMNS = (
    "address",
    "topics",
    "data",
    "transaction_hash",
    "log_index",
    "block_number",
    "block_timestamp",
)
"""Columns `decode_logs` needs (`topic0`..`topic3` may replace `topics`)."""

EVENT_KINDS: tuple[str, ...] = tuple(cls.KIND for cls in EVENT_CLASSES)

_SMALL_INT_FIELDS = frozenset(
    {"fee", "tick", "tick_lower", "tick_upper", "tick_spacing"}
)
"""int24/uint24 fields, safe as Int64. Every other int field is a decimal string."""

POOL_REGISTRY_SCHEMA = pl.Schema(
    {
        "pool": pl.String,
        "event_emitter": pl.String,  # address whose logs carry this pool's events
        "factory": pl.String,
        "dex": pl.String,
        "version": pl.String,
        "token0": pl.String,
        "token1": pl.String,
        "fee": pl.Int64,
        "tick_spacing": pl.Int64,
        "hooks": pl.String,
        "created_block_number": pl.Int64,
        "created_tx_hash": pl.String,
    }
)


@dataclass(frozen=True)
class DecodedLogs:
    events: dict[str, pl.DataFrame]
    """Event kind (e.g. `v3_swap`) -> typed table, one per kind, empty if none."""
    dex_action: pl.DataFrame
    errors: pl.DataFrame
    """Logs with a known topic0 that failed to decode, with the reason."""
    pool_registry: pl.DataFrame
    """The prior registry passed in plus every pool created in this batch."""


def _meta_schema(ts_dtype: pl.DataType) -> dict[str, pl.DataType]:
    return {
        "block_number": pl.Int64(),
        "block_timestamp": ts_dtype,
        "tx_hash": pl.String(),
        "log_index": pl.Int64(),
    }


def _event_schema(cls: type[DecodedEvent], ts_dtype: pl.DataType) -> pl.Schema:
    schema = _meta_schema(ts_dtype)
    for f in fields(cls):
        schema[f.name] = pl.Int64() if f.name in _SMALL_INT_FIELDS else pl.String()
    return pl.Schema(schema)


def _dex_action_schema(ts_dtype: pl.DataType) -> pl.Schema:
    schema = _meta_schema(ts_dtype)
    for name in (
        "pool",
        "emitter",
        "factory",
        "dex",
        "version",
        "action",
        "token0",
        "token1",
        "amount0",
        "amount1",
        "sender",
        "recipient",
        "owner",
        "liquidity_delta",
    ):
        schema[name] = pl.String()
    schema.update(
        tick_lower=pl.Int64(),
        tick_upper=pl.Int64(),
        fee=pl.Int64(),
        pool_resolved=pl.Boolean(),
    )
    return pl.Schema(schema)


def _error_schema(ts_dtype: pl.DataType) -> pl.Schema:
    schema = _meta_schema(ts_dtype)
    schema.update(address=pl.String(), topic0=pl.String(), error=pl.String())
    return pl.Schema(schema)


def _event_values(event: DecodedEvent) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for f in fields(event):
        value = getattr(event, f.name)
        out[f.name] = (
            str(value)
            if isinstance(value, int) and f.name not in _SMALL_INT_FIELDS
            else value
        )
    return out


def _to_decimal(value: int | None) -> str | None:
    return None if value is None else str(value)


def _dex_action(event: DecodedEvent) -> dict[str, Any] | None:
    """The dex_action fields for one event (before pool-registry attachment)."""
    match event:
        case ev.V2PairCreated():
            dex, version = factory_label(event.factory, "v2")
            return {
                "action": "create",
                "pool": event.pair,
                "emitter": event.factory,
                "factory": event.factory,
                "dex": dex,
                "version": version,
                "token0": event.token0,
                "token1": event.token1,
            }
        case ev.V3PoolCreated():
            dex, version = factory_label(event.factory, "v3")
            return {
                "action": "create",
                "pool": event.pool,
                "emitter": event.factory,
                "factory": event.factory,
                "dex": dex,
                "version": version,
                "token0": event.token0,
                "token1": event.token1,
                "fee": event.fee,
            }
        case ev.V4Initialize():
            dex, version = factory_label(event.pool_manager, "v4")
            return {
                "action": "create",
                "pool": event.pool_id,
                "emitter": event.pool_manager,
                "factory": event.pool_manager,
                "dex": dex,
                "version": version,
                "token0": event.currency0,
                "token1": event.currency1,
                "fee": event.fee,
            }
        case ev.V2Mint():
            return {
                "action": "mint",
                "pool": event.pair,
                "emitter": event.pair,
                "version": "v2",
                "sender": event.sender,
                "amount0": _to_decimal(event.amount0),
                "amount1": _to_decimal(event.amount1),
            }
        case ev.V2Burn():
            return {
                "action": "burn",
                "pool": event.pair,
                "emitter": event.pair,
                "version": "v2",
                "sender": event.sender,
                "recipient": event.to,
                "amount0": _to_decimal(event.amount0),
                "amount1": _to_decimal(event.amount1),
            }
        case ev.V2Swap():
            return {
                "action": "swap",
                "pool": event.pair,
                "emitter": event.pair,
                "version": "v2",
                "sender": event.sender,
                "recipient": event.to,
                "amount0": _to_decimal(event.amount0_in - event.amount0_out),
                "amount1": _to_decimal(event.amount1_in - event.amount1_out),
            }
        case ev.V3Mint():
            return {
                "action": "mint",
                "pool": event.pool,
                "emitter": event.pool,
                "version": "v3",
                "sender": event.sender,
                "owner": event.owner,
                "amount0": _to_decimal(event.amount0),
                "amount1": _to_decimal(event.amount1),
                "liquidity_delta": _to_decimal(event.amount),
                "tick_lower": event.tick_lower,
                "tick_upper": event.tick_upper,
            }
        case ev.V3Burn():
            return {
                "action": "burn",
                "pool": event.pool,
                "emitter": event.pool,
                "version": "v3",
                "owner": event.owner,
                "amount0": _to_decimal(event.amount0),
                "amount1": _to_decimal(event.amount1),
                "liquidity_delta": _to_decimal(-event.amount),
                "tick_lower": event.tick_lower,
                "tick_upper": event.tick_upper,
            }
        case ev.V3Collect():
            return {
                "action": "collect",
                "pool": event.pool,
                "emitter": event.pool,
                "version": "v3",
                "owner": event.owner,
                "recipient": event.recipient,
                "amount0": _to_decimal(event.amount0),
                "amount1": _to_decimal(event.amount1),
                "tick_lower": event.tick_lower,
                "tick_upper": event.tick_upper,
            }
        case ev.V3Swap():
            return {
                "action": "swap",
                "pool": event.pool,
                "emitter": event.pool,
                "version": "v3",
                "sender": event.sender,
                "recipient": event.recipient,
                "amount0": _to_decimal(event.amount0),
                "amount1": _to_decimal(event.amount1),
            }
        case ev.V4ModifyLiquidity():
            delta = event.liquidity_delta
            action = "mint" if delta > 0 else "burn" if delta < 0 else "collect"
            return {
                "action": action,
                "pool": event.pool_id,
                "emitter": event.pool_manager,
                "version": "v4",
                "sender": event.sender,
                "liquidity_delta": _to_decimal(delta),
                "tick_lower": event.tick_lower,
                "tick_upper": event.tick_upper,
            }
        case ev.V4Swap():
            # V4 reports the swapper's balance change; flip it to the pool's.
            return {
                "action": "swap",
                "pool": event.pool_id,
                "emitter": event.pool_manager,
                "version": "v4",
                "sender": event.sender,
                "amount0": _to_decimal(-event.amount0),
                "amount1": _to_decimal(-event.amount1),
                "fee": event.fee,
            }
        case _:
            return None  # V2 Sync, V3 Initialize, ERC-20 events


def _normalize_logs(logs: pa.Table | pl.DataFrame) -> pl.DataFrame:
    df = pl.from_arrow(logs) if isinstance(logs, pa.Table) else logs
    if not isinstance(df, pl.DataFrame):
        raise TypeError(
            f"expected a pyarrow Table or polars DataFrame, got {type(logs).__name__}"
        )
    if "topics" not in df.columns and "topic0" in df.columns:
        topic_cols = [
            c for c in ("topic0", "topic1", "topic2", "topic3") if c in df.columns
        ]
        # Drop trailing null topics only; a null before a non-null topic stays a
        # null so the decoder rejects the log instead of shifting topics down.
        n_topics = pl.max_horizontal(
            pl.when(pl.col(col).is_not_null()).then(i + 1).otherwise(0)
            for i, col in enumerate(topic_cols)
        )
        df = df.with_columns(
            pl.concat_list(topic_cols).list.head(n_topics).alias("topics")
        )
    missing = [c for c in LOG_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"logs table is missing columns: {', '.join(missing)}")
    return df


def _empty_registry() -> pl.DataFrame:
    return pl.DataFrame(schema=POOL_REGISTRY_SCHEMA)


def build_pool_registry(events: Mapping[str, pl.DataFrame]) -> pl.DataFrame:
    """Build a pool registry from the creation tables in `decode_logs(...).events`.

    One row per pool from V2 PairCreated, V3 PoolCreated and V4 Initialize, keyed
    by (`pool`, `event_emitter`): the pool's own address for V2 and V3, the
    PoolManager for V4. Pools from factories not in `registry.KNOWN_FACTORIES`
    get dex `unknown_fork`.
    """
    null_int = pl.lit(None, dtype=pl.Int64)
    null_str = pl.lit(None, dtype=pl.String)
    created = [
        pl.col("block_number").alias("created_block_number"),
        pl.col("tx_hash").alias("created_tx_hash"),
    ]
    parts = []
    if (v2 := events.get("v2_pair_created")) is not None:
        parts.append(
            v2.select(
                *created,
                pool="pair",
                event_emitter="pair",
                factory="factory",
                layout=pl.lit("v2"),
                token0="token0",
                token1="token1",
                fee=null_int,
                tick_spacing=null_int,
                hooks=null_str,
            )
        )
    if (v3 := events.get("v3_pool_created")) is not None:
        parts.append(
            v3.select(
                *created,
                pool="pool",
                event_emitter="pool",
                factory="factory",
                layout=pl.lit("v3"),
                token0="token0",
                token1="token1",
                fee="fee",
                tick_spacing="tick_spacing",
                hooks=null_str,
            )
        )
    if (v4 := events.get("v4_initialize")) is not None:
        parts.append(
            v4.select(
                *created,
                pool="pool_id",
                event_emitter="pool_manager",
                factory="pool_manager",
                layout=pl.lit("v4"),
                token0="currency0",
                token1="currency1",
                fee="fee",
                tick_spacing="tick_spacing",
                hooks="hooks",
            )
        )
    if not parts:
        return _empty_registry()
    known = pl.DataFrame(
        {
            "factory": list(KNOWN_FACTORIES),
            "known_dex": [f.dex for f in KNOWN_FACTORIES.values()],
            "known_version": [f.version for f in KNOWN_FACTORIES.values()],
        }
    )
    return (
        pl.concat(parts)
        .join(known, on="factory", how="left", maintain_order="left")
        .with_columns(
            dex=pl.col("known_dex").fill_null(UNKNOWN_FORK),
            version=pl.coalesce("known_version", "layout"),
        )
        .unique(subset=["pool", "event_emitter"], keep="first", maintain_order=True)
        .select(POOL_REGISTRY_SCHEMA.names())
        .cast(POOL_REGISTRY_SCHEMA)
    )


def merge_pool_registries(*registries: pl.DataFrame | None) -> pl.DataFrame:
    """Concatenate registries; for a pool seen twice the earlier argument wins."""
    frames = [
        r.select(POOL_REGISTRY_SCHEMA.names()).cast(POOL_REGISTRY_SCHEMA)
        for r in registries
        if r is not None
    ]
    if not frames:
        return _empty_registry()
    return pl.concat(frames).unique(
        subset=["pool", "event_emitter"], keep="first", maintain_order=True
    )


def attach_pool_info(
    dex_action: pl.DataFrame, pool_registry: pl.DataFrame
) -> pl.DataFrame:
    """Fill token0, token1, factory, dex and fee on dex_action rows from a registry.

    Matches on (`pool`, `emitter`) = (`pool`, `event_emitter`). Values already on a
    row are kept. `pool_resolved` becomes true for matched rows and stays false
    for pools the registry does not know. Safe to rerun with a later registry.
    """
    reg = merge_pool_registries(pool_registry).select(
        "pool",
        pl.col("event_emitter").alias("emitter"),
        pl.col("factory").alias("_reg_factory"),
        pl.col("dex").alias("_reg_dex"),
        pl.col("token0").alias("_reg_token0"),
        pl.col("token1").alias("_reg_token1"),
        pl.col("fee").alias("_reg_fee"),
        pl.lit(True).alias("_reg_hit"),
    )
    return (
        dex_action.join(reg, on=["pool", "emitter"], how="left", maintain_order="left")
        .with_columns(
            factory=pl.coalesce("factory", "_reg_factory"),
            dex=pl.coalesce("dex", "_reg_dex"),
            token0=pl.coalesce("token0", "_reg_token0"),
            token1=pl.coalesce("token1", "_reg_token1"),
            fee=pl.coalesce("fee", "_reg_fee"),
            pool_resolved=pl.col("pool_resolved") | pl.col("_reg_hit").fill_null(False),
        )
        .select(dex_action.columns)
    )


def _rows(df: pl.DataFrame) -> Iterable[tuple[Any, ...]]:
    cols = [
        "address",
        "topics",
        "data",
        "block_number",
        "block_timestamp",
        "transaction_hash",
        "log_index",
    ]
    return df.select(cols).iter_rows()


def decode_logs(
    logs: pa.Table | pl.DataFrame, pool_registry: pl.DataFrame | None = None
) -> DecodedLogs:
    """Decode every known event in `logs`.

    `pool_registry` carries pools created in earlier batches (for example the
    `pool_registry` of a previous call) so swaps on older pools resolve their
    tokens. Pools created in this batch are added to it.
    """
    df = _normalize_logs(logs)
    ts_dtype = df.schema["block_timestamp"]
    known_topic0 = pl.Series(list(DECODERS), dtype=pl.String)
    topic0 = pl.col("topics").list.first().str.to_lowercase()
    topic0 = (
        pl.when(topic0.str.starts_with("0x"))
        .then(topic0)
        .otherwise(pl.lit("0x") + topic0)
    )
    candidates = df.filter(topic0.is_in(known_topic0.implode()))

    by_kind: dict[str, list[dict[str, Any]]] = {kind: [] for kind in EVENT_KINDS}
    actions: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for (
        address,
        topics,
        data,
        block_number,
        block_timestamp,
        tx_hash,
        log_index,
    ) in _rows(candidates):
        meta = {
            "block_number": block_number,
            "block_timestamp": block_timestamp,
            "tx_hash": tx_hash,
            "log_index": log_index,
        }
        try:
            event = decode_log(address, topics, data)
        except DecodeError as exc:
            errors.append(
                meta
                | {
                    "address": address,
                    "topic0": canonical_topic0(topics[0]),
                    "error": str(exc),
                }
            )
            continue
        if event is None:
            continue
        by_kind[event.KIND].append(meta | _event_values(event))
        action = _dex_action(event)
        if action is not None:
            actions.append(
                meta | action | {"pool_resolved": action["action"] == "create"}
            )

    events = {
        cls.KIND: pl.DataFrame(by_kind[cls.KIND], schema=_event_schema(cls, ts_dtype))
        for cls in EVENT_CLASSES
    }
    registry = merge_pool_registries(pool_registry, build_pool_registry(events))
    dex_action = attach_pool_info(
        pl.DataFrame(actions, schema=_dex_action_schema(ts_dtype)), registry
    )
    return DecodedLogs(
        events=events,
        dex_action=dex_action,
        errors=pl.DataFrame(errors, schema=_error_schema(ts_dtype)),
        pool_registry=registry,
    )
