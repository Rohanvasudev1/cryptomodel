"""Pure decoders for single event logs.

Each decoder takes the emitting address, the topics (topic0 first) and the data
of one log, as lowercase or mixed-case hex strings, and returns a frozen
dataclass. Amounts are exact Python ints; signed types stay signed. Addresses
come back as lowercase `0x` strings.

`decode_log` dispatches on topic0 and ignores events it does not know. A log
with a known topic0 but the wrong number of topics or data words raises
`DecodeError`: some unrelated contracts reuse these signatures with a different
`indexed` layout, and they must not be read as DEX events. ERC-721 `Transfer`
and `Approval` share topic0 with ERC-20 but have four topics; they are ignored.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import ClassVar

from cryptomodel.decode import constants as c
from cryptomodel.decode._abi import (
    DecodeError,
    as_address,
    as_bytes32,
    as_int,
    as_uint,
    data_words,
    normalize_hex,
    topic_words,
)

__all__ = [
    "DecodeError",
    "DecodedEvent",
    "Erc20Approval",
    "Erc20Transfer",
    "V2Burn",
    "V2Mint",
    "V2PairCreated",
    "V2Swap",
    "V2Sync",
    "V3Burn",
    "V3Collect",
    "V3Initialize",
    "V3Mint",
    "V3PoolCreated",
    "V3Swap",
    "V4Initialize",
    "V4ModifyLiquidity",
    "V4Swap",
    "decode_log",
]

Topics = Sequence[str | None]


@dataclass(frozen=True, slots=True)
class V2PairCreated:
    KIND: ClassVar[str] = "v2_pair_created"
    factory: str
    token0: str
    token1: str
    pair: str
    pair_index: int  # allPairs.length after creation


@dataclass(frozen=True, slots=True)
class V2Mint:
    KIND: ClassVar[str] = "v2_mint"
    pair: str
    sender: str
    amount0: int
    amount1: int


@dataclass(frozen=True, slots=True)
class V2Burn:
    KIND: ClassVar[str] = "v2_burn"
    pair: str
    sender: str
    amount0: int
    amount1: int
    to: str


@dataclass(frozen=True, slots=True)
class V2Swap:
    KIND: ClassVar[str] = "v2_swap"
    pair: str
    sender: str
    amount0_in: int
    amount1_in: int
    amount0_out: int
    amount1_out: int
    to: str


@dataclass(frozen=True, slots=True)
class V2Sync:
    KIND: ClassVar[str] = "v2_sync"
    pair: str
    reserve0: int
    reserve1: int


@dataclass(frozen=True, slots=True)
class V3PoolCreated:
    KIND: ClassVar[str] = "v3_pool_created"
    factory: str
    token0: str
    token1: str
    fee: int
    tick_spacing: int
    pool: str


@dataclass(frozen=True, slots=True)
class V3Initialize:
    KIND: ClassVar[str] = "v3_initialize"
    pool: str
    sqrt_price_x96: int
    tick: int


@dataclass(frozen=True, slots=True)
class V3Mint:
    KIND: ClassVar[str] = "v3_mint"
    pool: str
    sender: str
    owner: str
    tick_lower: int
    tick_upper: int
    amount: int  # liquidity added
    amount0: int
    amount1: int


@dataclass(frozen=True, slots=True)
class V3Burn:
    KIND: ClassVar[str] = "v3_burn"
    pool: str
    owner: str
    tick_lower: int
    tick_upper: int
    amount: int  # liquidity removed
    amount0: int
    amount1: int


@dataclass(frozen=True, slots=True)
class V3Swap:
    """Uniswap V3 Swap, or the PancakeSwap V3 variant with protocol fees.

    amount0 and amount1 are the pool's balance changes: positive means the
    token went into the pool.
    """

    KIND: ClassVar[str] = "v3_swap"
    pool: str
    sender: str
    recipient: str
    amount0: int
    amount1: int
    sqrt_price_x96: int
    liquidity: int
    tick: int
    protocol_fees_token0: int | None  # PancakeSwap V3 only
    protocol_fees_token1: int | None  # PancakeSwap V3 only


@dataclass(frozen=True, slots=True)
class V3Collect:
    KIND: ClassVar[str] = "v3_collect"
    pool: str
    owner: str
    recipient: str
    tick_lower: int
    tick_upper: int
    amount0: int
    amount1: int


@dataclass(frozen=True, slots=True)
class V4Initialize:
    KIND: ClassVar[str] = "v4_initialize"
    pool_manager: str
    pool_id: str
    currency0: str  # 0x000...000 is native ETH
    currency1: str
    fee: int
    tick_spacing: int
    hooks: str
    sqrt_price_x96: int
    tick: int


@dataclass(frozen=True, slots=True)
class V4ModifyLiquidity:
    KIND: ClassVar[str] = "v4_modify_liquidity"
    pool_manager: str
    pool_id: str
    sender: str
    tick_lower: int
    tick_upper: int
    liquidity_delta: int  # positive adds liquidity, negative removes it
    salt: str


@dataclass(frozen=True, slots=True)
class V4Swap:
    """Uniswap V4 Swap.

    Unlike V3, amount0 and amount1 are the swapper's balance changes: negative
    means the swapper paid that currency into the pool.
    """

    KIND: ClassVar[str] = "v4_swap"
    pool_manager: str
    pool_id: str
    sender: str
    amount0: int
    amount1: int
    sqrt_price_x96: int
    liquidity: int
    tick: int
    fee: int


@dataclass(frozen=True, slots=True)
class Erc20Transfer:
    KIND: ClassVar[str] = "erc20_transfer"
    token: str
    from_address: str
    to_address: str
    value: int


@dataclass(frozen=True, slots=True)
class Erc20Approval:
    KIND: ClassVar[str] = "erc20_approval"
    token: str
    owner: str
    spender: str
    value: int


DecodedEvent = (
    V2PairCreated
    | V2Mint
    | V2Burn
    | V2Swap
    | V2Sync
    | V3PoolCreated
    | V3Initialize
    | V3Mint
    | V3Burn
    | V3Swap
    | V3Collect
    | V4Initialize
    | V4ModifyLiquidity
    | V4Swap
    | Erc20Transfer
    | Erc20Approval
)

EVENT_CLASSES: tuple[type[DecodedEvent], ...] = (
    V2PairCreated,
    V2Mint,
    V2Burn,
    V2Swap,
    V2Sync,
    V3PoolCreated,
    V3Initialize,
    V3Mint,
    V3Burn,
    V3Swap,
    V3Collect,
    V4Initialize,
    V4ModifyLiquidity,
    V4Swap,
    Erc20Transfer,
    Erc20Approval,
)


def _emitter(address: str | None) -> str:
    text = normalize_hex(address, "log address")
    if len(text) != 40:
        raise DecodeError(f"log address has {len(text)} hex chars, expected 40")
    return "0x" + text


def decode_v2_pair_created(address: str, topics: Topics, data: str) -> V2PairCreated:
    name = "V2PairCreated"
    t = topic_words(topics, 3, name)
    d = data_words(data, 2, name)
    return V2PairCreated(
        factory=_emitter(address),
        token0=as_address(t[1], f"{name}.token0"),
        token1=as_address(t[2], f"{name}.token1"),
        pair=as_address(d[0], f"{name}.pair"),
        pair_index=as_uint(d[1], 256, f"{name}.pair_index"),
    )


def decode_v2_mint(address: str, topics: Topics, data: str) -> V2Mint:
    name = "V2Mint"
    t = topic_words(topics, 2, name)
    d = data_words(data, 2, name)
    return V2Mint(
        pair=_emitter(address),
        sender=as_address(t[1], f"{name}.sender"),
        amount0=as_uint(d[0], 256, f"{name}.amount0"),
        amount1=as_uint(d[1], 256, f"{name}.amount1"),
    )


def decode_v2_burn(address: str, topics: Topics, data: str) -> V2Burn:
    name = "V2Burn"
    t = topic_words(topics, 3, name)
    d = data_words(data, 2, name)
    return V2Burn(
        pair=_emitter(address),
        sender=as_address(t[1], f"{name}.sender"),
        amount0=as_uint(d[0], 256, f"{name}.amount0"),
        amount1=as_uint(d[1], 256, f"{name}.amount1"),
        to=as_address(t[2], f"{name}.to"),
    )


def decode_v2_swap(address: str, topics: Topics, data: str) -> V2Swap:
    name = "V2Swap"
    t = topic_words(topics, 3, name)
    d = data_words(data, 4, name)
    return V2Swap(
        pair=_emitter(address),
        sender=as_address(t[1], f"{name}.sender"),
        amount0_in=as_uint(d[0], 256, f"{name}.amount0_in"),
        amount1_in=as_uint(d[1], 256, f"{name}.amount1_in"),
        amount0_out=as_uint(d[2], 256, f"{name}.amount0_out"),
        amount1_out=as_uint(d[3], 256, f"{name}.amount1_out"),
        to=as_address(t[2], f"{name}.to"),
    )


def decode_v2_sync(address: str, topics: Topics, data: str) -> V2Sync:
    name = "V2Sync"
    topic_words(topics, 1, name)
    d = data_words(data, 2, name)
    return V2Sync(
        pair=_emitter(address),
        reserve0=as_uint(d[0], 112, f"{name}.reserve0"),
        reserve1=as_uint(d[1], 112, f"{name}.reserve1"),
    )


def decode_v3_pool_created(address: str, topics: Topics, data: str) -> V3PoolCreated:
    name = "V3PoolCreated"
    t = topic_words(topics, 4, name)
    d = data_words(data, 2, name)
    return V3PoolCreated(
        factory=_emitter(address),
        token0=as_address(t[1], f"{name}.token0"),
        token1=as_address(t[2], f"{name}.token1"),
        fee=as_uint(t[3], 24, f"{name}.fee"),
        tick_spacing=as_int(d[0], 24, f"{name}.tick_spacing"),
        pool=as_address(d[1], f"{name}.pool"),
    )


def decode_v3_initialize(address: str, topics: Topics, data: str) -> V3Initialize:
    name = "V3Initialize"
    topic_words(topics, 1, name)
    d = data_words(data, 2, name)
    return V3Initialize(
        pool=_emitter(address),
        sqrt_price_x96=as_uint(d[0], 160, f"{name}.sqrt_price_x96"),
        tick=as_int(d[1], 24, f"{name}.tick"),
    )


def decode_v3_mint(address: str, topics: Topics, data: str) -> V3Mint:
    name = "V3Mint"
    t = topic_words(topics, 4, name)
    d = data_words(data, 4, name)
    return V3Mint(
        pool=_emitter(address),
        sender=as_address(d[0], f"{name}.sender"),
        owner=as_address(t[1], f"{name}.owner"),
        tick_lower=as_int(t[2], 24, f"{name}.tick_lower"),
        tick_upper=as_int(t[3], 24, f"{name}.tick_upper"),
        amount=as_uint(d[1], 128, f"{name}.amount"),
        amount0=as_uint(d[2], 256, f"{name}.amount0"),
        amount1=as_uint(d[3], 256, f"{name}.amount1"),
    )


def decode_v3_burn(address: str, topics: Topics, data: str) -> V3Burn:
    name = "V3Burn"
    t = topic_words(topics, 4, name)
    d = data_words(data, 3, name)
    return V3Burn(
        pool=_emitter(address),
        owner=as_address(t[1], f"{name}.owner"),
        tick_lower=as_int(t[2], 24, f"{name}.tick_lower"),
        tick_upper=as_int(t[3], 24, f"{name}.tick_upper"),
        amount=as_uint(d[0], 128, f"{name}.amount"),
        amount0=as_uint(d[1], 256, f"{name}.amount0"),
        amount1=as_uint(d[2], 256, f"{name}.amount1"),
    )


def _decode_v3_swap(address: str, topics: Topics, data: str, *, pancakeswap: bool) -> V3Swap:
    name = "V3Swap"
    t = topic_words(topics, 3, name)
    d = data_words(data, 7 if pancakeswap else 5, name)
    return V3Swap(
        pool=_emitter(address),
        sender=as_address(t[1], f"{name}.sender"),
        recipient=as_address(t[2], f"{name}.recipient"),
        amount0=as_int(d[0], 256, f"{name}.amount0"),
        amount1=as_int(d[1], 256, f"{name}.amount1"),
        sqrt_price_x96=as_uint(d[2], 160, f"{name}.sqrt_price_x96"),
        liquidity=as_uint(d[3], 128, f"{name}.liquidity"),
        tick=as_int(d[4], 24, f"{name}.tick"),
        protocol_fees_token0=as_uint(d[5], 128, f"{name}.protocol_fees_token0") if pancakeswap else None,
        protocol_fees_token1=as_uint(d[6], 128, f"{name}.protocol_fees_token1") if pancakeswap else None,
    )


def decode_v3_swap(address: str, topics: Topics, data: str) -> V3Swap:
    return _decode_v3_swap(address, topics, data, pancakeswap=False)


def decode_pancakeswap_v3_swap(address: str, topics: Topics, data: str) -> V3Swap:
    return _decode_v3_swap(address, topics, data, pancakeswap=True)


def decode_v3_collect(address: str, topics: Topics, data: str) -> V3Collect:
    name = "V3Collect"
    t = topic_words(topics, 4, name)
    d = data_words(data, 3, name)
    return V3Collect(
        pool=_emitter(address),
        owner=as_address(t[1], f"{name}.owner"),
        recipient=as_address(d[0], f"{name}.recipient"),
        tick_lower=as_int(t[2], 24, f"{name}.tick_lower"),
        tick_upper=as_int(t[3], 24, f"{name}.tick_upper"),
        amount0=as_uint(d[1], 128, f"{name}.amount0"),
        amount1=as_uint(d[2], 128, f"{name}.amount1"),
    )


def decode_v4_initialize(address: str, topics: Topics, data: str) -> V4Initialize:
    name = "V4Initialize"
    t = topic_words(topics, 4, name)
    d = data_words(data, 5, name)
    return V4Initialize(
        pool_manager=_emitter(address),
        pool_id=as_bytes32(t[1]),
        currency0=as_address(t[2], f"{name}.currency0"),
        currency1=as_address(t[3], f"{name}.currency1"),
        fee=as_uint(d[0], 24, f"{name}.fee"),
        tick_spacing=as_int(d[1], 24, f"{name}.tick_spacing"),
        hooks=as_address(d[2], f"{name}.hooks"),
        sqrt_price_x96=as_uint(d[3], 160, f"{name}.sqrt_price_x96"),
        tick=as_int(d[4], 24, f"{name}.tick"),
    )


def decode_v4_modify_liquidity(address: str, topics: Topics, data: str) -> V4ModifyLiquidity:
    name = "V4ModifyLiquidity"
    t = topic_words(topics, 3, name)
    d = data_words(data, 4, name)
    return V4ModifyLiquidity(
        pool_manager=_emitter(address),
        pool_id=as_bytes32(t[1]),
        sender=as_address(t[2], f"{name}.sender"),
        tick_lower=as_int(d[0], 24, f"{name}.tick_lower"),
        tick_upper=as_int(d[1], 24, f"{name}.tick_upper"),
        liquidity_delta=as_int(d[2], 256, f"{name}.liquidity_delta"),
        salt=as_bytes32(d[3]),
    )


def decode_v4_swap(address: str, topics: Topics, data: str) -> V4Swap:
    name = "V4Swap"
    t = topic_words(topics, 3, name)
    d = data_words(data, 6, name)
    return V4Swap(
        pool_manager=_emitter(address),
        pool_id=as_bytes32(t[1]),
        sender=as_address(t[2], f"{name}.sender"),
        amount0=as_int(d[0], 128, f"{name}.amount0"),
        amount1=as_int(d[1], 128, f"{name}.amount1"),
        sqrt_price_x96=as_uint(d[2], 160, f"{name}.sqrt_price_x96"),
        liquidity=as_uint(d[3], 128, f"{name}.liquidity"),
        tick=as_int(d[4], 24, f"{name}.tick"),
        fee=as_uint(d[5], 24, f"{name}.fee"),
    )


def decode_erc20_transfer(address: str, topics: Topics, data: str) -> Erc20Transfer:
    name = "Erc20Transfer"
    t = topic_words(topics, 3, name)
    d = data_words(data, 1, name)
    return Erc20Transfer(
        token=_emitter(address),
        from_address=as_address(t[1], f"{name}.from"),
        to_address=as_address(t[2], f"{name}.to"),
        value=as_uint(d[0], 256, f"{name}.value"),
    )


def decode_erc20_approval(address: str, topics: Topics, data: str) -> Erc20Approval:
    name = "Erc20Approval"
    t = topic_words(topics, 3, name)
    d = data_words(data, 1, name)
    return Erc20Approval(
        token=_emitter(address),
        owner=as_address(t[1], f"{name}.owner"),
        spender=as_address(t[2], f"{name}.spender"),
        value=as_uint(d[0], 256, f"{name}.value"),
    )


DECODERS: dict[str, Callable[[str, Topics, str], DecodedEvent]] = {
    c.V2_PAIR_CREATED: decode_v2_pair_created,
    c.V2_MINT: decode_v2_mint,
    c.V2_BURN: decode_v2_burn,
    c.V2_SWAP: decode_v2_swap,
    c.V2_SYNC: decode_v2_sync,
    c.V3_POOL_CREATED: decode_v3_pool_created,
    c.V3_INITIALIZE: decode_v3_initialize,
    c.V3_MINT: decode_v3_mint,
    c.V3_BURN: decode_v3_burn,
    c.V3_SWAP: decode_v3_swap,
    c.PANCAKESWAP_V3_SWAP: decode_pancakeswap_v3_swap,
    c.V3_COLLECT: decode_v3_collect,
    c.V4_INITIALIZE: decode_v4_initialize,
    c.V4_MODIFY_LIQUIDITY: decode_v4_modify_liquidity,
    c.V4_SWAP: decode_v4_swap,
    c.ERC20_TRANSFER: decode_erc20_transfer,
    c.ERC20_APPROVAL: decode_erc20_approval,
}
"""topic0 -> decoder."""

_ERC721_SHARED_TOPIC0 = frozenset({c.ERC20_TRANSFER, c.ERC20_APPROVAL})


def decode_log(address: str, topics: Topics, data: str) -> DecodedEvent | None:
    """Decode one log, or return None if it is not an event this package handles.

    Raises `DecodeError` when topic0 is known but the log does not fit the layout.
    """
    if not topics or topics[0] is None:
        return None
    topic0 = topics[0].lower()
    decoder = DECODERS.get(topic0)
    if decoder is None:
        return None
    if topic0 in _ERC721_SHARED_TOPIC0 and len(topics) == 4:
        return None  # ERC-721 Transfer/Approval: tokenId is the 4th topic
    return decoder(address, topics, data)
