"""Tests for fingerprint_sha256: OpenSSH-style SHA256 host key fingerprint.
See simple_ssh_tool.py ~line 108."""

import paramiko

import simple_ssh_tool as sst


class _FakeKey:
    """Stand-in for a paramiko key: fingerprint_sha256 only ever calls
    .asbytes() on its argument."""

    def __init__(self, raw_bytes):
        self._raw = raw_bytes

    def asbytes(self):
        return self._raw


def test_known_bytes_produce_expected_fingerprint():
    # Expected value computed independently (hashlib.sha256 + base64, not by
    # calling the function under test) for the fixed input b"test-key-bytes".
    key = _FakeKey(b"test-key-bytes")
    assert sst.fingerprint_sha256(key) == "SHA256:JCO8HeDXSpkpred7BvVpKY9QysvdDzEIoItuXQN4nT0"


def test_fingerprint_format_has_prefix_and_no_padding():
    key = _FakeKey(b"some-other-key-material")
    fp = sst.fingerprint_sha256(key)
    assert fp.startswith("SHA256:")
    assert "=" not in fp


def test_different_key_bytes_give_different_fingerprints():
    a = sst.fingerprint_sha256(_FakeKey(b"key-a"))
    b = sst.fingerprint_sha256(_FakeKey(b"key-b"))
    assert a != b


def test_works_with_a_real_paramiko_key_object():
    # End-to-end with an actual generated key (not just the fake stand-in) to
    # confirm asbytes() really is all this function needs from a real key.
    key = paramiko.ECDSAKey.generate()
    fp = sst.fingerprint_sha256(key)
    assert fp.startswith("SHA256:")
    # Same key object -> same fingerprint every time (deterministic).
    assert fp == sst.fingerprint_sha256(key)
