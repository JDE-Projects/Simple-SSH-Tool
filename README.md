# Simple SSH Tool

A small, standalone Windows desktop tool to connect to your machines over SSH and run your own saved commands or one-off custom commands, with live output. Add a device, type the password when you connect, and use one-tap command buttons or a free command box. The interface is a clean web-style window.

Built by [JDE-Projects](https://github.com/JDE-Projects).

## Highlights

- **Per-device command library.** Build named commands for each device, mark some with sudo or a confirm prompt, pin up to 10 as quick buttons, and copy a command to another saved device.
- **Secrets are never saved.** The SSH password is held in memory only and wiped on disconnect. Only the name, host, username, and saved commands are written to `devices.json`.
- **Multiple connections at once.** Up to five devices connect independently, each with its own console tab.
- **Tabbed console with export.** Timestamped, per-device output. Export the active tab to a text file next to the app, and clear it for a fresh view.
- **Optional debug log.** A toggle in the bottom left writes a timestamped log next to the app for the session. Off by default, and passwords are never written to it.
- **Update check.** The version button checks GitHub Releases and points you to a newer build when one exists.

## How it works

- Backend: [Paramiko](https://www.paramiko.org/) for SSH, running each command on its own channel and streaming output line by line.
- Window: pywebview on the Qt backend (PySide6), with the UI in `simple_ssh_tool-UI.html`. Fonts are bundled in `fonts/`, so the look holds with no internet.
- `devices.json` is portable: it carries a small header with the project URL, so you can back it up or move it to another machine. Older config files migrate automatically on first load.

## Download and run

Grab the latest `Simple SSH Tool` zip from the [Releases](../../releases) page, unzip it, and run `Simple SSH Tool.exe` inside the folder. No Python or setup required. Windows only. Keep the folder together; the exe needs the files beside it.

Because it is unsigned, Windows SmartScreen may warn about an unknown publisher the first time. Click **More info > Run anyway**.

## Build from source (optional)

If you would rather run or build it yourself, you need:

- **Python 3** on the machine's PATH.
- Python packages: `pywebview`, `PySide6`, `paramiko`. Keep `PyQt6` uninstalled so PySide6 is the binding that gets bundled.

```
pip install pywebview PySide6 paramiko
```

Keep these together so the app finds them next to itself: `simple_ssh_tool.py`, `simple_ssh_tool-UI.html`, the `fonts/` folder, `simple_ssh_tool.ico`, `simple_ssh_tool.png`, and `simple_ssh_tool-splash.png`. Then either:

- **Run from source:** `python simple_ssh_tool.py`
- **Build the .exe:** double-click `Build_Simple_SSH_Tool.bat`, which uses PyInstaller to produce `dist\Simple SSH Tool\Simple SSH Tool.exe` (a folder). Distribute the whole `dist\Simple SSH Tool` folder, zipped. The splash shows while the app starts.

## Using it

1. Click **Add Device**, give it a display name, then enter the host or IP and the username.
2. On the device card, type the password and click **Connect**. A console tab opens for it.
3. Manage that device's commands in the **Command Library** pane along the bottom: add, edit, delete, pin, and copy to another device. Pinned commands appear as quick buttons on the card.
4. Run a saved command, a pin, or type one in the custom box (toggle **sudo** if it needs root). Commands with a confirm message ask before firing.
5. **Export** saves the active tab's console to a text file next to the app. **Disconnect** asks first, then clears the password from memory; closing a tab can disconnect too.

## Notes

- Saved commands are per device, so a Linux box and a switch each keep only the commands that make sense for them.
- Over SSH there is no interactive prompt for sudo, so the sudo toggle feeds your password to the command for you. Type a plain command and flip the toggle rather than prefixing `sudo` yourself.
- The tool accepts the host key on first connection. Use it on networks you control.

## Security and privacy

- The SSH password is never written to disk.
- `devices.json` holds only the name, host, username, and your saved commands. Keep it out of source control, since it maps your internal hosts and accounts.
- The debug log, when enabled, redacts the password before writing.

## A note on how this was built

This project was built with AI assistance. The design decisions, feature direction, and real-world testing were directed by me. The code was written and revised with an AI assistant against that direction. Treat it like any community tool: review and test it before relying on it.

## License

Released under the [PolyForm Noncommercial License 1.0.0](LICENSE): personal and noncommercial use, modification, and noncommercial redistribution are permitted; commercial use is not. Keep the copyright notice; no warranty. The tool bundles third-party code (PySide6/Qt and Paramiko, both LGPL) and fonts; their notices are in [THIRD-PARTY-LICENSES.txt](THIRD-PARTY-LICENSES.txt).

For commercial licensing, open a [GitHub issue](https://github.com/JDE-Projects/Simple-SSH-Tool/issues) with the title "Commercial License Inquiry".
