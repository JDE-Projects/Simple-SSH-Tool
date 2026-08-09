"""Network-free coverage for update-check error classification."""

import errno
import json
import socket
import ssl
import urllib.error

import pytest

import simple_ssh_tool as sst


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (urllib.error.HTTPError("https://example.test", 403, "", None, None), "GitHub is rate-limiting update checks from this network. Try again later."),
        (urllib.error.HTTPError("https://example.test", 404, "", None, None), "No published release was found."),
        (urllib.error.HTTPError("https://example.test", 502, "", None, None), "GitHub is having trouble on its end (HTTP 502)."),
        (urllib.error.HTTPError("https://example.test", 418, "", None, None), "GitHub returned an error (HTTP 418)."),
        (json.JSONDecodeError("bad JSON", "x", 0), "GitHub returned something unexpected. This often means a proxy or a guest wifi sign-in page answered instead."),
        (urllib.error.URLError(ssl.SSLCertVerificationError("certificate verify failed")), "GitHub's certificate could not be verified. This usually means antivirus or a network filter is inspecting HTTPS traffic."),
        (urllib.error.URLError(ssl.SSLEOFError("eof")), "The secure connection was cut off during the handshake with GitHub."),
        (urllib.error.URLError(ssl.SSLZeroReturnError()), "The secure connection was cut off during the handshake with GitHub."),
        (urllib.error.URLError(ssl.SSLError("handshake failed")), "The secure connection to GitHub failed."),
        (urllib.error.URLError(socket.gaierror("lookup failed")), "The address for api.github.com could not be looked up. Check DNS or the internet connection."),
        (urllib.error.URLError(socket.timeout("timed out")), "GitHub didn't respond in time."),
        (urllib.error.URLError(ConnectionRefusedError("refused")), "The connection was refused or reset. A firewall or proxy may be blocking it."),
        (urllib.error.URLError(ConnectionResetError("reset")), "The connection was refused or reset. A firewall or proxy may be blocking it."),
        (urllib.error.URLError(OSError(errno.ENETUNREACH, "unreachable")), "No network connection."),
        (urllib.error.URLError("unclassified"), "Couldn't reach GitHub. Check the internet connection."),
        (ValueError("x" * 200), "ValueError: " + "x" * 105 + "..."),
    ],
)
def test_update_error_reason_classifies_each_branch(exc, expected):
    assert sst._update_error_reason(exc) == expected
