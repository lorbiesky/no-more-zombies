#!/usr/bin/env python3
"""Run the Godot gameplay test suites with cross-platform paths and logging."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def find_godot() -> str | None:
    candidates = [os.environ.get("GODOT_BIN", ""), "godot", "godot4", "Godot", "godot.exe"]
    return next((shutil.which(candidate) for candidate in candidates if candidate and shutil.which(candidate)), None)


def main() -> int:
    godot = find_godot()
    if not godot:
        print("Godot executable not found. Set GODOT_BIN or add Godot 4.7.x to PATH.", file=sys.stderr)
        return 127
    version = subprocess.run([godot, "--version"], capture_output=True, text=True)
    found = (version.stdout or version.stderr).strip()
    if version.returncode or not re.match(r"^4\.7\.\d+", found):
        print(f"Expected Godot 4.7.x; found: {found or 'unknown'}", file=sys.stderr)
        return 2
    plugin = ROOT / "addons/gdUnit4/plugin.cfg"
    if not (ROOT / "addons/gdUnit4/bin/GdUnitCmdTool.gd").is_file():
        print("gdUnit4 command runner is missing from addons/gdUnit4.", file=sys.stderr)
        return 2
    if not re.search(r'(?m)^version="6\.2\.1"$', plugin.read_text(encoding="utf-8")):
        print("Expected gdUnit4 6.2.1 in addons/gdUnit4/plugin.cfg.", file=sys.stderr)
        return 2

    output = ROOT / "test-results/gdunit4"
    output.mkdir(parents=True, exist_ok=True)
    user_data = ROOT / ".godot/test-user-data"
    user_data.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if os.name == "nt":
        env["APPDATA"] = str(user_data / "appdata")
        (user_data / "appdata").mkdir(parents=True, exist_ok=True)
    elif sys.platform == "darwin":
        env["HOME"] = str(user_data / "home")
        (user_data / "home").mkdir(parents=True, exist_ok=True)
    else:
        env["XDG_DATA_HOME"] = str(user_data)
    scan_command = [godot, "--headless", "--editor", "--path", str(ROOT), "--quit"]
    scan = subprocess.run(scan_command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if scan.returncode:
        print(scan.stdout, end="")
        print("Godot failed to scan/import the project before running tests.", file=sys.stderr)
        return scan.returncode
    if scan.stdout.strip():
        print(scan.stdout, end="")
    command = [
        godot, "--headless", "--path", str(ROOT), "--audio-driver", "Dummy",
        "-s", "res://addons/gdUnit4/bin/GdUnitCmdTool.gd",
        "--ignoreHeadlessMode", "-c",
        "-a", "res://tests/unit",
        "-a", "res://tests/integration",
        "-rd", "res://test-results/gdunit4",
    ]
    log = output / "console.log"
    result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log.write_text(result.stdout, encoding="utf-8", newline="\n")
    print(result.stdout, end="")
    print(f"Godot {found}; log: {log}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
