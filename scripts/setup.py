#!/usr/bin/env python3
"""Check local prerequisites, install the pinned MCP server and write local client configs."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def project_port(root: Path) -> int:
    state_path = root / ".template/project.json"
    if not state_path.is_file():
        raise ValueError("Missing .template/project.json; initialize the project from the template first")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    port = state.get("mcp_port")
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("Project MCP port is invalid")
    project = (root / "project.godot").read_text(encoding="utf-8")
    if not re.search(rf"(?m)^bridge_port={port}$", project):
        raise ValueError("The MCP port in project.godot does not match .template/project.json")
    return port


def generate_local_configs(root: Path, port: int) -> tuple[Path, Path]:
    root = root.resolve()
    server = (root / "node_modules/@letsagents/godot-mcp/server.js").resolve()
    template = root / ".codex/config.example.toml"
    if not template.is_file():
        raise ValueError("Codex MCP config example is missing")
    toml_text = template.read_text(encoding="utf-8")
    toml_text = toml_text.replace("{{MCP_SERVER}}", json.dumps(str(server), ensure_ascii=False)[1:-1])
    toml_text = toml_text.replace("{{PROJECT_ROOT}}", json.dumps(str(root), ensure_ascii=False)[1:-1])
    toml_text = toml_text.replace("{{MCP_PORT}}", str(port))
    toml_path = root / ".codex/config.toml"
    toml_path.write_text(toml_text, encoding="utf-8", newline="\n")
    tomllib.loads(toml_text)

    mcp_path = root / ".mcp.json"
    mcp_data = {"mcpServers": {"godot-mcp": {
        "command": "node", "args": [str(server)], "cwd": str(root),
        "env": {"GODOT_MCP_BRIDGE_PORT": str(port)},
    }}}
    mcp_path.write_text(json.dumps(mcp_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return toml_path, mcp_path


def _version(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return (result.stdout or result.stderr).strip().splitlines()[0]


def check_prerequisites(check_godot: bool = True) -> list[str]:
    if sys.version_info < (3, 11):
        raise ValueError("Python 3.11 or newer is required")
    versions = [f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"]
    node = shutil.which("node")
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not node or not npm:
        raise ValueError("Node.js 20+ and npm are required on PATH")
    node_version = _version([node, "--version"])
    match = re.search(r"v?(\d+)", node_version)
    if not match or int(match.group(1)) < 20:
        raise ValueError(f"Node.js 20 or newer is required; found {node_version}")
    versions.append(f"Node.js {node_version}")
    if check_godot:
        candidates = [os.environ.get("GODOT_BIN", ""), "godot", "godot4", "Godot", "godot.exe"]
        godot = next((shutil.which(candidate) for candidate in candidates if candidate and shutil.which(candidate)), None)
        if not godot:
            raise ValueError("Godot 4.7.x was not found on PATH; set GODOT_BIN to its executable")
        godot_version = _version([godot, "--version"])
        if not re.match(r"^4\.7\.\d+", godot_version):
            raise ValueError(f"Godot 4.7.x is required; found {godot_version}")
        versions.append(f"Godot {godot_version}")
    return versions


def install_dependencies(root: Path) -> None:
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        raise ValueError("npm was not found on PATH")
    command = [npm, "ci"]
    if os.name == "nt" and npm.lower().endswith((".cmd", ".bat")):
        command = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", f'"{npm}" ci']
    subprocess.run(command, cwd=root, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-npm", action="store_true", help="Only check tools and regenerate local configs")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        versions = check_prerequisites()
        port = project_port(root)
        if not args.skip_npm:
            install_dependencies(root)
        toml_path, mcp_path = generate_local_configs(root, port)
        print("Prerequisites: " + ", ".join(versions))
        print(f"Generated local Codex config: {toml_path}")
        print(f"Generated local MCP config: {mcp_path}")
        if args.skip_npm:
            print("Skipped npm ci by request.")
        else:
            print("Installed exact package versions from package-lock.json with npm ci.")
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
        print(f"Setup failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
