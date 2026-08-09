"""Invented, realistic data for the README screenshot. No user data is read."""

DEVICES = [
    {
        "id": "edge-gateway",
        "name": "EDGE-GW-01",
        "host": "10.42.8.10",
        "username": "opsadmin",
        "commands": [
            {"name": "Service status", "command": "systemctl --failed", "sudo": False, "confirm": "", "pinned": True},
            {"name": "Disk usage", "command": "df -h /", "sudo": False, "confirm": "", "pinned": True},
        ],
    },
    {
        "id": "app-node",
        "name": "APP-NODE-02",
        "host": "10.42.8.22",
        "username": "deploy",
        "commands": [
            {"name": "Release health", "command": "sudo /opt/app/bin/healthcheck", "sudo": True, "confirm": "", "pinned": True},
            {"name": "Recent errors", "command": "journalctl -u app.service -n 50", "sudo": False, "confirm": "", "pinned": False},
        ],
    },
    {
        "id": "backup-node",
        "name": "BACKUP-01",
        "host": "10.42.8.45",
        "username": "backupsvc",
        "commands": [
            {"name": "Replication status", "command": "restic snapshots --latest 1", "sudo": False, "confirm": "", "pinned": True},
        ],
    },
]

CONSOLE_LINES = [
    ("edge-gateway", "$ systemctl --failed", "cmd"),
    ("edge-gateway", "0 loaded units listed.", "ok"),
    ("edge-gateway", "EDGE-GW-01 · 27 days uptime · 3.1 GiB free memory", "out"),
]
