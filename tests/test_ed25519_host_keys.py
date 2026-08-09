"""Paramiko's Ed25519 path remains compatible with cryptography 50."""

import io

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import paramiko

import simple_ssh_tool as sst


def test_ed25519_key_round_trips_through_paramiko_host_keys(tmp_path, monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.OpenSSH,
        serialization.NoEncryption(),
    ).decode("ascii")
    key = paramiko.Ed25519Key.from_private_key(io.StringIO(pem))
    fingerprint = sst.fingerprint_sha256(key)

    known_hosts = tmp_path / "known_hosts"
    monkeypatch.setattr(sst, "KNOWN_HOSTS_FILE", str(known_hosts))
    host = "ssh-screenshot-lab.example"
    keys = paramiko.HostKeys()
    keys.add(host, key.get_name(), key)
    keys.save(str(known_hosts))

    reloaded = sst.load_known_hosts().lookup(host)
    assert reloaded is not None
    reloaded_key = reloaded[key.get_name()]
    assert reloaded_key.get_name() == "ssh-ed25519"
    assert sst.fingerprint_sha256(reloaded_key) == fingerprint
