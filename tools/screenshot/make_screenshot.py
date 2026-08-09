#!/usr/bin/env python3
"""Regenerate screenshots/ssh-light-dark.png from invented SSH session data.

The working UI and local preferences are never modified. The tool stages the
HTML, glyph, and fonts into the OS temporary directory, serves that copy, and
uses the app's own render functions with the fixture in scene.py.
"""

import http.server
import json
import os
import re
import shutil
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
OUT_IMAGE = os.path.join(REPO_ROOT, "screenshots", "ssh-light-dark.png")
LAYOUT_WIDTH = 1800
LAYOUT_HEIGHT = 1120
CAPTURE_SCALE = 0.5


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def read_app_version():
    path = os.path.join(REPO_ROOT, "simple_ssh_tool.py")
    with open(path, encoding="utf-8") as source:
        match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', source.read())
    if not match:
        fail(f"could not find APP_VERSION in {path}")
    return match.group(1)


def stage_ui(temp_dir):
    shutil.copy2(os.path.join(REPO_ROOT, "simple_ssh_tool-UI.html"),
                 os.path.join(temp_dir, "index.html"))
    shutil.copy2(os.path.join(REPO_ROOT, "simple_ssh_tool.png"), temp_dir)
    shutil.copytree(os.path.join(REPO_ROOT, "fonts"), os.path.join(temp_dir, "fonts"))


def build_setup_script(version):
    """Seed the UI's actual state variables and call its render seams."""
    return (
        f"DEVICES = {json.dumps(scene.DEVICES)};"
        f"Object.assign(connected, {json.dumps({d['id']: True for d in scene.DEVICES})});"
        "currentDeviceId = 'edge-gateway';"
        f"document.getElementById('verLabel').textContent = 'v' + {json.dumps(version)};"
        "if (typeof render === 'function') render();"
        "if (typeof ensureTab === 'function') ensureTab('edge-gateway');"
        "if (typeof setActiveTab === 'function') setActiveTab('edge-gateway');"
        + "".join(
            f"if (typeof addLine === 'function') addLine({json.dumps(device_id)}, {json.dumps(text)}, {json.dumps(level)});"
            for device_id, text, level in scene.CONSOLE_LINES
        )
        + "if (typeof renderLibrary === 'function') renderLibrary();"
    )


def write_capture_config(temp_dir, port, version):
    config = {
        "url": f"http://127.0.0.1:{port}/index.html",
        "width": LAYOUT_WIDTH,
        "height": LAYOUT_HEIGHT,
        "scale": CAPTURE_SCALE,
        "outDir": "shots",
        "waitFor": "typeof render === 'function' && typeof applyTheme === 'function'",
        "setup": build_setup_script(version),
        "waitForData": "document.querySelectorAll('[data-card]').length === 3 && document.querySelectorAll('.ln').length === 3",
        "settleMs": 500,
        "shots": [
            {"name": "light", "script": "applyTheme('light')"},
            {"name": "dark", "script": "applyTheme('dark')"},
        ],
    }
    path = os.path.join(temp_dir, "shots.json")
    with open(path, "w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=2)
    return path


def run(command, label):
    result = subprocess.run(command, cwd=REPO_ROOT)
    if result.returncode:
        fail(f"{label} failed with exit code {result.returncode}")


def main(argv):
    keep = "--keep" in argv
    build_tools = os.path.join(os.path.dirname(REPO_ROOT), "build-tools")
    if "--build-tools" in argv:
        index = argv.index("--build-tools") + 1
        if index >= len(argv):
            fail("--build-tools needs a path after it")
        build_tools = argv[index]
    capture_script = os.path.join(build_tools, "screenshot", "capture.mjs")
    compose_script = os.path.join(build_tools, "screenshot", "compose.py")
    for path in (capture_script, compose_script):
        if not os.path.exists(path):
            fail(f"missing {path}. Pass --build-tools with the repo path.")

    temp_dir = tempfile.mkdtemp(prefix="ssh-screenshot-")
    httpd = None
    try:
        stage_ui(temp_dir)
        port = free_port()

        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=temp_dir, **kwargs)

        httpd = socketserver.TCPServer(("127.0.0.1", port), Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        config_path = write_capture_config(temp_dir, port, read_app_version())
        run(["node", capture_script, config_path], "capture")
        shots = os.path.join(temp_dir, "shots")
        run([sys.executable, compose_script, OUT_IMAGE,
             os.path.join(shots, "light.png"), os.path.join(shots, "dark.png")], "compose")
    finally:
        if httpd is not None:
            httpd.shutdown()
        if keep:
            print(f"temp folder kept at {temp_dir}")
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if os.path.exists(temp_dir):
                print(f"WARNING: could not remove {temp_dir}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
