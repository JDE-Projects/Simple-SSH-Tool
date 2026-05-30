# Simple SSH Tool

A small, standalone desktop tool to connect to your machines over SSH and run your own saved commands or one-off custom commands, with live output. Add a device, type the password when you connect, and use one-tap command buttons or a free command box. The interface is a clean web-style window.

Built by [JDE-Projects](https://github.com/JDE-Projects).

## Highlights

- **Per-device command library.** Build your own named commands for each device, mark some with sudo or a confirm prompt, and pin up to 10 as quick buttons on the card.
- **Passwords are never saved.** The SSH password is held in memory only and wiped on disconnect. Only the name, host, username, and saved commands are written to `devices.json`.
- **Multiple connections at once.** Up to five devices connect independently, each with its own console tab.
- **Tabbed console with export.** Timestamped, per-device output. Export the active tab to a text file next to the app, and clear it when you want a fresh view.
- **Custom command box.** Type any command, toggle sudo when you need it, and the tool offers to save it to that device's library for next time.

## How it works

- The backend uses [Paramiko](https://www.paramiko.org/) for SSH and runs each command on its own channel, streaming output back line by line.
- The window is a [pywebview](https://pywebview.flowrl.com/) host on the Qt backend, with the UI in `simple_ssh_tool-UI.html`.
- `devices.json` is portable: it carries a small header with the project URL, so you can back it up or move it to another machine. Older single-type config files migrate automatically on first load.

## Download and run

Grab the latest `Simple SSH Tool.exe` from the [Releases](../../releases) page and double-click it. No Python or setup required. Windows only.

Because it is unsigned, Windows SmartScreen may warn about an unknown publisher the first time. Click **More info > Run anyway**.

## Build from source (optional)

If you would rather run or build it yourself, you need:

- **Python 3** on the machine's PATH.
- Python packages: `pywebview`, `PyQt6`, `PyQt6-WebEngine`, `paramiko`.

```
pip install pywebview PyQt6 PyQt6-WebEngine paramiko
```

Keep `simple_ssh_tool.py` and `simple_ssh_tool-UI.html` together (the app loads the HTML next to itself). Then either:

- **Run from source:** `python simple_ssh_tool.py`
- **Build the .exe:** double-click `Build_Simple_SSH_Tool.bat`, which uses PyInstaller to produce `dist\Simple SSH Tool.exe`. The included `splash.png` shows while the app starts.

## Using it

1. Click **Add Device**, give it a display name, then enter the host or IP and the username.
2. On the device card, type the password and click **Connect**. A console tab opens for it.
3. Manage that device's commands in the **Command Library** pane along the bottom: add, edit, delete, and pin. Pinned commands appear as quick buttons on the card.
4. Run a saved command, pin, or type one in the custom box (toggle **sudo** if it needs root). Commands with a confirm message ask before firing.
5. **Export** saves the active tab's console to a text file next to the app. **Disconnect** clears the password from memory; closing a tab can disconnect too.

## Notes

- Saved commands are per device, so a Linux box and a switch each keep only the commands that make sense for them.
- Over SSH there is no interactive prompt for sudo, so the sudo toggle feeds your password to the command for you. Type a plain command and flip the toggle rather than prefixing `sudo` yourself.
- The tool accepts the host key on first connection. Use it on networks you control.

## Security and privacy

- The SSH password is never written to disk.
- `devices.json` holds only the name, host, username, and your saved commands. Keep it out of source control, since it maps your internal hosts and accounts.

## A note on how this was built

This project was built with AI assistance. The design decisions, feature direction, and real-world testing were directed by me. The code was written and revised with an AI assistant against that direction. Treat it like any community tool: review and test it before relying on it.

## License

Released under the [MIT License](LICENSE). You are free to use, modify, and distribute it; keep the copyright notice, and it comes with no warranty.
