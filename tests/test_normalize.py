"""Tests for _normalize_command and _normalize_device: shape normalization of
data coming out of devices.json. See simple_ssh_tool.py ~line 145 / ~161."""

import simple_ssh_tool as sst


# ---- _normalize_command ----------------------------------------------------

def test_normalize_command_full_fields():
    c = sst._normalize_command({
        "name": "List", "command": " ls -la ", "sudo": 1,
        "confirm": " sure? ", "pinned": 1, "extra": "dropped",
    })
    assert c == {
        "name": "List", "command": "ls -la", "sudo": True,
        "confirm": "sure?", "pinned": True,
    }
    assert "extra" not in c


def test_normalize_command_non_dict_or_empty_returns_none():
    assert sst._normalize_command("not a dict") is None
    assert sst._normalize_command(None) is None
    assert sst._normalize_command(["command", "ls"]) is None
    assert sst._normalize_command({}) is None
    assert sst._normalize_command({"command": "   "}) is None


def test_normalize_command_missing_or_blank_name_falls_back_to_command_prefix():
    long_cmd = "a-very-long-command-that-exceeds-24-chars-here"
    c = sst._normalize_command({"command": long_cmd})
    assert c["name"] == long_cmd[:24]

    c2 = sst._normalize_command({"name": "   ", "command": "uptime"})
    assert c2["name"] == "uptime"


def test_normalize_command_defaults_and_falsy_flags():
    c = sst._normalize_command({"command": "uptime"})
    assert c["sudo"] is False
    assert c["confirm"] == ""
    assert c["pinned"] is False

    c2 = sst._normalize_command({"command": "uptime", "sudo": 0, "pinned": False})
    assert c2["sudo"] is False
    assert c2["pinned"] is False


# ---- _normalize_device ------------------------------------------------------

def test_normalize_device_drops_old_schema_keys_and_returns_same_object():
    d = {"type": "linux", "capabilities": ["x"], "commands": []}
    result = sst._normalize_device(d)
    assert "type" not in d
    assert "capabilities" not in d
    assert result is d  # mutated in place, not replaced


def test_normalize_device_filters_invalid_commands():
    d = {"commands": [{"command": "ls"}, "bad", {"command": ""}, 42, None]}
    sst._normalize_device(d)
    assert d["commands"] == [
        {"name": "ls", "command": "ls", "sudo": False, "confirm": "", "pinned": False}
    ]


def test_normalize_device_missing_or_non_list_commands_becomes_empty_list():
    d1 = {"id": "dev1"}
    sst._normalize_device(d1)
    assert d1["commands"] == []

    d2 = {"commands": "not-a-list"}
    sst._normalize_device(d2)
    assert d2["commands"] == []
