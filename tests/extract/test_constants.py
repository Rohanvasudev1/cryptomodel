from Crypto.Hash import keccak

from cryptomodel.extract.constants import EVENT_TOPICS, LOG_TOPIC0S


def keccak_hex(text: str) -> str:
    h = keccak.new(digest_bits=256)
    h.update(text.encode())
    return "0x" + h.hexdigest()


def test_every_topic0_is_keccak_of_its_signature() -> None:
    for name, event in EVENT_TOPICS.items():
        assert event.topic0 == keccak_hex(event.signature), name


def test_required_events_are_present() -> None:
    names = set(EVENT_TOPICS)
    assert {"ERC20_TRANSFER", "ERC20_APPROVAL"} <= names
    assert {"V2_PAIR_CREATED", "V2_SWAP", "V2_MINT", "V2_BURN", "V2_SYNC"} <= names
    assert {
        "V3_POOL_CREATED",
        "V3_INITIALIZE",
        "V3_SWAP",
        "V3_MINT",
        "V3_BURN",
        "V3_COLLECT",
    } <= names
    assert {"V4_INITIALIZE", "V4_MODIFY_LIQUIDITY", "V4_SWAP"} <= names


def test_log_topic0s_are_unique_lowercase_hex() -> None:
    assert len(LOG_TOPIC0S) == len(EVENT_TOPICS)
    for t in LOG_TOPIC0S:
        assert t.startswith("0x") and len(t) == 66 and t == t.lower()
