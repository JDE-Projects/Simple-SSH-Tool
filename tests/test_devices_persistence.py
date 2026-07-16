"""Tests for load_devices / save_devices: round-trip through devices.json.
See simple_ssh_tool.py ~line 173 / ~197.

Every test points sst.DEVICES_FILE at a pytest tmp_path so real user data
under the repo is never read or written.
"""

import json

import pytest

import simple_ssh_tool as sst


@pytest.fixture(autouse=True)
def isolated_devices_file(tmp_path, monkeypatch):
    """Redirect the module's DEVICES_FILE constant to a scratch path for
    every test in this file, then restore it afterwards."""
    path = tmp_path / "devices.json"
    monkeypatch.setattr(sst, "DEVICES_FILE", str(path))
    return path


def test_load_devices_creates_defaults_and_writes_portable_envelope(isolated_devices_file):
    devices = sst.load_devices()
    assert devices == []  # DEFAULT_DEVICES ships empty
    assert isolated_devices_file.exists()

    data = json.loads(isolated_devices_file.read_text(encoding="utf-8"))
    assert data["_app"] == sst.APP_NAME
    assert data["_author"] == sst.AUTHOR_URL
    assert data["devices"] == []


def test_save_then_load_round_trip(isolated_devices_file):
    sample = [{
        "id": "dev1", "host": "1.2.3.4", "username": "u",
        "commands": [{"command": "ls"}],
    }]
    assert sst.save_devices(sample) is True
    loaded = sst.load_devices()
    assert loaded == [{
        "id": "dev1", "host": "1.2.3.4", "username": "u",
        "commands": [{
            "name": "ls", "command": "ls",
            "sudo": False, "confirm": "", "pinned": False,
        }],
    }]


def test_load_devices_migrates_old_bare_array_format(isolated_devices_file):
    old_format = [{"id": "devX", "host": "h", "username": "u", "commands": []}]
    isolated_devices_file.write_text(json.dumps(old_format), encoding="utf-8")

    loaded = sst.load_devices()
    assert loaded == old_format

    # Migration rewrites the file once into the new portable object schema.
    rewritten = json.loads(isolated_devices_file.read_text(encoding="utf-8"))
    assert isinstance(rewritten, dict)
    assert rewritten["devices"] == old_format


def test_load_devices_new_format_missing_devices_key_yields_empty_list(isolated_devices_file):
    isolated_devices_file.write_text(json.dumps({"_app": "x"}), encoding="utf-8")
    assert sst.load_devices() == []


def test_load_devices_filters_non_dict_entries(isolated_devices_file):
    payload = {"devices": [
        {"id": "ok", "host": "h", "username": "u", "commands": []},
        "bad-entry",
        42,
        None,
    ]}
    isolated_devices_file.write_text(json.dumps(payload), encoding="utf-8")

    loaded = sst.load_devices()
    assert loaded == [{"id": "ok", "host": "h", "username": "u", "commands": []}]


def test_load_devices_corrupt_json_falls_back_to_defaults(isolated_devices_file):
    isolated_devices_file.write_text("not valid json{", encoding="utf-8")
    assert sst.load_devices() == []


def test_save_devices_returns_false_when_directory_does_not_exist(tmp_path, monkeypatch):
    bad_path = tmp_path / "no-such-dir" / "devices.json"
    monkeypatch.setattr(sst, "DEVICES_FILE", str(bad_path))
    assert sst.save_devices([{"id": "x"}]) is False
    assert not bad_path.exists()
