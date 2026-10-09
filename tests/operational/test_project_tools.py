from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


INIT = load_module("init_project", ROOT / "scripts/init_project.py")
SETUP = load_module("setup_project", ROOT / "scripts/setup.py")


class ProjectInitializationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        files = {
            ".template/project.json": json.dumps({"project_type": "template", "initialized": False, "name": "Godot Game Template", "slug": "godot-sdd-template", "mcp_port": 6511}),
            "project.godot": '\n'.join(['config/name="Godot Game Template"', 'bridge_port=6511', '']),
            "GDD.md": '# GDD — {{PROJECT_NAME}}\n',
            ".specify/memory/constitution.md": '# {{PROJECT_NAME}} — Constitution\n',
            "docs/gdd/vision.md": '# Vision\n',
            "docs/sdd/bootstrap-playtest.md": '\n'.join([
                '**Lifecycle Status**: AWAITING FIRST PLAYTEST',
                '**First Playable Feature**: PENDING',
                '**Human Approval**: PENDING',
                'Game Feel aprovado: PENDING',
                'Diversão aprovada: PENDING',
                'Estrutura SDD aprovada: PENDING',
                'Evidência da decisão explícita do usuário: PENDING',
            ]),
            "README.md": '# Godot SDD Template\n',
        }
        for relative, content in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        marker = self.root / ".template/project.json"
        state = json.loads(marker.read_text(encoding="utf-8"))
        state["readme_sha256"] = hashlib.sha256((self.root / "README.md").read_bytes()).hexdigest()
        marker.write_text(json.dumps(state), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_dry_run_does_not_modify_files(self):
        before = (self.root / "project.godot").read_text(encoding="utf-8")
        result = INIT.initialize(self.root, "Ação: Noite", "acao-noite", 6512, dry_run=True)
        self.assertIn("Dry run; no files changed.", result)
        self.assertEqual(before, (self.root / "project.godot").read_text(encoding="utf-8"))
        self.assertFalse(json.loads((self.root / ".template/project.json").read_text())['initialized'])

    def test_unicode_name_custom_port_and_pending_approvals(self):
        INIT.initialize(self.root, "Ação: Noite", "acao-noite", 6512)
        self.assertIn('config/name="Ação: Noite"', (self.root / "project.godot").read_text(encoding="utf-8"))
        self.assertIn("bridge_port=6512", (self.root / "project.godot").read_text(encoding="utf-8"))
        self.assertIn("Ação: Noite", (self.root / "GDD.md").read_text(encoding="utf-8"))
        self.assertIn("Ação: Noite", (self.root / ".specify/memory/constitution.md").read_text(encoding="utf-8"))
        self.assertIn("Game Feel aprovado: PENDING", (self.root / "docs/sdd/bootstrap-playtest.md").read_text(encoding="utf-8"))
        self.assertIn("No game decisions", (self.root / "README.md").read_text(encoding="utf-8"))

    def test_same_initialization_is_idempotent_and_conflicts_are_rejected(self):
        INIT.initialize(self.root, "Puzzle", "puzzle", 6512)
        result = INIT.initialize(self.root, "Puzzle", "puzzle", 6512)
        self.assertIn("Already initialized", result[0])
        with self.assertRaisesRegex(ValueError, "already initialized"):
            INIT.initialize(self.root, "Different", "different", 6513)

    def test_existing_specs_and_approval_changes_block_initialization(self):
        specs = self.root / "specs/feature/spec.md"
        specs.parent.mkdir(parents=True)
        specs.write_text("existing spec", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Feature artifacts already exist"):
            INIT.initialize(self.root, "Puzzle", "puzzle", 6512)
        specs.unlink()
        bootstrap = self.root / "docs/sdd/bootstrap-playtest.md"
        bootstrap.write_text(bootstrap.read_text().replace("**Human Approval**: PENDING", "**Human Approval**: PASS"))
        with self.assertRaisesRegex(ValueError, "no longer pending"):
            INIT.initialize(self.root, "Puzzle", "puzzle", 6512)

    def test_port_in_use_blocks_initialization(self):
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
            with self.assertRaisesRegex(ValueError, "already in use"):
                INIT.initialize(self.root, "Puzzle", "puzzle", port)
        self.assertFalse(json.loads((self.root / ".template/project.json").read_text())["initialized"])

    def test_invalid_name_slug_and_port_are_rejected(self):
        for args in [("", "game", 6512), ("Game", "Bad-Slug", 6512), ("Game", "game", 80)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                INIT.validate_inputs(*args)

    def test_initialized_game_routes_to_discovery_and_is_not_main_eligible(self):
        for directory in ("assets", "scenes", "scripts"):
            (self.root / directory).mkdir(exist_ok=True)
            (self.root / directory / ".gitkeep").write_text("", encoding="utf-8")
        validator = self.root / "scripts/validate_operational_workflow.py"
        validator.write_text((ROOT / "scripts/validate_operational_workflow.py").read_text(encoding="utf-8"), encoding="utf-8")
        INIT.initialize(self.root, "Meu Jogo", "meu-jogo", 6512)
        route = subprocess.run(
            [sys.executable, str(validator), "--route", "--json", "--root", str(self.root)],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(json.loads(route.stdout)["next_role"], "AGENT_GAME_DESIGNER")
        main = subprocess.run(
            [sys.executable, str(validator), "--check-main", "--json", "--root", str(self.root)],
            capture_output=True, text=True,
        )
        self.assertEqual(main.returncode, 1)
        self.assertFalse(json.loads(main.stdout)["eligible"])


class LocalMcpConfigurationTests(unittest.TestCase):
    def test_generates_matching_codex_and_claude_configs_without_machine_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".codex").mkdir()
            (root / ".codex/config.example.toml").write_text('''[mcp_servers.godot-mcp]
command = "node"
args = ["{{MCP_SERVER}}"]
cwd = "{{PROJECT_ROOT}}"
env = { GODOT_MCP_BRIDGE_PORT = "{{MCP_PORT}}" }
[agents]
enabled = true
max_concurrent_threads_per_session = 3
''', encoding="utf-8")
            codex, mcp = SETUP.generate_local_configs(root, 6512)
            codex_doc = tomllib.loads(codex.read_text(encoding="utf-8"))
            mcp_doc = json.loads(mcp.read_text(encoding="utf-8"))
            self.assertEqual(codex_doc["mcp_servers"]["godot-mcp"]["env"]["GODOT_MCP_BRIDGE_PORT"], "6512")
            self.assertEqual(mcp_doc["mcpServers"]["godot-mcp"]["env"]["GODOT_MCP_BRIDGE_PORT"], "6512")
            server = root.resolve() / "node_modules/@letsagents/godot-mcp/server.js"
            self.assertEqual(Path(codex_doc["mcp_servers"]["godot-mcp"]["args"][0]), server)
            self.assertEqual(Path(mcp_doc["mcpServers"]["godot-mcp"]["args"][0]), server)
            self.assertEqual(codex_doc["agents"]["max_concurrent_threads_per_session"], 3)


if __name__ == "__main__":
    unittest.main()
