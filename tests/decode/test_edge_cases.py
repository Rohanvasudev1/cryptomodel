"""Edge cases: extreme values, malformed logs and unknown events."""

import _decode_fixtures as fx
import pytest
from _decode_fixtures import topic_addr as _topic_addr
from _decode_fixtures import word as _word

from cryptomodel.decode import constants
from cryptomodel.decode import events as ev
from cryptomodel.decode.events import DecodeError, decode_log

ADDR = "0x" + "11" * 20


def test_most_negative_int256_round_trips() -> None:
    data = "0x" + _word(-(2**255)) + _word(2**255 - 1) + _word(2**160 - 1) + _word(2**128 - 1) + _word(-1)
    topics = [constants.V3_SWAP, _topic_addr(ADDR), _topic_addr(ADDR)]
    swap = decode_log(ADDR, topics, data)
    assert isinstance(swap, ev.V3Swap)
    assert swap.amount0 == -(2**255)
    assert swap.amount1 == 2**255 - 1
    assert swap.sqrt_price_x96 == 2**160 - 1
    assert swap.liquidity == 2**128 - 1
    assert swap.tick == -1


def test_amounts_above_2_pow_128_are_exact() -> None:
    big0 = 2**200 + 12345
    big1 = 2**256 - 1
    data = "0x" + _word(0) + _word(big0) + _word(big1) + _word(0)
    topics = [constants.V2_SWAP, _topic_addr(ADDR), _topic_addr(ADDR)]
    swap = decode_log(ADDR, topics, data)
    assert isinstance(swap, ev.V2Swap)
    assert swap.amount1_in == big0
    assert swap.amount0_out == big1
    assert str(swap.amount0_out) == "115792089237316195423570985008687907853269984665640564039457584007913129639935"


def test_unknown_topic0_is_ignored() -> None:
    assert decode_log(ADDR, ["0x" + "ab" * 32, _topic_addr(ADDR)], "0x" + _word(1)) is None


def test_log_without_topics_is_ignored() -> None:
    assert decode_log(ADDR, [], "0x") is None


def test_erc721_transfer_is_not_an_erc20_transfer() -> None:
    # ERC-721 shares Transfer's topic0 but indexes tokenId as a 4th topic.
    topics = [constants.ERC20_TRANSFER, _topic_addr(ADDR), _topic_addr(ADDR), "0x" + _word(7)]
    assert decode_log(ADDR, topics, "0x") is None


@pytest.mark.parametrize(
    "data",
    [
        fx.V2_SWAP.data[:-64],  # one word short
        fx.V2_SWAP.data[:-2],  # not a whole word
        fx.V2_SWAP.data + "00" * 32,  # one word too many
        "0x",  # empty
    ],
)
def test_wrong_data_length_raises(data: str) -> None:
    with pytest.raises(DecodeError, match="V2Swap"):
        decode_log(fx.V2_SWAP.address, fx.V2_SWAP.topics, data)


def test_wrong_topic_count_raises() -> None:
    with pytest.raises(DecodeError, match="topics"):
        decode_log(fx.V2_SWAP.address, fx.V2_SWAP.topics[:2], fx.V2_SWAP.data)


def test_non_hex_data_raises() -> None:
    with pytest.raises(DecodeError, match="hex"):
        decode_log(fx.V2_SYNC.address, fx.V2_SYNC.topics, "0x" + "zz" * 64)


def test_short_topic_raises() -> None:
    topics = [fx.V2_SWAP.topics[0], "0x1234", fx.V2_SWAP.topics[2]]
    with pytest.raises(DecodeError, match="topic"):
        decode_log(fx.V2_SWAP.address, topics, fx.V2_SWAP.data)


def test_dirty_address_word_raises() -> None:
    topics = [fx.V2_SWAP.topics[0], "0x" + "ff" * 32, fx.V2_SWAP.topics[2]]
    with pytest.raises(DecodeError, match="address"):
        decode_log(fx.V2_SWAP.address, topics, fx.V2_SWAP.data)


def test_uint112_reserve_out_of_range_raises() -> None:
    data = "0x" + _word(2**112) + _word(1)
    with pytest.raises(DecodeError, match="uint112"):
        decode_log(ADDR, [constants.V2_SYNC], data)


def test_int24_tick_out_of_range_raises() -> None:
    data = "0x" + _word(1) + _word(2**23)
    with pytest.raises(DecodeError, match="int24"):
        decode_log(ADDR, [constants.V3_INITIALIZE], data)


def test_badly_sign_extended_int_raises() -> None:
    # A negative int24 must be sign-extended across the whole word.
    data = "0x" + _word(1) + "00" * 29 + "fffffe"
    with pytest.raises(DecodeError, match="int24"):
        decode_log(ADDR, [constants.V3_INITIALIZE], data)


def test_zero_amounts_decode_as_zero_not_missing() -> None:
    data = "0x" + _word(0) * 2
    sync = decode_log(ADDR, [constants.V2_SYNC], data)
    assert sync == ev.V2Sync(pair=ADDR, reserve0=0, reserve1=0)


def test_topic0_without_0x_prefix_is_recognised() -> None:
    log = fx.V2_SYNC
    assert decode_log(log.address, [log.topics[0][2:].upper()], log.data) == decode_log(
        log.address, log.topics, log.data
    )
