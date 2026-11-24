"""Decode Uniswap V2/V3/V4 (and fork) DEX events and ERC-20 events from raw logs.

- `events.decode_log`: one log -> typed dataclass with exact int amounts.
- `batch.decode_logs`: a logs table -> typed tables, `dex_action` and `errors`.
- `constants`: topic0 hashes. `registry`: known factories and their dex labels.
"""

from cryptomodel.decode.batch import DecodedLogs, attach_pool_info, build_pool_registry, decode_logs
from cryptomodel.decode.events import DecodeError, decode_log

__all__ = ["DecodeError", "DecodedLogs", "attach_pool_info", "build_pool_registry", "decode_log", "decode_logs"]
