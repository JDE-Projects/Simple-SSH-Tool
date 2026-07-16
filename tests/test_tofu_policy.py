"""Tests for the trust-on-first-use host key logic: UnknownHostKey,
_TofuPolicy, and load_known_hosts. See simple_ssh_tool.py ~line 108-136.

The comparison that decides "known host, matching key -> proceed silently"
vs. "known host, changed key -> raise paramiko.BadHostKeyException" happens
inside paramiko's own SSHClient.connect() during a live SSH handshake; it is
not code in this repo and cannot be exercised without a real (or heavily
mocked-out) network connection, so that raise itself is not tested here.
What IS this repo's code, and is tested below, is everything that decision
depends on: _TofuPolicy (raises on first contact with a new host) and
load_known_hosts (reconstructs the pinned key state from disk that paramiko
later compares the live server key against).
"""

import os

import pytest
import paramiko

import simple_ssh_tool as sst


@pytest.fixture(autouse=True)
def isolated_known_hosts_file(tmp_path, monkeypatch):
    path = tmp_path / "known_hosts"
    monkeypatch.setattr(sst, "KNOWN_HOSTS_FILE", str(path))
    return path


# ---- UnknownHostKey ----------------------------------------------------

def test_unknown_host_key_stores_hostname_and_key():
    key = object()
    exc = sst.UnknownHostKey("example.com", key)
    assert exc.hostname == "example.com"
    assert exc.key is key
    assert str(exc) == "unknown host key"


# ---- _TofuPolicy ---------------------------------------------------------

def test_tofu_policy_raises_unknown_host_key_on_first_contact():
    # This is the "unknown host" branch: paramiko calls missing_host_key()
    # only when it has no pinned key at all for the host.
    policy = sst._TofuPolicy()
    assert isinstance(policy, paramiko.MissingHostKeyPolicy)

    key = object()  # policy never calls anything on it, just carries it
    with pytest.raises(sst.UnknownHostKey) as excinfo:
        policy.missing_host_key(client=None, hostname="example.com", key=key)
    assert excinfo.value.hostname == "example.com"
    assert excinfo.value.key is key


def test_tofu_policy_never_auto_trusts():
    # Regression guard: this policy must never write to known_hosts itself.
    # Confirm the file is untouched after a missing_host_key call.
    policy = sst._TofuPolicy()
    with pytest.raises(sst.UnknownHostKey):
        policy.missing_host_key(client=None, hostname="example.com", key=object())
    assert not os.path.exists(sst.KNOWN_HOSTS_FILE)


# ---- load_known_hosts ----------------------------------------------------

def test_load_known_hosts_missing_file_has_no_entries():
    hk = sst.load_known_hosts()
    assert hk.lookup("example.com") is None


def test_load_known_hosts_corrupt_file_is_ignored_not_raised(isolated_known_hosts_file):
    isolated_known_hosts_file.write_text("not a known_hosts file !!\n", encoding="utf-8")
    hk = sst.load_known_hosts()  # must not raise
    assert hk.lookup("example.com") is None


def test_load_known_hosts_matching_key_check_passes(isolated_known_hosts_file):
    # "Known host with matching key passes": the pinned key equals the key
    # presented, so HostKeys.check() (what paramiko consults) returns True.
    key = paramiko.ECDSAKey.generate()
    written = paramiko.HostKeys()
    written.add("example.com", key.get_name(), key)
    written.save(str(isolated_known_hosts_file))

    hk = sst.load_known_hosts()
    assert hk.lookup("example.com") is not None
    assert hk.check("example.com", key) is True


def test_load_known_hosts_changed_key_check_fails(isolated_known_hosts_file):
    # "Known host with CHANGED key is rejected": a different key for the
    # same host must not check out as matching (this is the data paramiko
    # uses to decide to raise BadHostKeyException instead of connecting).
    original_key = paramiko.ECDSAKey.generate()
    changed_key = paramiko.ECDSAKey.generate()
    written = paramiko.HostKeys()
    written.add("example.com", original_key.get_name(), original_key)
    written.save(str(isolated_known_hosts_file))

    hk = sst.load_known_hosts()
    assert hk.check("example.com", changed_key) is False
