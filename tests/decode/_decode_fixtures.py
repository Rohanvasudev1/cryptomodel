"""Real Ethereum mainnet logs, one per event type, used as decode fixtures.

Source for every fixture: `eth_getLogs` / `eth_getTransactionReceipt` against
Ethereum mainnet through the public RPC `https://ethereum-rpc.publicnode.com`,
fetched 2026-11-24. Each log can be checked on Etherscan at
`https://etherscan.io/tx/<tx_hash>#eventlog` (the log index is given in hex there
too). The ERC-20 Transfer fixture is the first row of the AWS Public Blockchain
Data file `s3://aws-public-blockchain/v1.0/eth/logs/date=2026-11-20/part-00000-...`.

Hex strings are lowercase with a `0x` prefix, as in the AWS logs table.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RawLog:
    address: str
    topics: list[str]
    data: str
    block_number: int
    tx_hash: str
    log_index: int


def word(value: int) -> str:
    """Encode an int as one ABI word, two's complement for negatives (no 0x)."""
    return f"{value % (1 << 256):064x}"


def topic_addr(address: str) -> str:
    """An address as an indexed-topic word."""
    return "0x" + address[2:].rjust(64, "0")


def _t(word: str) -> str:
    return "0x" + word.rjust(64, "0")


# Uniswap V2 Factory PairCreated: new pair 0x3ac6...67ef for 0x6942...bdb5 / WETH.
# https://etherscan.io/tx/0x1aebac9442092e61b7bb2e3b6b67c07a495189b706c975769de1c50035c445db
V2_PAIR_CREATED = RawLog(
    address="0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
    topics=[
        "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9",
        _t("69420a491074b8a0c1238545f7eae62240a5bdb5"),
        _t("c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"),
    ],
    data="0x0000000000000000000000003ac69e914905577af1c325e6ef7ad9d76e1567ef"
    "000000000000000000000000000000000000000000000000000000000008109d",
    block_number=0x19417DD,
    tx_hash="0x1aebac9442092e61b7bb2e3b6b67c07a495189b706c975769de1c50035c445db",
    log_index=0x2EC,
)

# Uniswap V2 USDC/WETH pair 0xb4e1...c9dc. Mint and Burn come from the same
# remove-and-re-add transaction.
# https://etherscan.io/tx/0x9b098b081532f72647987b11a1e823f1567bb0f7c59006790339a7a5238d27bd
V2_MINT = RawLog(
    address="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
    topics=[
        "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f",
        _t("7a250d5630b4cf539739df2c5dacb4c659f2488d"),
    ],
    data="0x00000000000000000000000000000000000000000000000000000c95ed20c232"
    "0000000000000000000000000000000000000000000001bf7df29c4a8aceb586",
    block_number=0x1941627,
    tx_hash="0x9b098b081532f72647987b11a1e823f1567bb0f7c59006790339a7a5238d27bd",
    log_index=0x4B7,
)
V2_BURN = RawLog(
    address="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
    topics=[
        "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496",
        _t("0ea041260095b20feda41ef4fdbef7d801f4c438"),
        _t("0ea041260095b20feda41ef4fdbef7d801f4c438"),
    ],
    data="0x00000000000000000000000000000000000000000000000000000c95ed20c231"
    "0000000000000000000000000000000000000000000001bf7df29c4a891943e4",
    block_number=0x1941627,
    tx_hash="0x9b098b081532f72647987b11a1e823f1567bb0f7c59006790339a7a5238d27bd",
    log_index=0x4DF,
)

# Uniswap V2 USDC/WETH Sync then Swap (WETH in, USDC out).
# https://etherscan.io/tx/0x281773f200bf04eb8ffbdcd04c4a9d9e96bc8a5572d48ef2ab80f0c9ab823267
V2_SYNC = RawLog(
    address="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
    topics=["0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"],
    data="0x00000000000000000000000000000000000000000000000000000791a3491dba"
    "00000000000000000000000000000000000000000000010d1f61e0fed73af2f8",
    block_number=0x19426D5,
    tx_hash="0x281773f200bf04eb8ffbdcd04c4a9d9e96bc8a5572d48ef2ab80f0c9ab823267",
    log_index=0xB5,
)
V2_SWAP = RawLog(
    address="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
    topics=[
        "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
        _t("51c72848c68a965f66fa7a88855f9f7784502a7f"),
        _t("51c72848c68a965f66fa7a88855f9f7784502a7f"),
    ],
    data="0x0000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000545c92a93905400"
    "0000000000000000000000000000000000000000000000000000000025d9ccf6"
    "0000000000000000000000000000000000000000000000000000000000000000",
    block_number=0x19426D5,
    tx_hash="0x281773f200bf04eb8ffbdcd04c4a9d9e96bc8a5572d48ef2ab80f0c9ab823267",
    log_index=0xB6,
)

# Uniswap V3 Factory PoolCreated (fee 3000) and the new pool's Initialize.
# https://etherscan.io/tx/0x5f244476d6836db46142d48c415f309eef739899a93fc0c74a90cafb4fb057d2
V3_POOL_CREATED = RawLog(
    address="0x1f98431c8ad98523631ae4a59f267346ea31f984",
    topics=[
        "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
        _t("51ef2fabd68c08b3eb2fe4200bb5b16d6425d813"),
        _t("dac17f958d2ee523a2206206994597c13d831ec7"),
        _t("bb8"),
    ],
    data="0x000000000000000000000000000000000000000000000000000000000000003c"
    "000000000000000000000000b49d3e76d953c72ea2872893048597108f68db2b",
    block_number=0x1941B8E,
    tx_hash="0x5f244476d6836db46142d48c415f309eef739899a93fc0c74a90cafb4fb057d2",
    log_index=0x30,
)
V3_INITIALIZE = RawLog(
    address="0xb49d3e76d953c72ea2872893048597108f68db2b",
    topics=["0x98636036cb66a9c19a37435efc1e90142190214e8abeb821bdba3f2990dd4c95"],
    data="0x0000000000000000000000000000000000000000000000000000000100ad139c"
    "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2764c",
    block_number=0x1941B8E,
    tx_hash="0x5f244476d6836db46142d48c415f309eef739899a93fc0c74a90cafb4fb057d2",
    log_index=0x31,
)

# Uniswap V3 USDC/WETH 0.05% pool 0x88e6...5640, minted through the
# NonfungiblePositionManager 0xc364...fe88.
# https://etherscan.io/tx/0x23ae4287035162d8a1565c23fb254334a664c5c31ac4afd8c421e331d40d750f
V3_MINT = RawLog(
    address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
    topics=[
        "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde",
        _t("c36442b4a4522e871399cd717abdd847ab11fe88"),
        _t("30ac0"),
        _t("3186c"),
    ],
    data="0x000000000000000000000000c36442b4a4522e871399cd717abdd847ab11fe88"
    "00000000000000000000000000000000000000000000000000000195924ae311"
    "00000000000000000000000000000000000000000000000000000000002ad752"
    "00000000000000000000000000000000000000000000000000130d5244cf715e",
    block_number=0x1941FA7,
    tx_hash="0x23ae4287035162d8a1565c23fb254334a664c5c31ac4afd8c421e331d40d750f",
    log_index=0xE2,
)
# https://etherscan.io/tx/0x7404a1ffae88b50477013e78b03822d33353865890e2a1ec986680c521836319
V3_BURN = RawLog(
    address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
    topics=[
        "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c",
        _t("c36442b4a4522e871399cd717abdd847ab11fe88"),
        _t("31056"),
        _t("31330"),
    ],
    data="0x00000000000000000000000000000000000000000000000000019172bef9b33e"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000005370844be38b51c",
    block_number=0x1941FA3,
    tx_hash="0x7404a1ffae88b50477013e78b03822d33353865890e2a1ec986680c521836319",
    log_index=0x170,
)
# https://etherscan.io/tx/0xe7f3605d4f69cd4f1ff78adce26789db9c84182451fa027f6e9ca197aac6bd43
V3_COLLECT = RawLog(
    address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
    topics=[
        "0x70935338e69775456a85ddef226c395fb668b63fa0115f5f20610b388e6ca9c0",
        _t("c36442b4a4522e871399cd717abdd847ab11fe88"),
        _t("30ac0"),
        _t("3186c"),
    ],
    data="0x000000000000000000000000c36442b4a4522e871399cd717abdd847ab11fe88"
    "000000000000000000000000000000000000000000000000000000000014a4bd"
    "0000000000000000000000000000000000000000000000000002cd7245260ac8",
    block_number=0x1941F97,
    tx_hash="0xe7f3605d4f69cd4f1ff78adce26789db9c84182451fa027f6e9ca197aac6bd43",
    log_index=0x5B,
)
# Uniswap V3 WETH/USDT 0.3% pool 0x4e68...fa36: WETH in, USDT out, negative tick.
# https://etherscan.io/tx/0x9d1ab4a753c6d444e63d271ba70405000419f43bd8570c078e417cace8140f91
V3_SWAP = RawLog(
    address="0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
    topics=[
        "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67",
        _t("51c72848c68a965f66fa7a88855f9f7784502a7f"),
        _t("51c72848c68a965f66fa7a88855f9f7784502a7f"),
    ],
    data="0x00000000000000000000000000000000000000000000000042381344ba746400"
    "fffffffffffffffffffffffffffffffffffffffffffffffffffffffe241dab20"
    "00000000000000000000000000000000000000000002af489976123400003bc9"
    "00000000000000000000000000000000000000000000000025bfd5fcae9880ff"
    "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffceaae",
    block_number=0x19426D5,
    tx_hash="0x9d1ab4a753c6d444e63d271ba70405000419f43bd8570c078e417cace8140f91",
    log_index=0x4C,
)
# PancakeSwap V3 WETH/USDT 0.01% pool 0xacdb...6d07 (pool address from
# PancakeSwap V3 Factory getPool). Its Swap has two extra protocol-fee words.
# https://etherscan.io/tx/0x6d2c93cfd8914dc281705606750d0cf98d4aca16db66f624887bf77fe38b8afd
PANCAKE_V3_SWAP = RawLog(
    address="0xacdb27b266142223e1e676841c1e809255fc6d07",
    topics=[
        "0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83",
        _t("6747bcaf9bd5a5f0758cbe08903490e45ddfacb5"),
        _t("8feab81d36e7576107d5de0758c1b839be31b4f6"),
    ],
    data="0xfffffffffffffffffffffffffffffffffffffffffffffffffffbd02d378bbdde"
    "00000000000000000000000000000000000000000000000000000000001e4218"
    "00000000000000000000000000000000000000000002b02e4d190c43c72f49d6"
    "0000000000000000000000000000000000000000000000000008025949a4b7b7"
    "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffceac8"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000017",
    block_number=0x1941F15,
    tx_hash="0x6d2c93cfd8914dc281705606750d0cf98d4aca16db66f624887bf77fe38b8afd",
    log_index=0x222,
)

# Uniswap V4 PoolManager 0x0000...8a90.
# https://etherscan.io/tx/0xe50c32cc7d620291440b4ef38d67f453e2707a54f502ca90d76029fe834f3633
V4_INITIALIZE = RawLog(
    address="0x000000000004444c5dc75cb358380d2e3de08a90",
    topics=[
        "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438",
        "0x08988e4385fdd636e5de72bb70ad196e871eefa8fdd66af937035aedef2e6c2a",
        _t("c4441c2be5d8fa8126822b9929ca0b81ea0de38e"),
        _t("ee71175198dd55d72246dfea4d8196188430426f"),
    ],
    data="0x00000000000000000000000000000000000000000000000000000000000f4219"
    "0000000000000000000000000000000000000000000000000000000000004a3c"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000113e6f4b5d117f2d9c796f3558"
    "000000000000000000000000000000000000000000000000000000000000de78",
    block_number=0x1941F14,
    tx_hash="0xe50c32cc7d620291440b4ef38d67f453e2707a54f502ca90d76029fe834f3633",
    log_index=0x6F7,
)
# https://etherscan.io/tx/0x3cc9ecbb637fb42468e1ff2bf36eb3d279dc71c32d3599a167f6d7877647e609
V4_MODIFY_LIQUIDITY = RawLog(
    address="0x000000000004444c5dc75cb358380d2e3de08a90",
    topics=[
        "0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec",
        "0x21c67e77068de97969ba93d4aab21826d33ca12bb9f565d8496e8fda8a82ca27",
        _t("bd216513d74c8cf14cf4747e6aaa6420ff64ee9e"),
    ],
    data="0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffceaa0"
    "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffceaaa"
    "0000000000000000000000000000000000000000000000009d8da52700000000"
    "00000000000000000000000000000000000000000000000000000000000817db",
    block_number=0x19426B0,
    tx_hash="0x3cc9ecbb637fb42468e1ff2bf36eb3d279dc71c32d3599a167f6d7877647e609",
    log_index=0x44,
)
# Native ETH (currency0) out to the swapper, token 0x8fd1...2ed5 (currency1) in.
# The same receipt shows a Transfer of 259741301662557053331753 of 0x8fd1...2ed5
# into the PoolManager, which fixes V4's sign convention (negative = user paid).
# https://etherscan.io/tx/0x4f451db983ee5fc7b04d907dd195b5ce011261e5680c9e93c1eb4e7c17928cd5
V4_SWAP = RawLog(
    address="0x000000000004444c5dc75cb358380d2e3de08a90",
    topics=[
        "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f",
        "0xb80eb6a392d33eb1b014656b31b96edf9aa16c39c0baa5dbf7492435327516ea",
        _t("66a9893cc07d91d95644aedd05d03f95e1dba8af"),
    ],
    data="0x0000000000000000000000000000000000000000000000000b60767813add6eb"
    "ffffffffffffffffffffffffffffffffffffffffffffc8ff6554a24cec78d6d7"
    "000000000000000000000000000000000000023701d75032158847e8ba86d909"
    "0000000000000000000000000000000000000000000006b28872d14f35e485b0"
    "000000000000000000000000000000000000000000000000000000000001ef5d"
    "0000000000000000000000000000000000000000000000000000000000000000",
    block_number=0x19426D8,
    tx_hash="0x4f451db983ee5fc7b04d907dd195b5ce011261e5680c9e93c1eb4e7c17928cd5",
    log_index=0x109,
)

# USDT (0xdac1...1ec7) Transfer, first row of the AWS logs file above.
# https://etherscan.io/tx/0x2eca226b6114f0e5ccb991b5b0ec7ac4750d06ab5bb4c6e40d446c8a2d340a77
ERC20_TRANSFER = RawLog(
    address="0xdac17f958d2ee523a2206206994597c13d831ec7",
    topics=[
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        _t("4444c5dc75cb358380d2e3de08a90"),
        _t("51c72848c68a965f66fa7a88855f9f7784502a7f"),
    ],
    data="0x00000000000000000000000000000000000000000000000000000000583ae5ca",
    block_number=26453797,
    tx_hash="0x2eca226b6114f0e5ccb991b5b0ec7ac4750d06ab5bb4c6e40d446c8a2d340a77",
    log_index=185,
)
# https://etherscan.io/tx/0x428cb2438e7d50775525335b53792478deea6e48031064f1d38cec0958e520b8
ERC20_APPROVAL = RawLog(
    address="0xdac17f958d2ee523a2206206994597c13d831ec7",
    topics=[
        "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",
        _t("88c9a2637b17a4a900dce114df5ef0daa0533032"),
        _t("0439e60f02a8900a951603950d8d4527f400c3f1"),
    ],
    data="0x0000000000000000000000000000000000000000000000000000000005a9db77",
    block_number=0x19426C4,
    tx_hash="0x428cb2438e7d50775525335b53792478deea6e48031064f1d38cec0958e520b8",
    log_index=0x143,
)

ALL_FIXTURES: list[RawLog] = [
    V2_PAIR_CREATED,
    V2_MINT,
    V2_BURN,
    V2_SYNC,
    V2_SWAP,
    V3_POOL_CREATED,
    V3_INITIALIZE,
    V3_MINT,
    V3_BURN,
    V3_COLLECT,
    V3_SWAP,
    PANCAKE_V3_SWAP,
    V4_INITIALIZE,
    V4_MODIFY_LIQUIDITY,
    V4_SWAP,
    ERC20_TRANSFER,
    ERC20_APPROVAL,
]
