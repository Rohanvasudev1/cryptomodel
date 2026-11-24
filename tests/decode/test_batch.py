"""Batch decoding of an AWS-shaped logs table into typed tables and dex_action."""

from datetime import datetime

import _decode_fixtures as fx
import polars as pl
import pyarrow as pa  # type: ignore[import-untyped]
import pytest
from _decode_fixtures import topic_addr as _topic_addr
from _decode_fixtures import word as _word

from cryptomodel.decode import constants
from cryptomodel.decode.batch import (
    EVENT_KINDS,
    POOL_REGISTRY_SCHEMA,
    DecodedLogs,
    attach_pool_info,
    build_pool_registry,
    decode_logs,
)

TS = datetime(2026, 11, 20, 4, 4, 47)
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
UNKNOWN_FACTORY = "0x" + "12" * 20


# A PoolCreated for the real WETH/USDT pool 0x4e68...fa36, but emitted by a
# made-up factory, so the V3 swap fixture resolves to an "unknown_fork" pool.
SYNTHETIC_FORK_POOL_CREATED = fx.RawLog(
    address=UNKNOWN_FACTORY,
    topics=[constants.V3_POOL_CREATED, _topic_addr(WETH), _topic_addr(USDT), "0x" + _word(3000)],
    data="0x" + _word(60) + _word(int("4e68ccd3e89f51c3074ca5072bbac773960dfa36", 16)),
    block_number=1,
    tx_hash="0x" + "aa" * 32,
    log_index=0,
)
# Malformed: a V2 Sync with one data word missing.
MALFORMED_SYNC = fx.RawLog(
    address=fx.V2_SYNC.address,
    topics=fx.V2_SYNC.topics,
    data=fx.V2_SYNC.data[:66],
    block_number=2,
    tx_hash="0x" + "bb" * 32,
    log_index=5,
)
UNKNOWN_EVENT = fx.RawLog(
    address=fx.V2_SYNC.address,
    topics=["0x" + "ab" * 32],
    data="0x",
    block_number=3,
    tx_hash="0x" + "cc" * 32,
    log_index=0,
)
LOGS = [*fx.ALL_FIXTURES, SYNTHETIC_FORK_POOL_CREATED, MALFORMED_SYNC, UNKNOWN_EVENT]

# What an earlier batch would have learned: Uniswap V2 USDC/WETH, created 2020.
PRIOR_REGISTRY = pl.DataFrame(
    {
        "pool": ["0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"],
        "event_emitter": ["0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"],
        "factory": ["0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f"],
        "dex": ["uniswap"],
        "version": ["v2"],
        "token0": [USDC],
        "token1": [WETH],
        "fee": [None],
        "tick_spacing": [None],
        "hooks": [None],
        "created_block_number": [10008355],
        "created_tx_hash": ["0x" + "dd" * 32],
    },
    schema=POOL_REGISTRY_SCHEMA,
)


def _logs_frame(logs: list[fx.RawLog]) -> pl.DataFrame:
    """Rows shaped like the AWS `v1.0/eth/logs` table (see batch.LOG_SCHEMA)."""
    return pl.DataFrame(
        {
            "address": [log.address for log in logs],
            "topics": [log.topics for log in logs],
            "data": [log.data for log in logs],
            "transaction_index": [0 for _ in logs],
            "log_index": [log.log_index for log in logs],
            "transaction_hash": [log.tx_hash for log in logs],
            "block_number": [log.block_number for log in logs],
            "block_hash": ["0x" + "00" * 32 for _ in logs],
            "block_timestamp": [TS for _ in logs],
        },
        schema={
            "address": pl.String,
            "topics": pl.List(pl.String),
            "data": pl.String,
            "transaction_index": pl.Int64,
            "log_index": pl.Int64,
            "transaction_hash": pl.String,
            "block_number": pl.Int64,
            "block_hash": pl.String,
            "block_timestamp": pl.Datetime("us"),
        },
    )


@pytest.fixture(scope="module")
def decoded() -> DecodedLogs:
    return decode_logs(_logs_frame(LOGS), pool_registry=PRIOR_REGISTRY)


def _row(df: pl.DataFrame, **match: object) -> dict[str, object]:
    out = df.filter(pl.all_horizontal(pl.col(k) == v for k, v in match.items()))
    assert out.height == 1, out
    return out.row(0, named=True)


def test_typed_tables_have_one_table_per_kind(decoded: DecodedLogs) -> None:
    assert set(decoded.events) == set(EVENT_KINDS)
    counts = {kind: df.height for kind, df in decoded.events.items()}
    assert counts["v3_swap"] == 2  # Uniswap and PancakeSwap layouts
    assert counts["v3_pool_created"] == 2  # real plus synthetic fork
    assert all(n == 1 for kind, n in counts.items() if kind not in {"v3_swap", "v3_pool_created"})


def test_typed_table_keeps_amounts_as_exact_decimal_strings(decoded: DecodedLogs) -> None:
    swap = decoded.events["v4_swap"]
    assert swap.schema["amount1"] == pl.String
    assert swap.schema["tick"] == pl.Int64
    row = swap.row(0, named=True)
    assert row["amount1"] == "-259741301662557053331753"
    assert row["sqrt_price_x96"] == "44922937928362125308274317646089"
    assert row["tx_hash"] == fx.V4_SWAP.tx_hash
    assert row["log_index"] == fx.V4_SWAP.log_index
    assert row["block_timestamp"] == TS


def test_no_float_columns_anywhere(decoded: DecodedLogs) -> None:
    frames = [*decoded.events.values(), decoded.dex_action, decoded.errors, decoded.pool_registry]
    for frame in frames:
        assert not any(dtype.is_float() for dtype in frame.schema.values()), frame.schema


def test_malformed_log_goes_to_errors_and_unknown_is_dropped(decoded: DecodedLogs) -> None:
    assert decoded.errors.height == 1
    err = decoded.errors.row(0, named=True)
    assert err["tx_hash"] == MALFORMED_SYNC.tx_hash
    assert err["log_index"] == 5
    assert err["topic0"] == constants.V2_SYNC
    assert "V2Sync" in err["error"]
    assert decoded.events["v2_sync"].height == 1  # only the good Sync


def test_dex_action_row_count(decoded: DecodedLogs) -> None:
    actions = decoded.dex_action.group_by("action").len().sort("action")
    assert dict(actions.iter_rows()) == {"burn": 2, "collect": 1, "create": 4, "mint": 3, "swap": 4}


def test_v2_swap_is_pool_signed_and_resolved_from_prior_registry(decoded: DecodedLogs) -> None:
    row = _row(decoded.dex_action, tx_hash=fx.V2_SWAP.tx_hash, log_index=fx.V2_SWAP.log_index)
    assert row["action"] == "swap"
    assert row["version"] == "v2"
    assert row["amount0"] == "-635030774"  # USDC out of the pool
    assert row["amount1"] == "379930928284193792"  # WETH into the pool
    assert row["token0"] == USDC
    assert row["token1"] == WETH
    assert row["dex"] == "uniswap"
    assert row["pool_resolved"] is True
    assert row["sender"] == "0x51c72848c68a965f66fa7a88855f9f7784502a7f"
    assert row["recipient"] == "0x51c72848c68a965f66fa7a88855f9f7784502a7f"


def test_v4_swap_is_flipped_to_pool_perspective(decoded: DecodedLogs) -> None:
    row = _row(decoded.dex_action, tx_hash=fx.V4_SWAP.tx_hash, log_index=fx.V4_SWAP.log_index)
    assert row["version"] == "v4"
    assert row["pool"] == "0xb80eb6a392d33eb1b014656b31b96edf9aa16c39c0baa5dbf7492435327516ea"
    assert row["amount0"] == "-819785390279743211"  # ETH out to the swapper
    assert row["amount1"] == "259741301662557053331753"  # token into the PoolManager
    assert row["pool_resolved"] is False  # pool initialised before this batch
    assert row["token0"] is None
    assert row["dex"] is None
    assert row["factory"] is None


def test_unresolved_pancakeswap_pool_stays_explicit(decoded: DecodedLogs) -> None:
    row = _row(decoded.dex_action, tx_hash=fx.PANCAKE_V3_SWAP.tx_hash)
    assert row["version"] == "v3"
    assert row["pool_resolved"] is False
    assert row["token0"] is None
    assert row["token1"] is None
    assert row["amount0"] == "-1178482259542562"


def test_unknown_factory_is_labelled_unknown_fork(decoded: DecodedLogs) -> None:
    create = _row(decoded.dex_action, tx_hash=SYNTHETIC_FORK_POOL_CREATED.tx_hash)
    assert create["action"] == "create"
    assert create["dex"] == "unknown_fork"
    assert create["version"] == "v3"
    assert create["factory"] == UNKNOWN_FACTORY
    swap = _row(decoded.dex_action, tx_hash=fx.V3_SWAP.tx_hash)
    assert swap["dex"] == "unknown_fork"
    assert swap["token0"] == WETH
    assert swap["token1"] == USDT
    assert swap["pool_resolved"] is True
    assert swap["amount1"] == "-7984010464"


def test_create_rows_carry_tokens_and_known_dex(decoded: DecodedLogs) -> None:
    v2 = _row(decoded.dex_action, tx_hash=fx.V2_PAIR_CREATED.tx_hash)
    assert (v2["pool"], v2["dex"], v2["version"]) == ("0x3ac69e914905577af1c325e6ef7ad9d76e1567ef", "uniswap", "v2")
    assert v2["token1"] == WETH
    assert v2["amount0"] is None
    v4 = _row(decoded.dex_action, tx_hash=fx.V4_INITIALIZE.tx_hash)
    assert (v4["dex"], v4["version"], v4["fee"]) == ("uniswap", "v4", 999961)
    assert v4["pool"] == "0x08988e4385fdd636e5de72bb70ad196e871eefa8fdd66af937035aedef2e6c2a"
    assert v4["factory"] == "0x000000000004444c5dc75cb358380d2e3de08a90"


def test_liquidity_fields(decoded: DecodedLogs) -> None:
    v3_mint = _row(decoded.dex_action, tx_hash=fx.V3_MINT.tx_hash)
    assert (v3_mint["liquidity_delta"], v3_mint["tick_lower"], v3_mint["tick_upper"]) == (
        "1741916136209",
        199360,
        202860,
    )
    assert v3_mint["owner"] == "0xc36442b4a4522e871399cd717abdd847ab11fe88"
    v3_burn = _row(decoded.dex_action, tx_hash=fx.V3_BURN.tx_hash)
    assert v3_burn["action"] == "burn"
    assert v3_burn["liquidity_delta"] == "-441396993045310"
    assert v3_burn["amount1"] == "375778185250911516"
    v4_mod = _row(decoded.dex_action, tx_hash=fx.V4_MODIFY_LIQUIDITY.tx_hash)
    assert v4_mod["action"] == "mint"
    assert v4_mod["liquidity_delta"] == "11352911822593196032"
    assert v4_mod["amount0"] is None  # V4 ModifyLiquidity carries no token amounts
    v2_burn = _row(decoded.dex_action, tx_hash=fx.V2_BURN.tx_hash, action="burn")
    assert v2_burn["liquidity_delta"] is None
    assert v2_burn["recipient"] == "0x0ea041260095b20feda41ef4fdbef7d801f4c438"


def test_pool_registry_merges_prior_and_new_pools(decoded: DecodedLogs) -> None:
    reg = decoded.pool_registry
    assert reg.schema == POOL_REGISTRY_SCHEMA
    assert reg.height == 5  # prior USDC/WETH + PairCreated + 2 PoolCreated + V4 Initialize
    assert reg["pool"].n_unique() == 5


def test_pyarrow_input_matches_polars_input() -> None:
    frame = _logs_frame(LOGS)
    from_arrow = decode_logs(frame.to_arrow(), pool_registry=PRIOR_REGISTRY)
    from_polars = decode_logs(frame, pool_registry=PRIOR_REGISTRY)
    assert from_arrow.dex_action.equals(from_polars.dex_action)
    assert isinstance(frame.to_arrow(), pa.Table)


def test_topic0_to_topic3_columns_are_accepted() -> None:
    frame = _logs_frame(fx.ALL_FIXTURES)
    split = frame.with_columns(
        pl.col("topics").list.get(i, null_on_oob=True).alias(f"topic{i}") for i in range(4)
    ).drop("topics")
    assert decode_logs(split).dex_action.equals(decode_logs(frame).dex_action)


def test_missing_column_raises() -> None:
    with pytest.raises(ValueError, match="data"):
        decode_logs(_logs_frame(fx.ALL_FIXTURES).drop("data"))


def test_empty_input_gives_empty_typed_tables() -> None:
    out = decode_logs(_logs_frame([]))
    assert out.dex_action.height == 0
    assert out.errors.height == 0
    assert all(df.height == 0 for df in out.events.values())
    assert out.events["v3_swap"].schema["amount0"] == pl.String


def test_attach_pool_info_can_be_rerun_with_a_later_registry() -> None:
    # Decode the PancakeSwap swap alone, then attach a registry learned later.
    out = decode_logs(_logs_frame([fx.PANCAKE_V3_SWAP]))
    assert out.dex_action["pool_resolved"].to_list() == [False]
    later = build_pool_registry(
        decode_logs(
            _logs_frame(
                [
                    fx.RawLog(
                        address="0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865",
                        topics=[constants.V3_POOL_CREATED, _topic_addr(WETH), _topic_addr(USDT), "0x" + _word(100)],
                        data="0x" + _word(1) + _word(int("acdb27b266142223e1e676841c1e809255fc6d07", 16)),
                        block_number=1,
                        tx_hash="0x" + "ee" * 32,
                        log_index=0,
                    )
                ]
            )
        ).events
    )
    row = attach_pool_info(out.dex_action, later).row(0, named=True)
    assert (row["dex"], row["token0"], row["token1"], row["fee"]) == ("pancakeswap", WETH, USDT, 100)
    assert row["pool_resolved"] is True


def test_null_gap_in_topic_columns_is_an_error_not_a_shift() -> None:
    # topic1 null but topic2 set: must not be read as a 2-topic log.
    frame = (
        _logs_frame([fx.V2_BURN])
        .with_columns(
            topic0=pl.col("topics").list.get(0),
            topic1=pl.lit(None, dtype=pl.String),
            topic2=pl.col("topics").list.get(2),
            topic3=pl.lit(None, dtype=pl.String),
        )
        .drop("topics")
    )
    out = decode_logs(frame)
    assert out.events["v2_burn"].height == 0
    assert out.errors.height == 1
    assert "topic1 is missing" in out.errors["error"][0]


def test_topic0_without_0x_prefix_is_recognised() -> None:
    log = fx.V2_SYNC
    out = decode_logs(_logs_frame([fx.RawLog(log.address, [log.topics[0][2:]], log.data, 1, log.tx_hash, 0)]))
    assert out.events["v2_sync"].height == 1
