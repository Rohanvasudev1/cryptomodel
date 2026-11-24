"""Decode each real fixture log and check the values.

Expected values are the fixture words read by hand (int(word, 16), two's
complement for signed types); see `_decode_fixtures.py` for sources.
"""

import _decode_fixtures as fx

from cryptomodel.decode import events as ev
from cryptomodel.decode.events import decode_log


def _decode(log: fx.RawLog) -> ev.DecodedEvent | None:
    return decode_log(log.address, log.topics, log.data)


def test_v2_pair_created() -> None:
    assert _decode(fx.V2_PAIR_CREATED) == ev.V2PairCreated(
        factory="0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
        token0="0x69420a491074b8a0c1238545f7eae62240a5bdb5",
        token1="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        pair="0x3ac69e914905577af1c325e6ef7ad9d76e1567ef",
        pair_index=528541,
    )


def test_v2_mint() -> None:
    assert _decode(fx.V2_MINT) == ev.V2Mint(
        pair="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
        sender="0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
        amount0=13838068007474,
        amount1=8254770088991244858758,
    )


def test_v2_burn() -> None:
    assert _decode(fx.V2_BURN) == ev.V2Burn(
        pair="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
        sender="0x0ea041260095b20feda41ef4fdbef7d801f4c438",
        amount0=13838068007473,
        amount1=8254770088991216190436,
        to="0x0ea041260095b20feda41ef4fdbef7d801f4c438",
    )


def test_v2_sync() -> None:
    assert _decode(fx.V2_SYNC) == ev.V2Sync(
        pair="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
        reserve0=8322091130298,
        reserve1=4964435491700923364088,
    )


def test_v2_swap() -> None:
    assert _decode(fx.V2_SWAP) == ev.V2Swap(
        pair="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
        sender="0x51c72848c68a965f66fa7a88855f9f7784502a7f",
        amount0_in=0,
        amount1_in=379930928284193792,
        amount0_out=635030774,
        amount1_out=0,
        to="0x51c72848c68a965f66fa7a88855f9f7784502a7f",
    )


def test_v3_pool_created() -> None:
    assert _decode(fx.V3_POOL_CREATED) == ev.V3PoolCreated(
        factory="0x1f98431c8ad98523631ae4a59f267346ea31f984",
        token0="0x51ef2fabd68c08b3eb2fe4200bb5b16d6425d813",
        token1="0xdac17f958d2ee523a2206206994597c13d831ec7",
        fee=3000,
        tick_spacing=60,
        pool="0xb49d3e76d953c72ea2872893048597108f68db2b",
    )


def test_v3_initialize_negative_tick() -> None:
    assert _decode(fx.V3_INITIALIZE) == ev.V3Initialize(
        pool="0xb49d3e76d953c72ea2872893048597108f68db2b",
        sqrt_price_x96=4306310044,
        tick=-887220,
    )


def test_v3_mint() -> None:
    assert _decode(fx.V3_MINT) == ev.V3Mint(
        pool="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        sender="0xc36442b4a4522e871399cd717abdd847ab11fe88",
        owner="0xc36442b4a4522e871399cd717abdd847ab11fe88",
        tick_lower=199360,
        tick_upper=202860,
        amount=1741916136209,
        amount0=2807634,
        amount1=5362671550427486,
    )


def test_v3_burn() -> None:
    assert _decode(fx.V3_BURN) == ev.V3Burn(
        pool="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        owner="0xc36442b4a4522e871399cd717abdd847ab11fe88",
        tick_lower=200790,
        tick_upper=201520,
        amount=441396993045310,
        amount0=0,
        amount1=375778185250911516,
    )


def test_v3_collect() -> None:
    assert _decode(fx.V3_COLLECT) == ev.V3Collect(
        pool="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        owner="0xc36442b4a4522e871399cd717abdd847ab11fe88",
        recipient="0xc36442b4a4522e871399cd717abdd847ab11fe88",
        tick_lower=199360,
        tick_upper=202860,
        amount0=1352893,
        amount1=788840623508168,
    )


def test_v3_swap_signed_amounts() -> None:
    assert _decode(fx.V3_SWAP) == ev.V3Swap(
        pool="0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
        sender="0x51c72848c68a965f66fa7a88855f9f7784502a7f",
        recipient="0x51c72848c68a965f66fa7a88855f9f7784502a7f",
        amount0=4771584991105934336,
        amount1=-7984010464,
        sqrt_price_x96=3245604997350702951971785,
        liquidity=2720127981192773887,
        tick=-202066,
        protocol_fees_token0=None,
        protocol_fees_token1=None,
    )


def test_pancakeswap_v3_swap_is_a_v3_swap_with_protocol_fees() -> None:
    assert _decode(fx.PANCAKE_V3_SWAP) == ev.V3Swap(
        pool="0xacdb27b266142223e1e676841c1e809255fc6d07",
        sender="0x6747bcaf9bd5a5f0758cbe08903490e45ddfacb5",
        recipient="0x8feab81d36e7576107d5de0758c1b839be31b4f6",
        amount0=-1178482259542562,
        amount1=1983000,
        sqrt_price_x96=3249842245926807128721878,
        liquidity=2254382324561847,
        tick=-202040,
        protocol_fees_token0=0,
        protocol_fees_token1=23,
    )


def test_v4_initialize() -> None:
    assert _decode(fx.V4_INITIALIZE) == ev.V4Initialize(
        pool_manager="0x000000000004444c5dc75cb358380d2e3de08a90",
        pool_id="0x08988e4385fdd636e5de72bb70ad196e871eefa8fdd66af937035aedef2e6c2a",
        currency0="0xc4441c2be5d8fa8126822b9929ca0b81ea0de38e",
        currency1="0xee71175198dd55d72246dfea4d8196188430426f",
        fee=999961,
        tick_spacing=19004,
        hooks="0x0000000000000000000000000000000000000000",
        sqrt_price_x96=1366201380011688547838717801816,
        tick=56952,
    )


def test_v4_modify_liquidity() -> None:
    assert _decode(fx.V4_MODIFY_LIQUIDITY) == ev.V4ModifyLiquidity(
        pool_manager="0x000000000004444c5dc75cb358380d2e3de08a90",
        pool_id="0x21c67e77068de97969ba93d4aab21826d33ca12bb9f565d8496e8fda8a82ca27",
        sender="0xbd216513d74c8cf14cf4747e6aaa6420ff64ee9e",
        tick_lower=-202080,
        tick_upper=-202070,
        liquidity_delta=11352911822593196032,
        salt="0x00000000000000000000000000000000000000000000000000000000000817db",
    )


def test_v4_swap() -> None:
    assert _decode(fx.V4_SWAP) == ev.V4Swap(
        pool_manager="0x000000000004444c5dc75cb358380d2e3de08a90",
        pool_id="0xb80eb6a392d33eb1b014656b31b96edf9aa16c39c0baa5dbf7492435327516ea",
        sender="0x66a9893cc07d91d95644aedd05d03f95e1dba8af",
        amount0=819785390279743211,
        amount1=-259741301662557053331753,
        sqrt_price_x96=44922937928362125308274317646089,
        liquidity=31627551493412811474352,
        tick=126813,
        fee=0,
    )


def test_erc20_transfer() -> None:
    assert _decode(fx.ERC20_TRANSFER) == ev.Erc20Transfer(
        token="0xdac17f958d2ee523a2206206994597c13d831ec7",
        from_address="0x000000000004444c5dc75cb358380d2e3de08a90",
        to_address="0x51c72848c68a965f66fa7a88855f9f7784502a7f",
        value=1480254922,
    )


def test_erc20_approval() -> None:
    assert _decode(fx.ERC20_APPROVAL) == ev.Erc20Approval(
        token="0xdac17f958d2ee523a2206206994597c13d831ec7",
        owner="0x88c9a2637b17a4a900dce114df5ef0daa0533032",
        spender="0x0439e60f02a8900a951603950d8d4527f400c3f1",
        value=95017847,
    )


def test_every_fixture_has_a_distinct_kind() -> None:
    kinds = [type(_decode(log)).__name__ for log in fx.ALL_FIXTURES]
    # PancakeSwap V3 Swap decodes to V3Swap, so 16 kinds for 17 fixtures.
    assert len(set(kinds)) == 16


def test_decoding_is_case_insensitive() -> None:
    log = fx.V2_SWAP
    upper = decode_log(
        log.address.upper().replace("0X", "0x"),
        [t.upper().replace("0X", "0x") for t in log.topics],
        log.data.upper().replace("0X", "0x"),
    )
    assert upper == _decode(log)
