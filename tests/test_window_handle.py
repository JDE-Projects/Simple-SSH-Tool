"""Regression coverage for process-owned Win32 window discovery."""

import simple_ssh_tool as sst


class _Win32Function:
    def __init__(self, implementation):
        self.implementation = implementation
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.implementation(*args)


class _FakeUser32:
    def __init__(self, windows):
        self.windows = windows
        self.EnumWindows = _Win32Function(self._enum_windows)
        self.GetWindowThreadProcessId = _Win32Function(self._get_pid)
        self.GetWindowTextLengthW = _Win32Function(self._title_length)
        self.GetWindowTextW = _Win32Function(self._get_title)
        self.IsWindowVisible = _Win32Function(self._is_visible)

    def _enum_windows(self, callback, _lparam):
        for hwnd in self.windows:
            if not callback(hwnd, 0):
                break
        return True

    def _get_pid(self, hwnd, pid_pointer):
        pid_pointer._obj.value = self.windows[hwnd]["pid"]
        return 1

    def _title_length(self, hwnd):
        return len(self.windows[hwnd]["title"])

    def _get_title(self, hwnd, buffer, _length):
        buffer.value = self.windows[hwnd]["title"]
        return len(buffer.value)

    def _is_visible(self, hwnd):
        return self.windows[hwnd]["visible"]


def test_own_window_handle_filters_visibility_process_and_exact_title(monkeypatch):
    windows = {
        101: {"pid": 7000, "title": "Simple SSH Tool", "visible": False},
        202: {"pid": 8000, "title": "Simple SSH Tool", "visible": True},
        303: {"pid": 7000, "title": "Another Window", "visible": True},
        404: {"pid": 7000, "title": "Simple SSH Tool", "visible": True},
    }
    monkeypatch.setattr(sst.os, "getpid", lambda: 7000)
    monkeypatch.setattr(sst.ctypes.windll, "user32", _FakeUser32(windows))

    assert sst._own_window_handle("Simple SSH Tool") == 404


def test_own_window_handle_quietly_returns_none_on_win32_failure(monkeypatch):
    monkeypatch.setattr(sst.ctypes.windll, "user32", object())

    assert sst._own_window_handle("Simple SSH Tool") is None
