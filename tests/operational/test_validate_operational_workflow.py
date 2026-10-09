from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import validate_operational_workflow as workflow


class WorkflowValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "project.godot").write_text("config_version=5\n", encoding="utf-8")
        (self.root / "docs" / "sdd").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "sdd" / "bootstrap-playtest.md").write_text(
            "**Lifecycle Status**: PASS\n**First Playable Feature**: specs/001-test-feature\n"
            "**Human Approval**: PASS\n-Fingerprint avaliada: first-build\n"
            "- Game Feel aprovado: PASS\n- Diversão aprovada: PASS\n"
            "- Estrutura SDD aprovada: PASS\n"
            "- Evidência da decisão explícita do usuário: explicit approval\n",
            encoding="utf-8",
        )
        self.feature = self.root / "specs" / "001-test-feature"
        self.feature.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write(self, relative: str, text: str) -> None:
        path = self.feature / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def make_complete_feature(self, human_result: str = "PENDING") -> None:
        self.write("epic.md", "**Lifecycle Status**: READY\n")
        self.write(
            "spec.md",
            "**Lifecycle Status**: READY\n**Package Revision**: 1\n"
            "**UI Impact**: NO\n**UI Impact Reason**: No player-facing UI change\n"
            "**UI/UX Status**: NOT REQUIRED\n",
        )
        self.write("plan.md", "**Lifecycle Status**: READY\n**Package Revision**: 1\n")
        self.write("tasks.md", "**Lifecycle Status**: READY\n**Package Revision**: 1\n- [x] Done\n")
        self.write(
            "approval.md",
            "**Analysis Result**: PASS\n**User Decision**: APPROVED\n**Approved Revision**: 1\n"
            "- Evidence of explicit user approval: User approved revision 1\n",
        )
        self.write(
            "implementation-report.md",
            "**Lifecycle Status**: COMPLETE\n**Implemented Revision**: 1\n",
        )
        fingerprint = workflow.source_fingerprint(self.root)
        self.write(
            "qa-report.md",
            f"**Result**: PASS\n**Package Revision**: 1\n**Tested Fingerprint**: {fingerprint}\n",
        )
        self.write(
            "human-playtest.md",
            f"**Result**: {human_result}\n**Tested Fingerprint**: {fingerprint}\n"
            "- Game Feel: PASS\n-Fun: PASS\n- Overall: PASS\n"
            "- Approving user: Joao\n- Decision evidence: Explicit approval\n"
            "- If this is the first playable increment, explicitly approve SDD bootstrap: YES\n",
        )
        self.write(
            "convergence.md",
            "**Lifecycle Status**: CONVERGED\n**Result**: PASS\n**Package Revision**: 1\n",
        )

    def test_missing_spec_routes_to_game_designer(self) -> None:
        result = workflow.feature_route(self.root, self.feature)
        self.assertEqual(result["next_role"], "AGENT_GAME_DESIGNER")

    def test_ui_impact_dispatches_ui_ux_specialist(self) -> None:
        self.write("epic.md", "**Lifecycle Status**: READY\n")
        self.write(
            "spec.md",
            "**Lifecycle Status**: READY\n**UI Impact**: YES\n**UI/UX Status**: PENDING\n",
        )
        result = workflow.feature_route(self.root, self.feature)
        self.assertEqual(result["next_role"], "SUB_AGENT_UI_UX_DESIGNER")

    def test_non_ui_feature_requires_explicit_reason(self) -> None:
        self.write("epic.md", "**Lifecycle Status**: READY\n")
        self.write("spec.md", "**Lifecycle Status**: READY\n**UI Impact**: NO\n**UI/UX Status**: PENDING\n")
        result = workflow.feature_route(self.root, self.feature)
        self.assertEqual(result["next_role"], "AGENT_GAME_DESIGNER")

    def test_qa_failure_routes_back_to_developer(self) -> None:
        self.make_complete_feature()
        self.write("qa-report.md", "**Result**: FAIL\n**Package Revision**: 1\n**Tested Fingerprint**: stale\n")
        result = workflow.feature_route(self.root, self.feature)
        self.assertEqual(result["next_role"], "DEVELOPER")

    def test_playable_source_change_invalidates_human_playtest(self) -> None:
        self.make_complete_feature(human_result="PASS")
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "player.gd").write_text("extends Node\n", encoding="utf-8")
        result = workflow.feature_route(self.root, self.feature)
        self.assertEqual(result["next_role"], "QA")
        (self.feature / "qa-report.md").write_text(
            f"**Result**: PASS\n**Package Revision**: 1\n**Tested Fingerprint**: {workflow.source_fingerprint(self.root)}\n",
            encoding="utf-8",
        )
        result = workflow.feature_route(self.root, self.feature)
        self.assertEqual(result["next_role"], "USER")

    def test_documentation_does_not_stale_playable_fingerprint(self) -> None:
        before = workflow.source_fingerprint(self.root)
        (self.root / "docs").mkdir(exist_ok=True)
        (self.root / "docs" / "note.md").write_text("Changed docs\n", encoding="utf-8")
        self.assertEqual(before, workflow.source_fingerprint(self.root))

    def test_only_explicit_human_pass_makes_feature_eligible(self) -> None:
        self.make_complete_feature(human_result="PASS")
        result = workflow.feature_route(self.root, self.feature)
        self.assertEqual(result["status"], "MAIN_ELIGIBLE")

    def test_first_playtest_must_explicitly_include_bootstrap(self) -> None:
        self.make_complete_feature(human_result="PASS")
        (self.root / "docs" / "sdd" / "bootstrap-playtest.md").write_text(
            "**Lifecycle Status**: AWAITING FIRST PLAYTEST\n", encoding="utf-8"
        )
        playtest_path = self.feature / "human-playtest.md"
        playtest_path.write_text(
            playtest_path.read_text(encoding="utf-8").replace(
                "explicitly approve SDD bootstrap: YES", "explicitly approve SDD bootstrap: PENDING"
            ),
            encoding="utf-8",
        )
        result = workflow.feature_route(self.root, self.feature)
        self.assertEqual(result["status"], "BOOTSTRAP_PLAYTEST")
        self.assertEqual(result["next_role"], "USER")

    def test_unchecked_task_blocks_main_eligibility(self) -> None:
        self.make_complete_feature(human_result="PASS")
        self.write("tasks.md", "**Lifecycle Status**: READY\n**Package Revision**: 1\n- [ ] Not done\n")
        result = workflow.feature_route(self.root, self.feature)
        self.assertEqual(result["status"], "REMAINING_TASKS")

    def test_bootstrap_gate_blocks_even_complete_feature(self) -> None:
        self.make_complete_feature(human_result="PASS")
        (self.root / "docs" / "sdd").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "sdd" / "bootstrap-playtest.md").write_text(
            "**Lifecycle Status**: AWAITING FIRST PLAYTEST\n", encoding="utf-8"
        )
        result = workflow.main_gate(self.root, self.feature)
        self.assertFalse(result["eligible"])
        self.assertIn("bootstrap", result["blockers"][0].lower())

    def test_bootstrap_gate_passes_after_explicit_user_approval(self) -> None:
        self.make_complete_feature(human_result="PASS")
        (self.root / "docs" / "sdd").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "sdd" / "bootstrap-playtest.md").write_text(
            "**Lifecycle Status**: PASS\n**First Playable Feature**: specs/001-test-feature\n"
            "**Human Approval**: PASS\n-Fingerprint avaliada: build-123\n"
            "- Game Feel aprovado: PASS\n- Diversão aprovada: PASS\n"
            "- Estrutura SDD aprovada: PASS\n"
            "- Evidência da decisão explícita do usuário: explicit message\n",
            encoding="utf-8",
        )
        result = workflow.main_gate(self.root, self.feature)
        self.assertTrue(result["eligible"])

    def test_direct_change_requires_its_summary_before_qa(self) -> None:
        change = self.root / "docs" / "sdd" / "direct-changes" / "001-fix"
        result = workflow.direct_change_gate(self.root, change)
        self.assertEqual(result["next_role"], "ORCHESTRATOR")
        self.assertEqual(result["status"], "CHANGE_SUMMARY")

    def test_direct_change_requires_qa_before_human_playtest(self) -> None:
        change = self.root / "docs" / "sdd" / "direct-changes" / "001-fix"
        change.mkdir(parents=True)
        (change / "change.md").write_text(
            "**Lifecycle Status**: READY\n**Change Type**: BUG FIX\n"
            "**Summary**: Fix input capture\n**Reason**: The action was dropped\n",
            encoding="utf-8",
        )
        result = workflow.direct_change_gate(self.root, change)
        self.assertEqual(result["next_role"], "QA")

    def test_direct_change_qa_failure_routes_to_developer(self) -> None:
        change = self.root / "docs" / "sdd" / "direct-changes" / "001-fix"
        change.mkdir(parents=True)
        (change / "change.md").write_text(
            "**Lifecycle Status**: READY\n**Change Type**: BUG FIX\n"
            "**Summary**: Fix input capture\n**Reason**: The action was dropped\n",
            encoding="utf-8",
        )
        (change / "qa-report.md").write_text("**Result**: FAIL\n", encoding="utf-8")
        result = workflow.direct_change_gate(self.root, change)
        self.assertEqual(result["next_role"], "DEVELOPER")

    def test_direct_change_can_pass_all_gates(self) -> None:
        change = self.root / "docs" / "sdd" / "direct-changes" / "001-fix"
        change.mkdir(parents=True)
        (change / "change.md").write_text(
            "**Lifecycle Status**: READY\n**Change Type**: DOCUMENTATION\n"
            "**Summary**: Update onboarding docs\n**Reason**: Clarify test invocation\n",
            encoding="utf-8",
        )
        (self.root / "docs" / "sdd" / "bootstrap-playtest.md").parent.mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "sdd" / "bootstrap-playtest.md").write_text(
            "**Lifecycle Status**: PASS\n**First Playable Feature**: specs/001-first\n"
            "**Human Approval**: PASS\n-Fingerprint avaliada: first-build\n"
            "- Game Feel aprovado: PASS\n- Diversão aprovada: PASS\n"
            "- Estrutura SDD aprovada: PASS\n"
            "- Evidência da decisão explícita do usuário: explicit approval\n",
            encoding="utf-8",
        )
        fingerprint = workflow.source_fingerprint(self.root)
        (change / "qa-report.md").write_text(
            f"**Result**: PASS\n**Tested Fingerprint**: {fingerprint}\n", encoding="utf-8"
        )
        (change / "human-playtest.md").write_text(
            f"**Result**: PASS\n**Overall**: PASS\n**Game Feel**: PASS\n**Fun**: PASS\n"
            f"**Tested Fingerprint**: {fingerprint}\n**Approving user**: Joao\n"
            "**Decision evidence**: explicit approval\n",
            encoding="utf-8",
        )
        result = workflow.direct_change_gate(self.root, change)
        self.assertTrue(result["eligible"])


if __name__ == "__main__":
    unittest.main()
