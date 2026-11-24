"""Projection and filtering per table, run through the real pipeline on local fixtures."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from cryptomodel.extract.constants import EVENT_TOPICS
from cryptomodel.extract.pipeline import extract_table_day
from cryptomodel.extract.source import LocalSource

from .conftest import DAY, WriteAws, addr, h32

TRANSFER = EVENT_TOPICS["ERC20_TRANSFER"].topic0
V4_SWAP = EVENT_TOPICS["V4_SWAP"].topic0
V2_SYNC = EVENT_TOPICS["V2_SYNC"].topic0
UNRELATED = h32(0xDEADBEEF)


def run(aws_root: Path, out_root: Path, table: str) -> pa.Table:
    result = extract_table_day(LocalSource(aws_root), table, DAY, out_root)
    assert result.status == "written"
    return pq.read_table(out_root / table / f"date={DAY.isoformat()}" / "data.parquet")


# ---------------------------------------------------------------- logs


def test_logs_keep_only_listed_topics(write_aws: WriteAws, aws_root: Path, out_root: Path) -> None:
    write_aws(
        "logs",
        [
            {"topics": [TRANSFER, h32(1), h32(2)], "log_index": 0},
            {"topics": [UNRELATED, h32(1)], "log_index": 1},
            {"topics": [], "log_index": 2},  # anonymous event, no topic0
            {"topics": [V4_SWAP.upper().replace("0X", "0x"), h32(3)], "log_index": 3},
            {"topics": [V2_SYNC], "log_index": 4},
        ],
    )
    out = run(aws_root, out_root, "logs")
    assert out.column("log_index").to_pylist() == [0, 3, 4]


def test_logs_projection_and_fixed_size_binary(
    write_aws: WriteAws, aws_root: Path, out_root: Path
) -> None:
    write_aws(
        "logs",
        [
            {
                "address": addr(0xAB),
                "topics": [TRANSFER, h32(1), h32(2)],
                "data": "0x" + "00" * 31 + "05",
                "transaction_hash": h32(9),
                "block_number": 23_700_000,
                "transaction_index": 4,
                "log_index": 7,
            }
        ],
    )
    out = run(aws_root, out_root, "logs")
    s = out.schema
    assert s.field("address").type == pa.binary(20)
    for c in ("topic0", "topic1", "topic2", "topic3", "transaction_hash"):
        assert s.field(c).type == pa.binary(32), c
    assert s.field("data").type == pa.binary()
    assert "block_hash" not in s.names and "date" not in s.names
    row = out.to_pylist()[0]
    assert row["address"] == bytes.fromhex(f"{0xAB:040x}")
    assert row["topic0"] == bytes.fromhex(TRANSFER[2:])
    assert row["topic3"] is None
    assert row["transaction_hash"] == bytes.fromhex(f"{9:064x}")
    assert (row["block_number"], row["transaction_index"], row["log_index"]) == (23_700_000, 4, 7)


def test_logs_uint256_above_2_pow_53_survives_exactly(
    write_aws: WriteAws, aws_root: Path, out_root: Path
) -> None:
    amounts = [2**53 + 1, 10**30 + 7, 2**256 - 1]
    write_aws(
        "logs",
        [
            {"topics": [TRANSFER, h32(1), h32(2)], "data": "0x" + f"{a:064x}", "log_index": i}
            for i, a in enumerate(amounts)
        ],
    )
    out = run(aws_root, out_root, "logs")
    decoded = [int.from_bytes(b, "big") for b in out.column("data").to_pylist()]
    assert decoded == amounts


# ---------------------------------------------------------------- transactions


def test_transactions_projection(write_aws: WriteAws, aws_root: Path, out_root: Path) -> None:
    write_aws(
        "transactions",
        [
            {
                "hash": h32(1),
                "from_address": addr(1),
                "to_address": addr(2),
                "input": "0xa9059cbb" + "00" * 64,
                "value": 1.5e18,
                "gas": 60_000,
                "receipt_status": 1,
                "block_number": 5,
                "receipt_contract_address": "",  # AWS uses '' here, not 'None'
            },
            {  # contract creation: AWS writes the missing to_address as 'None'
                "hash": h32(2),
                "from_address": addr(1),
                "to_address": "None",
                "receipt_contract_address": addr(3),
                "input": "0x6080",
                "receipt_status": 0,
            },
            {"hash": h32(3), "input": "0x"},
        ],
    )
    out = run(aws_root, out_root, "transactions")
    s = out.schema
    assert "input" not in s.names and "block_hash" not in s.names
    assert s.field("hash").type == pa.binary(32)
    for c in ("from_address", "to_address", "receipt_contract_address"):
        assert s.field(c).type == pa.binary(20), c
    assert s.field("selector").type == pa.binary(4)
    rows = out.to_pylist()
    assert rows[0]["selector"] == bytes.fromhex("a9059cbb")
    assert rows[0]["input_size"] == 4 + 64
    assert rows[0]["to_address"] == bytes.fromhex(f"{2:040x}")
    assert rows[0]["receipt_contract_address"] is None
    assert rows[0]["gas"] == 60_000 and rows[0]["receipt_status"] == 1
    assert rows[1]["to_address"] is None
    assert rows[1]["receipt_contract_address"] == bytes.fromhex(f"{3:040x}")
    assert rows[1]["selector"] is None  # shorter than 4 bytes
    assert rows[2]["selector"] is None and rows[2]["input_size"] == 0


def test_transactions_value_is_never_stored_as_float(
    write_aws: WriteAws, aws_root: Path, out_root: Path
) -> None:
    # AWS itself stores value as a double, so precision past 2^53 is already gone at the
    # source. We store the double's exact integer as a decimal so nothing downstream
    # can lose more, and flag it as approximate in the column name.
    write_aws("transactions", [{"hash": h32(1), "value": 1.5e18}, {"hash": h32(2), "value": 7.0}])
    out = run(aws_root, out_root, "transactions")
    t = out.schema.field("value_wei_approx").type
    assert pa.types.is_decimal(t) and t.scale == 0 and t.precision == 38
    assert [int(v) for v in out.column("value_wei_approx").to_pylist()] == [
        1_500_000_000_000_000_000,
        7,
    ]


# ---------------------------------------------------------------- traces


def test_traces_filter(write_aws: WriteAws, aws_root: Path, out_root: Path) -> None:
    sel = "0x70a08231"
    write_aws(
        "traces",
        [
            # 0 top-level call with value: duplicates the transaction, dropped
            {"trace_type": "call", "call_type": "call", "trace_address": "None", "value": 1e18},
            # 1 internal call with value: kept
            {"trace_type": "call", "call_type": "call", "trace_address": "0,1", "value": 5e17},
            # 2 internal zero-value successful call: dropped
            {"trace_type": "call", "call_type": "staticcall", "trace_address": "0", "input": sel},
            # 3 failed internal call to a contract (has a selector): kept
            {
                "trace_type": "call",
                "call_type": "call",
                "trace_address": "2",
                "error": "Reverted",
                "status": 0,
                "input": sel + "00" * 32,
            },
            # 4 failed call with no calldata (plain ETH send): dropped
            {"trace_type": "call", "trace_address": "3", "error": "out of gas", "input": "0x"},
            # 5 create: kept, with init code
            {"trace_type": "create", "trace_address": "None", "input": "0x6080604052"},
            # 6 selfdestruct: kept
            {"trace_type": "suicide", "trace_address": "4"},
            # 7 failed top-level call to a contract: kept (carries the revert reason)
            {"trace_type": "call", "trace_address": "None", "error": "Reverted", "input": sel},
            # 8 child of a reverted call, no error of its own, zero value: dropped
            {"trace_type": "call", "trace_address": "2,0", "status": 0, "input": sel},
        ],
    )
    out = run(aws_root, out_root, "traces")
    kept = out.to_pylist()
    assert [r["trace_type"] for r in kept] == ["call", "call", "create", "suicide", "call"]
    assert [r["trace_address"] for r in kept] == ["0,1", "2", None, "4", None]
    assert kept[1]["error"] == "Reverted" and kept[1]["selector"] == bytes.fromhex("70a08231")
    assert kept[2]["init_code"] == bytes.fromhex("6080604052")
    assert kept[0]["init_code"] is None and kept[0]["error"] is None
    assert kept[3]["call_type"] is None  # 'None' string becomes a real null
    s = out.schema
    assert "input" not in s.names and "output" not in s.names
    assert s.field("from_address").type == pa.binary(20)
    assert s.field("gas").type == pa.int64() and s.field("gas_used").type == pa.int64()
    assert pa.types.is_decimal(s.field("value_wei_approx").type)


# ---------------------------------------------------------------- blocks, contracts


def test_blocks_kept_in_full(write_aws: WriteAws, aws_root: Path, out_root: Path) -> None:
    write_aws(
        "blocks",
        [
            {
                "number": n,
                "hash": h32(n),
                "parent_hash": h32(n - 1),
                "miner": addr(7),
                "nonce": "0x0000000000000000",
                "logs_bloom": "0x" + "00" * 256,
                "extra_data": "0xbeef",
                "transaction_count": 3,
            }
            for n in (10, 11)
        ],
    )
    out = run(aws_root, out_root, "blocks")
    assert out.num_rows == 2
    s = out.schema
    assert s.field("hash").type == pa.binary(32)
    assert s.field("miner").type == pa.binary(20)
    assert s.field("logs_bloom").type == pa.binary(256)
    assert s.field("extra_data").type == pa.binary()
    assert "date" not in s.names and "last_modified" not in s.names
    assert out.column("extra_data").to_pylist() == [b"\xbe\xef"] * 2


def test_contracts_kept_in_full(write_aws: WriteAws, aws_root: Path, out_root: Path) -> None:
    write_aws(
        "contracts",
        [{"address": addr(i), "bytecode": "0x6080", "block_hash": h32(i)} for i in range(3)],
    )
    out = run(aws_root, out_root, "contracts")
    assert out.num_rows == 3
    assert out.schema.field("address").type == pa.binary(20)
    assert out.column("bytecode").to_pylist() == [b"\x60\x80"] * 3


def test_multiple_source_files_are_concatenated(
    write_aws: WriteAws, aws_root: Path, out_root: Path
) -> None:
    write_aws("contracts", [{"address": addr(1)}], part=0)
    write_aws("contracts", [{"address": addr(2)}], part=1)
    out = run(aws_root, out_root, "contracts")
    assert out.num_rows == 2
