"""Constants for the AWS extraction: source location and the log topics we keep.

The topic0 hashes are keccak256 of the event signatures. ``tests/extract/test_constants.py``
recomputes every hash from its signature, so a typo here fails the tests.
"""

from __future__ import annotations

from typing import NamedTuple

AWS_BUCKET = "aws-public-blockchain"
AWS_PREFIX = "v1.0/eth"
AWS_REGION = "us-east-2"

TABLES: tuple[str, ...] = ("blocks", "transactions", "logs", "traces", "contracts")


class EventTopic(NamedTuple):
    signature: str
    topic0: str  # 0x-prefixed lowercase hex of keccak256(signature)


EVENT_TOPICS: dict[str, EventTopic] = {
    # ERC-20 (Transfer shares its topic0 with ERC-721 Transfer; both are kept).
    "ERC20_TRANSFER": EventTopic(
        "Transfer(address,address,uint256)",
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
    ),
    "ERC20_APPROVAL": EventTopic(
        "Approval(address,address,uint256)",
        "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",
    ),
    # Uniswap V2 factory and pair (and forks with the same ABI).
    "V2_PAIR_CREATED": EventTopic(
        "PairCreated(address,address,address,uint256)",
        "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9",
    ),
    "V2_SWAP": EventTopic(
        "Swap(address,uint256,uint256,uint256,uint256,address)",
        "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
    ),
    "V2_MINT": EventTopic(
        "Mint(address,uint256,uint256)",
        "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f",
    ),
    "V2_BURN": EventTopic(
        "Burn(address,uint256,uint256,address)",
        "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496",
    ),
    "V2_SYNC": EventTopic(
        "Sync(uint112,uint112)",
        "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1",
    ),
    # Uniswap V3 factory and pool (and forks with the same ABI).
    "V3_POOL_CREATED": EventTopic(
        "PoolCreated(address,address,uint24,int24,address)",
        "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
    ),
    "V3_INITIALIZE": EventTopic(
        "Initialize(uint160,int24)",
        "0x98636036cb66a9c19a37435efc1e90142190214e8abeb821bdba3f2990dd4c95",
    ),
    "V3_SWAP": EventTopic(
        "Swap(address,address,int256,int256,uint160,uint128,int24)",
        "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67",
    ),
    "V3_MINT": EventTopic(
        "Mint(address,address,int24,int24,uint128,uint256,uint256)",
        "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde",
    ),
    "V3_BURN": EventTopic(
        "Burn(address,int24,int24,uint128,uint256,uint256)",
        "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c",
    ),
    "V3_COLLECT": EventTopic(
        "Collect(address,address,int24,int24,uint128,uint128)",
        "0x70935338e69775456a85ddef226c395fb668b63fa0115f5f20610b388e6ca9c0",
    ),
    # Uniswap V4 PoolManager (a singleton; pools are keyed by a bytes32 id).
    "V4_INITIALIZE": EventTopic(
        "Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)",
        "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438",
    ),
    "V4_MODIFY_LIQUIDITY": EventTopic(
        "ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)",
        "0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec",
    ),
    "V4_SWAP": EventTopic(
        "Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)",
        "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f",
    ),
}

# topic0 values the logs filter keeps.
LOG_TOPIC0S: tuple[str, ...] = tuple(sorted({e.topic0 for e in EVENT_TOPICS.values()}))
