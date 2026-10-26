""" Tests for SeenPackets dedup cache """
from mtg.connection.mqtt.transport import SeenPackets


def test_duplicate_detected():
    seen = SeenPackets(ttl=60)
    assert seen.check_and_add(0x91d4a7ac, 123) is False
    assert seen.check_and_add(0x91d4a7ac, 123) is True


def test_different_sender_or_id_not_duplicate():
    seen = SeenPackets(ttl=60)
    assert seen.check_and_add(1, 123) is False
    assert seen.check_and_add(2, 123) is False
    assert seen.check_and_add(1, 124) is False


def test_expired_entry_is_purged():
    seen = SeenPackets(ttl=-1)
    assert seen.check_and_add(1, 1) is False
    assert seen.check_and_add(1, 1) is False
