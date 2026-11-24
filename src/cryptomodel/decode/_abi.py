"""Hand-written ABI word decoding for event logs.

Every value is an exact Python int. Each helper checks that the word is a valid
encoding of its Solidity type (zero-padded for unsigned types and addresses,
sign-extended for signed types) and raises `DecodeError` otherwise, so a log
from an unrelated contract that reuses a topic0 is rejected rather than
misread.
"""

from collections.abc import Sequence

WORD_HEX_CHARS = 64
_HEX_DIGITS = frozenset("0123456789abcdef")


class DecodeError(ValueError):
    """A log matched a known topic0 but its topics or data do not fit the event layout."""


def normalize_hex(value: str | None, what: str) -> str:
    """Return `value` lowercased without its `0x` prefix, checking it is hex."""
    if value is None:
        raise DecodeError(f"{what} is missing")
    text = value.lower()
    if text.startswith("0x"):
        text = text[2:]
    if not _HEX_DIGITS.issuperset(text):
        raise DecodeError(f"{what} is not hex: {value[:80]!r}")
    return text


def topic_words(topics: Sequence[str | None], expected: int, event: str) -> list[int]:
    """Parse all topics (including topic0) as 32-byte words, checking the count."""
    if len(topics) != expected:
        raise DecodeError(f"{event}: expected {expected} topics, got {len(topics)}")
    words = []
    for i, topic in enumerate(topics):
        text = normalize_hex(topic, f"{event} topic{i}")
        if len(text) != WORD_HEX_CHARS:
            raise DecodeError(f"{event}: topic{i} has {len(text)} hex chars, expected {WORD_HEX_CHARS}")
        words.append(int(text, 16))
    return words


def data_words(data: str | None, expected: int, event: str) -> list[int]:
    """Split `data` into exactly `expected` 32-byte words."""
    text = normalize_hex(data if data is not None else "0x", f"{event} data")
    if len(text) != expected * WORD_HEX_CHARS:
        raise DecodeError(
            f"{event}: data has {len(text)} hex chars, expected {expected} words ({expected * WORD_HEX_CHARS} chars)"
        )
    return [int(text[i : i + WORD_HEX_CHARS], 16) for i in range(0, len(text), WORD_HEX_CHARS)]


def as_uint(word: int, bits: int, field: str) -> int:
    if word >> bits:
        raise DecodeError(f"{field}: value does not fit uint{bits}")
    return word


def as_int(word: int, bits: int, field: str) -> int:
    """Decode a two's-complement signed int that must be sign-extended to 256 bits."""
    value = word - (1 << 256) if word >> 255 else word
    bound = 1 << (bits - 1)
    if not -bound <= value < bound:
        raise DecodeError(f"{field}: value does not fit int{bits}")
    return value


def as_address(word: int, field: str) -> str:
    if word >> 160:
        raise DecodeError(f"{field}: address word has non-zero high bytes")
    return f"0x{word:040x}"


def as_bytes32(word: int) -> str:
    return f"0x{word:064x}"
