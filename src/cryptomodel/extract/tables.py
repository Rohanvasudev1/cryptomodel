"""What each table keeps: the source columns read, the DuckDB projection and filter, and
the output schema.

Conventions:

- Addresses are ``binary(20)``, hashes and topics ``binary(32)``, other hex blobs ``binary``.
- AWS writes missing strings as the literal ``'None'`` (traces, ``transactions.to_address``)
  or as ``''`` (``transactions.receipt_contract_address``). Every string goes through
  ``nn()`` or ``hexbin()``, which turn both into a real null.
- AWS stores ``transactions.value`` and ``traces.value`` as doubles, so precision beyond
  2^53 wei is lost at the source. We keep the double's integer exactly as
  ``decimal(38, 0)`` in ``value_wei_approx``. Token amounts come from ``logs.data``,
  which is exact.
- Timestamps are ``timestamp[us, UTC]``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import pyarrow as pa

from cryptomodel.extract.constants import LOG_TOPIC0S

# Bump when the meaning of an output changes without the SQL or schema text changing.
SPEC_VERSION = 1

ADDR = pa.binary(20)
HASH = pa.binary(32)
BLOB = pa.binary()
TS = pa.timestamp("us", tz="UTC")
WEI = pa.decimal128(38, 0)

# Macros installed on every DuckDB connection before a spec's SQL runs.
MACROS = """
CREATE OR REPLACE MACRO nn(x) AS CASE WHEN x IN ('None', '') THEN NULL ELSE x END;
CREATE OR REPLACE MACRO hexbin(x) AS unhex(substr(nn(x), 3));
CREATE OR REPLACE MACRO selector(x) AS
    CASE WHEN length(nn(x)) >= 10 THEN unhex(substr(x, 3, 8)) END;
CREATE OR REPLACE MACRO hexsize(x) AS coalesce((length(nn(x)) - 2) // 2, 0);
CREATE OR REPLACE MACRO utc(x) AS timezone('UTC', x::TIMESTAMP);
"""


@dataclass(frozen=True)
class TableSpec:
    name: str
    source_columns: tuple[str, ...]
    sql: str  # reads from the view ``src``; output columns in ``schema`` order
    schema: pa.Schema


def _spec(name: str, source_columns: list[str], sql: str, fields: list[pa.Field]) -> TableSpec:
    return TableSpec(name, tuple(source_columns), sql.strip(), pa.schema(fields))


_TOPIC_LIST = ", ".join(f"'{t}'" for t in LOG_TOPIC0S)

BLOCKS = _spec(
    "blocks",
    [
        "number",
        "hash",
        "parent_hash",
        "timestamp",
        "miner",
        "nonce",
        "difficulty",
        "size",
        "base_fee_per_gas",
        "gas_limit",
        "gas_used",
        "extra_data",
        "logs_bloom",
        "state_root",
        "receipts_root",
        "transactions_root",
        "sha3_uncles",
        "transaction_count",
    ],
    """
    SELECT number, hexbin(hash), hexbin(parent_hash), utc(timestamp), hexbin(miner),
           hexbin(nonce), difficulty, size, base_fee_per_gas, gas_limit, gas_used,
           hexbin(extra_data), hexbin(logs_bloom), hexbin(state_root), hexbin(receipts_root),
           hexbin(transactions_root), hexbin(sha3_uncles), transaction_count
    FROM src
    """,
    [
        pa.field("number", pa.int64()),
        pa.field("hash", HASH),
        pa.field("parent_hash", HASH),
        pa.field("timestamp", TS),
        pa.field("miner", ADDR),
        pa.field("nonce", pa.binary(8)),
        pa.field("difficulty", pa.float64()),
        pa.field("size", pa.int64()),
        pa.field("base_fee_per_gas", pa.int64()),
        pa.field("gas_limit", pa.int64()),
        pa.field("gas_used", pa.int64()),
        pa.field("extra_data", BLOB),
        pa.field("logs_bloom", pa.binary(256)),
        pa.field("state_root", HASH),
        pa.field("receipts_root", HASH),
        pa.field("transactions_root", HASH),
        pa.field("sha3_uncles", HASH),
        pa.field("transaction_count", pa.int64()),
    ],
)

TRANSACTIONS = _spec(
    "transactions",
    [
        "hash",
        "block_number",
        "block_timestamp",
        "transaction_index",
        "from_address",
        "to_address",
        "value",
        "nonce",
        "gas",
        "gas_price",
        "max_fee_per_gas",
        "max_priority_fee_per_gas",
        "receipt_gas_used",
        "receipt_effective_gas_price",
        "receipt_status",
        "receipt_contract_address",
        "transaction_type",
        "input",
    ],
    """
    SELECT hexbin(hash), block_number, utc(block_timestamp), transaction_index,
           hexbin(from_address), hexbin(to_address), CAST(value AS DECIMAL(38, 0)),
           nonce, gas, gas_price, max_fee_per_gas, max_priority_fee_per_gas,
           receipt_gas_used, receipt_effective_gas_price, receipt_status,
           hexbin(receipt_contract_address), transaction_type,
           selector(input), hexsize(input)
    FROM src
    """,
    [
        pa.field("hash", HASH),
        pa.field("block_number", pa.int64()),
        pa.field("block_timestamp", TS),
        pa.field("transaction_index", pa.int64()),
        pa.field("from_address", ADDR),
        pa.field("to_address", ADDR),
        pa.field("value_wei_approx", WEI),
        pa.field("nonce", pa.int64()),
        pa.field("gas", pa.int64()),
        pa.field("gas_price", pa.int64()),
        pa.field("max_fee_per_gas", pa.int64()),
        pa.field("max_priority_fee_per_gas", pa.int64()),
        pa.field("receipt_gas_used", pa.int64()),
        pa.field("receipt_effective_gas_price", pa.int64()),
        pa.field("receipt_status", pa.int64()),
        pa.field("receipt_contract_address", ADDR),
        pa.field("transaction_type", pa.int64()),
        pa.field("selector", pa.binary(4)),
        pa.field("input_size", pa.int64()),
    ],
)

LOGS = _spec(
    "logs",
    [
        "block_number",
        "block_timestamp",
        "transaction_index",
        "log_index",
        "transaction_hash",
        "address",
        "topics",
        "data",
    ],
    f"""
    SELECT block_number, utc(block_timestamp), transaction_index, log_index,
           hexbin(transaction_hash), hexbin(address),
           hexbin(topics[1]), hexbin(topics[2]), hexbin(topics[3]), hexbin(topics[4]),
           hexbin(data)
    FROM src
    WHERE lower(topics[1]) IN ({_TOPIC_LIST})
    """,
    [
        pa.field("block_number", pa.int64()),
        pa.field("block_timestamp", TS),
        pa.field("transaction_index", pa.int64()),
        pa.field("log_index", pa.int64()),
        pa.field("transaction_hash", HASH),
        pa.field("address", ADDR),
        pa.field("topic0", HASH),
        pa.field("topic1", HASH),
        pa.field("topic2", HASH),
        pa.field("topic3", HASH),
        pa.field("data", BLOB),
    ],
)

# Kept traces:
# - every create (with its init code: creation bytecode plus constructor arguments) and
#   every selfdestruct ('suicide');
# - internal calls (non-null trace_address) that move ETH; top-level calls with value
#   duplicate the transaction row;
# - calls that errored and carry calldata (a 4-byte selector), i.e. failed calls to
#   contracts, including the top-level frame. Their reverted children, which have no
#   error of their own, are dropped.
# Whether the callee is a token or pool contract is not known at this stage, so the
# failed-call filter cannot be narrowed to those; that happens after the event table.
TRACES = _spec(
    "traces",
    [
        "block_number",
        "block_timestamp",
        "transaction_index",
        "transaction_hash",
        "trace_address",
        "trace_type",
        "call_type",
        "from_address",
        "to_address",
        "value",
        "gas",
        "gas_used",
        "status",
        "error",
        "input",
    ],
    """
    SELECT block_number, utc(block_timestamp), transaction_index, hexbin(transaction_hash),
           nn(trace_address), trace_type, nn(call_type), hexbin(from_address),
           hexbin(to_address), CAST(value AS DECIMAL(38, 0)), CAST(gas AS BIGINT),
           CAST(gas_used AS BIGINT), status, nn(error), selector(input), hexsize(input),
           CASE WHEN trace_type = 'create' THEN hexbin(input) END
    FROM src
    WHERE trace_type IN ('create', 'suicide')
       OR (trace_type = 'call' AND nn(trace_address) IS NOT NULL AND value > 0)
       OR (trace_type = 'call' AND nn(error) IS NOT NULL AND length(nn(input)) >= 10)
    """,
    [
        pa.field("block_number", pa.int64()),
        pa.field("block_timestamp", TS),
        pa.field("transaction_index", pa.int64()),
        pa.field("transaction_hash", HASH),
        pa.field("trace_address", pa.string()),
        pa.field("trace_type", pa.string()),
        pa.field("call_type", pa.string()),
        pa.field("from_address", ADDR),
        pa.field("to_address", ADDR),
        pa.field("value_wei_approx", WEI),
        pa.field("gas", pa.int64()),
        pa.field("gas_used", pa.int64()),
        pa.field("status", pa.int64()),
        pa.field("error", pa.string()),
        pa.field("selector", pa.binary(4)),
        pa.field("input_size", pa.int64()),
        pa.field("init_code", BLOB),
    ],
)

CONTRACTS = _spec(
    "contracts",
    ["address", "bytecode", "block_number", "block_hash", "block_timestamp"],
    """
    SELECT hexbin(address), hexbin(bytecode), block_number, hexbin(block_hash),
           utc(block_timestamp)
    FROM src
    """,
    [
        pa.field("address", ADDR),
        pa.field("bytecode", BLOB),
        pa.field("block_number", pa.int64()),
        pa.field("block_hash", HASH),
        pa.field("block_timestamp", TS),
    ],
)

TABLE_SPECS: dict[str, TableSpec] = {
    s.name: s for s in (BLOCKS, TRANSACTIONS, LOGS, TRACES, CONTRACTS)
}


def spec_hash(table: str) -> str:
    """Fingerprint of a table's filter and schema; a change forces re-extraction."""
    spec = TABLE_SPECS[table]
    text = "\n".join(
        [str(SPEC_VERSION), MACROS, ",".join(spec.source_columns), spec.sql, str(spec.schema)]
    )
    return hashlib.sha256(text.encode()).hexdigest()[:16]
