#!/usr/bin/env python3
"""Initialize a Godot SDD template checkout as a new game project."""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def validate_inputs(name: str, slug: str, port: int) -> None:
    if not name.strip() or any(ord(char) < 32 for char in name):
        raise ValueError("--name must be nonempty and cannot contain control characters")
    if not SLUG_RE.fullmatch(slug):
        raise ValueError("--slug must use lowercase letters, digits and single hyphens")
    if not 1024 <= port <= 65535:
        raise ValueError("--mcp-port must be between 1024 and 65535")


def _has_existing_specs(root: Path) -> bool:
    specs = root / "specs"
    return specs.exists() and any(path.is_file() for path in specs.rglob("*"))


def _port_is_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _bootstrap_is_pending(root: Path) -> bool:
    path = root / "docs/sdd/bootstrap-playtest.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    expected = (
        "**Lifecycle Status**: AWAITING FIRST PLAYTEST",
        "**First Playable Feature**: PENDING",
        "**Human Approval**: PENDING",
        "Game Feel aprovado: PENDING",
        "Diversão aprovada: PENDING",
        "Estrutura SDD aprovada: PENDING",
        "Evidência da decisão explícita do usuário: PENDING",
    )
    return all(marker in text for marker in expected)


def initialize(root: Path, name: str, slug: str, port: int, dry_run: bool = False) -> list[str]:
    validate_inputs(name, slug, port)
    root = root.resolve()
    marker = root / ".template/project.json"
    if not marker.is_file():
        raise ValueError("Template state file is missing; refusing to modify this directory")
    state = json.loads(marker.read_text(encoding="utf-8"))
    if state.get("project_type") == "game" and state.get("initialized") is True:
        if (state.get("name"), state.get("slug"), state.get("mcp_port")) == (name, slug, port):
            return ["Already initialized with these values; no changes made."]
        raise ValueError("This checkout is already initialized. Refusing to overwrite the game identity or port.")
    if state.get("project_type") != "template" or state.get("initialized") is not False:
        raise ValueError("Unexpected template state; refusing to overwrite project data")
    if _has_existing_specs(root):
        raise ValueError("Feature artifacts already exist under specs/; refusing to reset approvals")
    if not _bootstrap_is_pending(root):
        raise ValueError("Bootstrap approval is missing or no longer pending; refusing to reset user decisions")
    if not _port_is_available(port):
        raise ValueError(f"MCP port {port} is already in use; choose a free local port")

    project_file = root / "project.godot"
    project = project_file.read_text(encoding="utf-8")
    default_name = 'config/name="Godot Game Template"'
    if project.count(default_name) != 1 or project.count("bridge_port=6511") != 1:
        raise ValueError("project.godot no longer matches the clean template defaults")
    project = project.replace(default_name, f"config/name={json.dumps(name, ensure_ascii=False)}")
    project = project.replace("bridge_port=6511", f"bridge_port={port}")

    pending: list[tuple[Path, str]] = [(project_file, project)]
    for relative in ("GDD.md", ".specify/memory/constitution.md"):
        path = root / relative
        content = path.read_text(encoding="utf-8")
        if content.count("{{PROJECT_NAME}}") != 1:
            raise ValueError(f"Expected exactly one project identity marker in {relative}")
        pending.append((path, content.replace("{{PROJECT_NAME}}", name)))

    readme = root / "README.md"
    pending.append((readme, f"""# {name}

Godot 4.7 game project initialized from the Godot SDD Template.

## Development

- Run `python3 scripts/setup.py` after cloning to install the pinned local Godot MCP server and generate local client configuration.
- Run `python3 scripts/test.py` for gdUnit4 gameplay tests and `python3 scripts/test_workflow.py` for workflow validation tests.
- Read `AGENTS.md` and `docs/sdd/lifecycle.md` before starting a feature.

New gameplay features follow the approved Spec-Driven Development lifecycle. No game decisions, feature specifications or user approvals are created by initialization.
"""))
    updated = dict(state)
    updated.update({"project_type": "game", "initialized": True, "name": name, "slug": slug, "mcp_port": port})
    pending.append((marker, json.dumps(updated, ensure_ascii=False, indent=2) + "\n"))

    actions = [f"Set project name to {name!r} and slug to {slug!r}.", f"Set the Godot MCP bridge port to {port}.", "Keep all package and bootstrap approvals pending."]
    if dry_run:
        return ["Dry run; no files changed.", *actions]
    for path, content in pending:
        path.write_text(content, encoding="utf-8", newline="\n")
    return ["Initialized the Godot game project.", *actions]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Human-readable game name")
    parser.add_argument("--slug", required=True, help="Lowercase project slug")
    parser.add_argument("--mcp-port", type=int, required=True, help="Free local Godot MCP bridge port (required; the template uses 6511)")
    parser.add_argument("--dry-run", action="store_true", help="Show planned changes without writing files")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        for message in initialize(args.root, args.name, args.slug, args.mcp_port, args.dry_run):
            print(message)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Initialization failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
