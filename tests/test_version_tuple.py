"""Tests for _version_tuple: turns a version string into a comparable tuple
of ints so update checks compare numerically, not as strings.
See simple_ssh_tool.py ~line 216."""

import simple_ssh_tool as sst


def test_numeric_ordering_beats_lexical_ordering():
    # As strings "1.10.0" < "1.9.9"; numerically it must be greater.
    assert sst._version_tuple("1.10.0") > sst._version_tuple("1.9.9")
    assert sst._version_tuple("1.2.3") == sst._version_tuple("1.2.3")


def test_strips_leading_v_prefix_single_and_repeated():
    assert sst._version_tuple("v2.0.0") == (2, 0, 0)
    # lstrip("vV") removes every leading v/V character, not just one.
    assert sst._version_tuple("VV3.0.0") == (3, 0, 0)


def test_none_and_empty_input_yield_zero_tuple():
    assert sst._version_tuple(None) == (0,)
    assert sst._version_tuple("") == (0,)


def test_non_numeric_garbage_yields_zero_tuple():
    assert sst._version_tuple("garbage") == (0,)


def test_non_digit_suffix_in_segment_is_stripped_not_rejected():
    # Only digit characters within each dot-separated part are kept.
    assert sst._version_tuple("1.2.3-beta") == (1, 2, 3)


def test_empty_segment_between_dots_becomes_zero():
    assert sst._version_tuple("1..2") == (1, 0, 2)


def test_single_number_version():
    assert sst._version_tuple("5") == (5,)
