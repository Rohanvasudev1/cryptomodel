"""Known DEX factory (and V4 PoolManager) addresses on Ethereum mainnet.

Events are decoded by topic0 whatever contract emits them, so forks are decoded
too. This registry only labels a pool's creator with a `dex` and `version`.
Each address below was checked on 2026-11-24 with an `eth_call` against
mainnet: `allPairsLength()` for V2 factories and `feeAmountTickSpacing(500)` for
V3 factories both returned non-zero.
"""

from dataclasses import dataclass

UNKNOWN_FORK = "unknown_fork"


@dataclass(frozen=True, slots=True)
class KnownFactory:
    address: str
    dex: str
    version: str


_FACTORIES = [
    KnownFactory("0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f", "uniswap", "v2"),
    KnownFactory("0xc0aee478e3658e2610c5f7a4a2e1777ce9e4f2ac", "sushiswap", "v2"),
    KnownFactory("0x1097053fd2ea711dad45caccc45eff7548fcb362", "pancakeswap", "v2"),
    KnownFactory("0x115934131916c8b277dd010ee02de363c09d037c", "shibaswap", "v2"),
    KnownFactory("0x9deb29c9a4c7a88a3c0257393b7f3335338d9a9d", "defiswap", "v2"),
    KnownFactory("0x1f98431c8ad98523631ae4a59f267346ea31f984", "uniswap", "v3"),
    KnownFactory("0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865", "pancakeswap", "v3"),
    KnownFactory("0xbaceb8ec6b9355dfc0269c18bac9d6e2bdc29c4f", "sushiswap", "v3"),
    KnownFactory("0x000000000004444c5dc75cb358380d2e3de08a90", "uniswap", "v4"),
]

KNOWN_FACTORIES: dict[str, KnownFactory] = {f.address: f for f in _FACTORIES}
"""Lowercase address -> factory label."""


def factory_label(address: str, layout_version: str) -> tuple[str, str]:
    """Return `(dex, version)` for a creating contract.

    `layout_version` is the version implied by the event layout (`v2`, `v3` or
    `v4`); it is used for factories not in the registry, whose dex is
    `unknown_fork`.
    """
    known = KNOWN_FACTORIES.get(address.lower())
    if known is None:
        return UNKNOWN_FORK, layout_version
    return known.dex, known.version
