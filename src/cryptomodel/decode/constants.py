"""topic0 hashes of the decoded events.

topic0 is keccak256 of the canonical event signature. There is no keccak in the
project dependencies (hashlib's sha3_256 uses different padding), so the hashes
are hardcoded here and checked against a pure-Python Keccak-256 in
`tests/decode/test_constants.py`.

Uniswap's forks (SushiSwap, PancakeSwap, ShibaSwap and others) emit the same
events, so these hashes cover them too. PancakeSwap V3's Swap is the exception:
it appends two protocol-fee fields, which changes the signature and the hash.
"""

# ERC-20
ERC20_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ERC20_APPROVAL = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"

# Uniswap V2 factory and pair
V2_PAIR_CREATED = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
V2_MINT = "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"
V2_BURN = "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496"
V2_SWAP = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
V2_SYNC = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"

# Uniswap V3 factory and pool
V3_POOL_CREATED = "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"
V3_INITIALIZE = "0x98636036cb66a9c19a37435efc1e90142190214e8abeb821bdba3f2990dd4c95"
V3_MINT = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
V3_BURN = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c"
V3_SWAP = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
V3_COLLECT = "0x70935338e69775456a85ddef226c395fb668b63fa0115f5f20610b388e6ca9c0"
PANCAKESWAP_V3_SWAP = (
    "0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83"
)

# Uniswap V4 PoolManager
V4_INITIALIZE = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"
V4_MODIFY_LIQUIDITY = (
    "0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec"
)
V4_SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"

EVENT_SIGNATURES: dict[str, str] = {
    ERC20_TRANSFER: "Transfer(address,address,uint256)",
    ERC20_APPROVAL: "Approval(address,address,uint256)",
    V2_PAIR_CREATED: "PairCreated(address,address,address,uint256)",
    V2_MINT: "Mint(address,uint256,uint256)",
    V2_BURN: "Burn(address,uint256,uint256,address)",
    V2_SWAP: "Swap(address,uint256,uint256,uint256,uint256,address)",
    V2_SYNC: "Sync(uint112,uint112)",
    V3_POOL_CREATED: "PoolCreated(address,address,uint24,int24,address)",
    V3_INITIALIZE: "Initialize(uint160,int24)",
    V3_MINT: "Mint(address,address,int24,int24,uint128,uint256,uint256)",
    V3_BURN: "Burn(address,int24,int24,uint128,uint256,uint256)",
    V3_SWAP: "Swap(address,address,int256,int256,uint160,uint128,int24)",
    V3_COLLECT: "Collect(address,address,int24,int24,uint128,uint128)",
    PANCAKESWAP_V3_SWAP: (
        "Swap(address,address,int256,int256,uint160,uint128,int24,uint128,uint128)"
    ),
    V4_INITIALIZE: (
        "Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)"
    ),
    V4_MODIFY_LIQUIDITY: "ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)",
    V4_SWAP: "Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)",
}
"""topic0 -> canonical event signature, for every event this package decodes."""
