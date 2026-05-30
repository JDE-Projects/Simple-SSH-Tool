"""
Simple SSH Tool
A small, standalone desktop tool to connect to your machines over SSH and run
your own saved commands (or one-off custom commands) with live output.

Author : JDE-Projects
GitHub : https://github.com/JDE-Projects

Backend: pywebview window host + Paramiko SSH.
Frontend: simple_ssh_tool-UI.html (web-style interface).

Passwords are held in memory only. They are never written to disk.
Only device name / host / username and the per-device command library are
persisted in devices.json.
"""

import os
import re
import sys
import json
import time
import threading
import webbrowser

import paramiko
import webview


APP_NAME = "Simple SSH Tool"
AUTHOR_URL = "https://github.com/JDE-Projects"

MAX_CONNECTIONS = 5   # how many devices can be connected at once
MAX_PINNED = 10       # how many commands can be pinned as quick buttons

# Strip terminal escape sequences from command output. Covers colours and
# cursor moves (CSI, ESC[...]) plus the cursor save/restore codes (ESC 7 /
# ESC 8) that dpkg's "fancy" progress uses, and window-title (OSC) codes.
ANSI_RE = re.compile(
    r"\x1b\[[0-9;?]*[ -/]*[@-~]"            # CSI: colours, cursor moves
    r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"    # OSC: window titles, etc.
    r"|\x1b[ -/]*[0-~]"                      # 2/3-char escapes incl. ESC 7 / ESC 8
)

# Leftover dpkg progress lines once the escapes are stripped.
_PROGRESS_RE = re.compile(r"^Progress: \[\s*\d+%\]$")
_BAR_RE = re.compile(r"^\[[#.\s]*\]$")


def clean_output_line(s):
    """Remove escape sequences and collapse progress spam. Carriage-return
    redraws collapse to their final state; dpkg's fancy progress lines and
    bare progress bars are dropped, so apt's percent updates don't flood the
    console (e.g. 'Reading... 0%\\rReading... Done' shows just 'Done')."""
    s = ANSI_RE.sub("", s)
    if "\r" in s:
        parts = [p for p in s.split("\r") if p.strip()]
        s = parts[-1] if parts else ""
    stripped = s.strip()
    if _PROGRESS_RE.match(stripped) or _BAR_RE.match(stripped):
        return ""
    return s


# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------

def app_dir():
    """Folder for devices.json. Sits next to the .exe when frozen."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(name):
    """Locate bundled files (simple_ssh_tool-UI.html) whether running as script or exe."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)


DEVICES_FILE = os.path.join(app_dir(), "devices.json")


# ----------------------------------------------------------------------------
# Default devices (first run only). Passwords never stored.
# ----------------------------------------------------------------------------

DEFAULT_DEVICES = []  # ship build: no built-in devices, users add their own


def _normalize_command(c):
    if not isinstance(c, dict):
        return None
    cmd = (c.get("command") or "").strip()
    if not cmd:
        return None
    name = (c.get("name") or "").strip() or cmd[:24]
    return {
        "name": name,
        "command": cmd,
        "sudo": bool(c.get("sudo", False)),
        "confirm": (c.get("confirm") or "").strip(),
        "pinned": bool(c.get("pinned", False)),
    }


def _normalize_device(d):
    # Drop the old capability/type schema; carry over a clean command library.
    d.pop("type", None)
    d.pop("capabilities", None)
    cmds = d.get("commands")
    if not isinstance(cmds, list):
        cmds = []
    clean = [c for c in (_normalize_command(c) for c in cmds) if c]
    d["commands"] = clean
    return d


def load_devices():
    """Return the list of devices. Migrates the old array / capability schema."""
    if not os.path.exists(DEVICES_FILE):
        defaults = [_normalize_device(dict(d)) for d in DEFAULT_DEVICES]
        save_devices(defaults)
        return defaults
    try:
        with open(DEVICES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        old_format = isinstance(data, list)
        if old_format:                      # old bare-array format
            devices = data
        elif isinstance(data, dict):        # new portable object format
            devices = data.get("devices", [])
        else:
            devices = []
        devices = [_normalize_device(d) for d in devices if isinstance(d, dict)]
        if old_format:                      # rewrite once so the URL header lands
            save_devices(devices)
        return devices
    except Exception:
        return [_normalize_device(dict(d)) for d in DEFAULT_DEVICES]


def save_devices(devices):
    """Write the portable config. The author URL rides at the top of the file."""
    payload = {
        "_app": APP_NAME,
        "_author": AUTHOR_URL,
        "devices": devices,
    }
    try:
        with open(DEVICES_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True
    except Exception:
        return False


# ----------------------------------------------------------------------------
# A single live SSH session
# ----------------------------------------------------------------------------

class Session:
    def __init__(self, device, password):
        self.device = device
        self.password = password  # memory only
        self.client = None
        self.busy = False         # True while a command is actively running
        self.channel = None       # active exec channel (used to cancel)
        self.cancelled = False    # set True when the user cancels a command

    def connect(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.device["host"],
            username=self.device["username"],
            password=self.password,
            timeout=12,
            allow_agent=False,
            look_for_keys=False,
        )
        self.client = client
        # Silent keepalive so idle sessions are not dropped by the server.
        try:
            transport = client.get_transport()
            if transport:
                transport.set_keepalive(30)
        except Exception:
            pass

    def sudo_prefix(self):
        # -S reads sudo password from stdin; -p '' suppresses the prompt text.
        return "sudo -S -p ''"

    def close(self):
        try:
            if self.client:
                self.client.close()
        finally:
            self.client = None
            self.channel = None
            self.password = None  # wipe from memory


# ----------------------------------------------------------------------------
# API exposed to the JavaScript frontend
# ----------------------------------------------------------------------------

class Api:
    def __init__(self):
        self.sessions = {}  # device_id -> Session
        self.window = None
        self.frontend_ready = False  # set True by main() when page is loaded

    # ---- frontend helpers -------------------------------------------------

    def _emit(self, channel, payload):
        # Don't push JS until the page has signalled it's loaded; calling
        # evaluate_js too early can deadlock the bridge on Windows.
        if not self.window or not self.frontend_ready:
            return
        data = json.dumps(payload)
        js = f"window.__onPyEvent && window.__onPyEvent({json.dumps(channel)}, {data});"
        try:
            self.window.evaluate_js(js)
        except Exception:
            pass

    def _log(self, device_id, text, level="out"):
        self._emit("log", {"deviceId": device_id, "text": text, "level": level})

    # ---- misc -------------------------------------------------------------

    def get_config(self):
        return {
            "devices": load_devices(),
            "author": AUTHOR_URL,
            "maxConnections": MAX_CONNECTIONS,
            "maxPinned": MAX_PINNED,
        }

    def open_url(self, url):
        # Used by the GitHub link to open in the user's real browser.
        try:
            if isinstance(url, str) and url.startswith("http"):
                webbrowser.open(url)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ---- device CRUD ------------------------------------------------------

    def save_device(self, device):
        # The frontend owns the command list and sends the full device back.
        cmds = device.get("commands")
        if not isinstance(cmds, list):
            device["commands"] = []
        device = _normalize_device(device)
        devices = load_devices()
        if device.get("id"):
            for i, d in enumerate(devices):
                if d["id"] == device["id"]:
                    devices[i] = device
                    break
            else:
                devices.append(device)
        else:
            device["id"] = "dev" + str(int(time.time() * 1000))
            devices.append(device)
        save_devices(devices)
        return {"ok": True, "devices": devices}

    def delete_device(self, device_id):
        devices = [d for d in load_devices() if d["id"] != device_id]
        save_devices(devices)
        self.disconnect(device_id)
        return {"ok": True, "devices": devices}

    # ---- connection -------------------------------------------------------

    def connect(self, device_id, password):
        devices = load_devices()
        device = next((d for d in devices if d["id"] == device_id), None)
        if not device:
            return {"ok": False, "error": "Device not found."}
        if not password:
            return {"ok": False, "error": "Password is required."}

        # Connection cap (reconnecting to an already-connected device is fine).
        if device_id not in self.sessions and len(self.sessions) >= MAX_CONNECTIONS:
            return {"ok": False,
                    "error": f"Maximum of {MAX_CONNECTIONS} connections reached. "
                             f"Disconnect one first."}

        # Reconnecting to the same device: drop the old session cleanly.
        if device_id in self.sessions:
            self.disconnect(device_id)

        sess = Session(device, password)
        try:
            sess.connect()
        except paramiko.AuthenticationException:
            return {"ok": False, "error": "Authentication failed. Check username and password."}
        except Exception as e:
            return {"ok": False, "error": f"Could not connect: {e}"}

        self.sessions[device_id] = sess
        self._log(device_id, f"Connected to {device['host']} as {device['username']}.", "ok")
        return {"ok": True}

    def disconnect(self, device_id):
        sess = self.sessions.pop(device_id, None)
        if sess:
            sess.close()
            self._log(device_id, "Disconnected. Password cleared from memory.", "muted")
        self._emit("status", {"deviceId": device_id, "state": "idle"})
        return {"ok": True}

    def disconnect_all(self):
        for device_id in list(self.sessions.keys()):
            self.disconnect(device_id)
        return {"ok": True}

    def cancel(self, device_id):
        # Stop a running command by closing its channel. _exec sees the closed
        # channel, ends its read loop, and logs the command as cancelled.
        sess = self.sessions.get(device_id)
        if not sess or not sess.channel:
            return {"ok": False}
        sess.cancelled = True
        try:
            sess.channel.close()
        except Exception:
            pass
        return {"ok": True}

    def export_console(self, device_name, text):
        # Write the supplied console text to a .txt next to the executable.
        safe = (device_name or "Console").replace(" ", "_")
        safe = re.sub(r'[\\/:*?"<>|]', "", safe)  # strip Windows-illegal chars
        stamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        fname = f"{safe}_Console_Output_{stamp}.txt"
        path = os.path.join(app_dir(), fname)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text or "")
            return {"ok": True, "path": path, "name": fname}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ---- running commands -------------------------------------------------

    def run_command(self, device_id, raw_cmd, use_sudo, label=None):
        sess = self.sessions.get(device_id)
        if not sess:
            return {"ok": False, "error": "Not connected."}
        raw_cmd = (raw_cmd or "").strip()
        if not raw_cmd:
            return {"ok": False, "error": "Empty command."}
        label = label or "Custom command"
        # Honour the sudo toggle.
        if use_sudo:
            if raw_cmd.startswith("sudo "):
                # User invoked sudo themselves (keeps their own flags such as
                # -i / -u); just feed the password through our prefix.
                cmd = raw_cmd.replace("sudo ", f"{sess.sudo_prefix()} ", 1)
            else:
                # Run the whole line as root via a root shell, so &&, ;, and |
                # all stay elevated (not just the first command).
                inner = raw_cmd.replace("'", "'\\''")
                cmd = f"{sess.sudo_prefix()} bash -c '{inner}'"
            feed = True
        else:
            cmd = raw_cmd
            feed = False
        threading.Thread(
            target=self._exec, args=(device_id, cmd, label, feed),
            daemon=True,
        ).start()
        return {"ok": True}

    # ---- internal execution ----------------------------------------------

    def _exec(self, device_id, cmd, label, feed_sudo):
        sess = self.sessions.get(device_id)
        if not sess or not sess.client:
            self._log(device_id, "Not connected.", "err")
            return

        # Only feed the password if the command really invokes sudo. Commands
        # like `uptime` don't need stdin; using a PTY for them would echo any
        # stdin we wrote back through stdout (how a password could leak).
        needs_sudo = feed_sudo and ("sudo" in cmd)
        password = sess.password if needs_sudo else None

        self._emit("status", {"deviceId": device_id, "state": "running"})
        self._log(device_id, f"$ {label}", "cmd")
        sess.busy = True
        sess.cancelled = False
        try:
            # Only allocate a PTY when sudo is involved; otherwise plain pipes
            # (no echo, can't leak anything written to stdin).
            stdin, stdout, stderr = sess.client.exec_command(
                cmd, get_pty=needs_sudo
            )
            sess.channel = stdout.channel  # so cancel() can close it
            if needs_sudo and password:
                try:
                    stdin.write(password + "\n")
                    stdin.flush()
                except Exception:
                    pass

            def is_safe(line_text):
                # Defence in depth: filter any output matching the password, or
                # sudo prompt artifacts that slipped through.
                s = line_text.strip()
                if not s:
                    return True
                if password and s == password:
                    return False
                if s.startswith("[sudo] password for"):
                    return False
                return True

            for line in iter(stdout.readline, ""):
                if line == "":
                    break
                clean = clean_output_line(line.rstrip("\n"))
                if not clean.strip():
                    continue
                if not is_safe(clean):
                    continue
                self._log(device_id, clean, "out")

            err = stderr.read().decode("utf-8", "replace").strip()
            code = stdout.channel.recv_exit_status()

            if err:
                for ln in err.splitlines():
                    ln = clean_output_line(ln)
                    if not ln.strip() or not is_safe(ln):
                        continue
                    self._log(device_id, ln, "err")

            if sess.cancelled:
                self._log(device_id, f"\u25a0 {label} cancelled.", "warn")
            elif code == 0:
                self._log(device_id, f"\u2713 {label} finished.", "ok")
            else:
                self._log(device_id, f"\u2717 {label} exited with code {code}.", "err")
        except Exception as e:
            if sess and sess.cancelled:
                self._log(device_id, f"\u25a0 {label} cancelled.", "warn")
            else:
                self._log(device_id, f"Error: {e}", "err")
        finally:
            sess.busy = False
            sess.channel = None
            self._emit("status", {"deviceId": device_id, "state": "connected"})


# ----------------------------------------------------------------------------
# Boot
# ----------------------------------------------------------------------------

def main():
    # Make Windows show this app's own taskbar icon instead of the generic one.
    try:
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "JDEProjects.SimpleSSHTool"
            )
    except Exception:
        pass

    # pyi_splash exists only inside the onefile frozen build; ignore otherwise.
    try:
        import pyi_splash  # type: ignore
    except Exception:
        pyi_splash = None

    def close_splash():
        if pyi_splash:
            try:
                pyi_splash.close()
            except Exception:
                pass

    api = Api()
    html_path = resource_path("simple_ssh_tool-UI.html")
    window = webview.create_window(
        APP_NAME,
        url=html_path,
        js_api=api,
        width=1240,
        height=860,
        min_size=(980, 660),
        background_color="#0a0e14",
    )
    api.window = window

    def on_loaded():
        # Fires when the HTML page has loaded. From this point on it is safe to
        # push events to the page via evaluate_js.
        api.frontend_ready = True
        close_splash()

    try:
        window.events.loaded += on_loaded
    except Exception:
        # Older pywebview API: just mark ready immediately as a safe fallback.
        api.frontend_ready = True
        close_splash()

    # Safety net: close the splash even if the loaded event never fires.
    if pyi_splash:
        threading.Thread(
            target=lambda: (time.sleep(25), close_splash()),
            daemon=True,
        ).start()

    # Qt (PyQt6 + WebEngine) backend avoids the slow WinForms/WebView2 startup.
    # icon= sets the live window/taskbar icon on Qt. Guarded so an older
    # pywebview without the icon parameter still starts.
    try:
        webview.start(gui='qt', icon=resource_path('icon.png'))
    except TypeError:
        webview.start(gui='qt')


if __name__ == "__main__":
    main()
