"""Tests for clean_output_line: ANSI stripping, CR-collapse, dpkg progress
spam removal. See simple_ssh_tool.py ~line 64."""

import simple_ssh_tool as sst


def test_plain_and_whitespace_text_passes_through_unchanged():
    assert sst.clean_output_line("hello world") == "hello world"
    assert sst.clean_output_line("") == ""
    # No CR, no escapes, no progress pattern match: passed through as-is
    # (callers decide whether to skip blank lines).
    assert sst.clean_output_line("   ") == "   "


def test_strips_ansi_color_and_sgr_codes():
    assert sst.clean_output_line("\x1b[31mred\x1b[0m") == "red"
    # Bold + colour combined into one CSI sequence (e.g. "\x1b[1;31m").
    assert sst.clean_output_line("\x1b[1;31mbold red\x1b[0m") == "bold red"


def test_strips_osc_title_and_cursor_save_restore_escapes():
    # OSC sequences (window title) are terminated by BEL (\x07) or ESC \.
    assert sst.clean_output_line("\x1b]0;mytitle\x07text") == "text"
    # dpkg's "fancy" progress uses ESC 7 (save cursor) / ESC 8 (restore).
    assert sst.clean_output_line("\x1b7Hello\x1b8") == "Hello"


def test_cr_collapse_keeps_final_redraw():
    # A carriage-return redraw collapses to its final state, per the
    # function's own docstring example.
    assert sst.clean_output_line("Reading... 0%\rReading... Done") == "Reading... Done"
    assert sst.clean_output_line("0%\r33%\r66%\r100%") == "100%"
    assert sst.clean_output_line("\r\r") == ""


def test_dpkg_progress_line_is_dropped():
    assert sst.clean_output_line("Progress: [ 50%]") == ""
    assert sst.clean_output_line("Progress: [100%]") == ""


def test_bare_progress_bar_is_dropped():
    assert sst.clean_output_line("[####......]") == ""
    assert sst.clean_output_line("[..........]") == ""


def test_progress_line_with_trailing_text_is_not_dropped():
    # Only an exact "Progress: [ NN%]" line is spam; anything extra on the
    # line means it is not the redraw filler and should survive.
    assert sst.clean_output_line("Progress: [ 50%] extra") == "Progress: [ 50%] extra"


def test_bracket_line_with_non_bar_chars_is_not_dropped():
    # _BAR_RE only matches '#', '.' and whitespace inside the brackets.
    assert sst.clean_output_line("[abc]") == "[abc]"


def test_combines_ansi_strip_and_cr_collapse():
    line = "\x1b[2K\rDownloading... 50%\r\x1b[2KDownloading... Done"
    assert sst.clean_output_line(line) == "Downloading... Done"
