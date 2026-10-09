#!/usr/bin/env python3
"""Resolve SDD ownership and validate the local main-integration gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAYABLE_PATHS = (Path("project.godot"), Path("scenes"), Path("scripts"), Path("assets"))
PENDING_VALUES = {"", "PENDING", "TBD", "DRAFT", "N/A"}


def source_fingerprint(root: Path = ROOT) -> str:
    """Hash all project/runtime inputs while excluding workflow documentation."""
    digest = hashlib.sha256()
    for relative in PLAYABLE_PATHS:
        candidate = root / relative
        paths = [candidate] if candidate.is_file() else (
            sorted(path for path in candidate.rglob("*") if path.is_file())
            if candidate.is_dir()
            else []
        )
        for path in paths:
            if ".godot" in path.parts or path.name == ".gitkeep":
                continue
            if relative == Path("scripts") and path.suffix.lower() not in {".gd", ".cs", ".gdshaderinc", ".gdshader"}:
                continue
            relpath = path.relative_to(root).as_posix()
            digest.update(relpath.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def field(text: str, label: str, default: str = "") -> str:
    pattern = re.compile(
        rf"^\s*(?:[-*]\s*)?\**{re.escape(label)}\**\s*:\s*(.*?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else default


def artifact(feature: Path, name: str) -> tuple[Path, str]:
    path = feature / name
    return path, read_text(path)


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).upper()


def tasks_complete(text: str) -> bool:
    checks = re.findall(r"^\s*-\s+\[([ xX])\]", text, re.MULTILINE)
    return bool(checks) and all(value.lower() == "x" for value in checks)


def next_role_for_pending_task(text: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^\s*-\s+\[ \]\s+(.*)$", line, re.IGNORECASE)
        if not match:
            continue
        task = match.group(1).lower()
        if "playtest" in task or "human approval" in task:
            return "USER"
        if "ui/ux" in task or "interface specification" in task:
            return "SUB_AGENT_UI_UX_DESIGNER"
        if "qa" in task or "test" in task or "regression" in task:
            return "QA"
        return "DEVELOPER"
    return "DEVELOPER"


def feature_route(root: Path, feature: Path) -> dict[str, Any]:
    feature = feature.resolve()
    root = root.resolve()
    try:
        feature.relative_to(root / "specs")
    except ValueError:
        return {
            "feature_dir": str(feature),
            "status": "INVALID_FEATURE_PATH",
            "next_role": None,
            "reasons": ["Feature directory must be under this project's specs/ directory."],
        }

    epic_path, epic = artifact(feature, "epic.md")
    spec_path, spec = artifact(feature, "spec.md")
    plan_path, plan = artifact(feature, "plan.md")
    tasks_path, tasks = artifact(feature, "tasks.md")
    approval_path, approval = artifact(feature, "approval.md")
    implementation_path, implementation = artifact(feature, "implementation-report.md")
    qa_path, qa = artifact(feature, "qa-report.md")
    playtest_path, playtest = artifact(feature, "human-playtest.md")
    convergence_path, convergence = artifact(feature, "convergence.md")
    current_fingerprint = source_fingerprint(root)
    reasons: list[str] = []

    if not epic_path.is_file() or normalized(field(epic, "Lifecycle Status", "DRAFT")) != "READY":
        return route(feature, "DISCOVERY", "AGENT_GAME_DESIGNER", "Complete the Epic and mark it READY before specifying the increment.", current_fingerprint)
    if not spec_path.is_file():
        return route(feature, "NEEDS_DISCOVERY", "AGENT_GAME_DESIGNER", "No spec.md exists yet.", current_fingerprint)
    spec_status = normalized(field(spec, "Lifecycle Status", field(spec, "Status", "DRAFT")))
    if spec_status in {"DRAFT", "NEEDS CLARIFICATION", ""}:
        return route(feature, "SPECIFICATION", "AGENT_GAME_DESIGNER", "Complete discovery and the functional specification.", current_fingerprint)

    ui_impact = normalized(field(spec, "UI Impact", "TBD"))
    ux_status = normalized(field(spec, "UI/UX Status", "PENDING"))
    if ui_impact in {"YES", "TRUE"} and ux_status not in {"COMPLETE", "READY", "PASS"}:
        return route(feature, "UI_UX_SPECIFICATION", "SUB_AGENT_UI_UX_DESIGNER", "Complete the assigned UI/UX GDD and spec sections.", current_fingerprint)
    if ui_impact not in {"YES", "NO"}:
        return route(feature, "UI_IMPACT_CLASSIFICATION", "AGENT_GAME_DESIGNER", "Classify player-facing UI/HUD/menu/visual-feedback impact.", current_fingerprint)
    if ui_impact == "NO" and ux_status not in {"NOT REQUIRED", "N/A", "NO"}:
        return route(feature, "UI_UX_CLASSIFICATION", "AGENT_GAME_DESIGNER", "Record why UI/UX delegation is not required.", current_fingerprint)
    if ui_impact == "NO" and normalized(field(spec, "UI Impact Reason", "PENDING")) in PENDING_VALUES:
        return route(feature, "UI_UX_CLASSIFICATION", "AGENT_GAME_DESIGNER", "Record why UI/UX delegation is not required.", current_fingerprint)

    if not plan_path.is_file() or not tasks_path.is_file():
        return route(feature, "PLANNING", "TECH_LEAD", "Create plan.md and tasks.md from the approved specification.", current_fingerprint)
    plan_status = normalized(field(plan, "Lifecycle Status", "DRAFT"))
    tasks_status = normalized(field(tasks, "Lifecycle Status", "DRAFT"))
    if plan_status != "READY" or tasks_status != "READY":
        return route(feature, "PLANNING", "TECH_LEAD", "Complete plan/tasks and mark both READY.", current_fingerprint)
    if not approval_path.is_file():
        return route(feature, "ANALYSIS", "TECH_LEAD", "Record analyze findings and package revision in approval.md.", current_fingerprint)
    analysis = normalized(field(approval, "Analysis Result", "PENDING"))
    if analysis != "PASS":
        return route(feature, "ANALYSIS", "TECH_LEAD", "Resolve analyze findings and record PASS in approval.md.", current_fingerprint)

    revision = field(spec, "Package Revision", "")
    if not revision or field(plan, "Package Revision", "") != revision or field(tasks, "Package Revision", "") != revision:
        return route(feature, "PACKAGE_REVISION", "TECH_LEAD", "Align the package revision across spec, plan and tasks.", current_fingerprint)
    if normalized(field(approval, "User Decision", "PENDING")) != "APPROVED" or field(approval, "Approved Revision", "") != revision:
        return route(feature, "PACKAGE_APPROVAL", "AGENT_GAME_DESIGNER", "Present spec, plan and tasks for explicit user approval.", current_fingerprint)
    if normalized(field(approval, "Evidence of explicit user approval", "PENDING")) in PENDING_VALUES:
        return route(feature, "PACKAGE_APPROVAL", "AGENT_GAME_DESIGNER", "Record evidence of the user's explicit package approval.", current_fingerprint)

    if not implementation_path.is_file():
        return route(feature, "IMPLEMENTATION", "DEVELOPER", "Implement the approved tasks and create implementation-report.md.", current_fingerprint)
    if normalized(field(implementation, "Lifecycle Status", "IN PROGRESS")) != "COMPLETE" or field(implementation, "Implemented Revision", "") != revision:
        return route(feature, "IMPLEMENTATION", "DEVELOPER", "Complete approved implementation tasks and record evidence.", current_fingerprint)

    if not qa_path.is_file():
        return route(feature, "TECHNICAL_QA", "QA", "Create and run gdUnit4 gameplay tests; write qa-report.md.", current_fingerprint)
    qa_result = normalized(field(qa, "Result", "PENDING"))
    qa_fingerprint = field(qa, "Tested Fingerprint", "")
    if qa_result in {"FAIL", "FAILED"}:
        return route(feature, "TECHNICAL_REMEDIATION", "DEVELOPER", "Fix the QA failures within approved scope, then return the feature to QA.", current_fingerprint)
    if qa_result != "PASS" or field(qa, "Package Revision", "") != revision or qa_fingerprint != current_fingerprint:
        reason = "Run QA or fix reported technical failures." if qa_result != "PASS" else "QA evidence is stale or belongs to another package revision; rerun it."
        return route(feature, "TECHNICAL_QA", "QA", reason, current_fingerprint)

    if not playtest_path.is_file():
        return route(feature, "HUMAN_PLAYTEST", "USER", "Present the tested build and request explicit approval of Game Feel and fun.", current_fingerprint)
    human_result = normalized(field(playtest, "Result", "PENDING"))
    human_fingerprint = field(playtest, "Tested Fingerprint", "")
    human_approval = normalized(field(playtest, "Overall", field(playtest, "Overall Decision", "PENDING")))
    if human_result in {"FAIL", "FAILED", "REJECTED"} or human_approval in {"FAIL", "FAILED", "REJECTED"}:
        return route(feature, "PLAYTEST_FEEDBACK", "AGENT_GAME_DESIGNER", "Review the user's feedback and agree any gameplay changes before implementation.", current_fingerprint)
    if human_result != "PASS" or human_approval != "PASS" or human_fingerprint != current_fingerprint:
        return route(feature, "HUMAN_PLAYTEST", "USER", "A current explicit user PASS for Game Feel and fun is required.", current_fingerprint)
    if normalized(field(playtest, "Game Feel", "PENDING")) != "PASS" or normalized(field(playtest, "Fun", "PENDING")) != "PASS":
        return route(feature, "HUMAN_PLAYTEST", "USER", "Record separate explicit PASS decisions for Game Feel and fun.", current_fingerprint)
    if normalized(field(playtest, "Approving user", "PENDING")) in PENDING_VALUES or normalized(field(playtest, "Decision evidence", "PENDING")) in PENDING_VALUES:
        return route(feature, "HUMAN_PLAYTEST", "USER", "Record the user's explicit approval evidence.", current_fingerprint)

    if not convergence_path.is_file() or normalized(field(convergence, "Lifecycle Status", "PENDING")) != "CONVERGED" or normalized(field(convergence, "Result", "PENDING")) != "PASS":
        return route(feature, "CONVERGENCE", "SPECKIT_CONVERGE", "Run converge and record that no approved work remains.", current_fingerprint)
    if field(convergence, "Package Revision", "") != revision:
        return route(feature, "CONVERGENCE", "SPECKIT_CONVERGE", "Recheck convergence against the current package revision.", current_fingerprint)
    if not tasks_complete(tasks):
        next_role = next_role_for_pending_task(tasks)
        return route(feature, "REMAINING_TASKS", next_role, "Complete or resolve every remaining approved task, then repeat QA and convergence.", current_fingerprint)

    if not bootstrap_approval_valid(root):
        bootstrap_decision = normalized(
            field(playtest, "If this is the first playable increment, explicitly approve SDD bootstrap", "PENDING")
        )
        if bootstrap_decision not in {"YES", "PASS"}:
            return route(feature, "BOOTSTRAP_PLAYTEST", "USER", "The user's first playtest must explicitly approve the SDD bootstrap too.", current_fingerprint)
        return route(feature, "BOOTSTRAP_RECORD", "ORCHESTRATOR", "Record the user's explicit bootstrap approval in docs/sdd/bootstrap-playtest.md.", current_fingerprint)

    return route(feature, "MAIN_ELIGIBLE", "MAIN", "All feature-local technical, human and convergence gates pass.", current_fingerprint)


def route(feature: Path, status: str, next_role: str, reason: str, fingerprint: str) -> dict[str, Any]:
    return {
        "feature_dir": str(feature),
        "status": status,
        "next_role": next_role,
        "reasons": [reason],
        "source_fingerprint": fingerprint,
    }


def discover_feature(root: Path, explicit: str | None) -> tuple[Path | None, list[str]]:
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            path = root / path
        return path, []
    specs_dir = root / "specs"
    candidates = sorted(path for path in specs_dir.iterdir() if path.is_dir() and (path / "spec.md").is_file()) if specs_dir.is_dir() else []
    if len(candidates) > 1:
        return None, [path.relative_to(root).as_posix() for path in candidates]
    return (candidates[0], []) if candidates else (None, [])


def main_gate(root: Path, feature: Path) -> dict[str, Any]:
    result = feature_route(root, feature)
    blockers: list[str] = []
    if result["status"] != "MAIN_ELIGIBLE":
        blockers.extend(result["reasons"])
        blockers.append(f"Feature route is {result['status']} (next: {result['next_role']}).")
    if not bootstrap_approval_valid(root):
        blockers.append("The first playable human playtest has not explicitly approved the SDD bootstrap.")
        if result["status"] == "MAIN_ELIGIBLE":
            result["status"] = "BOOTSTRAP_PLAYTEST"
            result["next_role"] = "USER"
    result["mode"] = "check-main"
    result["eligible"] = not blockers
    result["blockers"] = blockers
    return result


def valid_human_approval(report: str) -> bool:
    return (
        normalized(field(report, "Result", "PENDING")) == "PASS"
        and normalized(field(report, "Overall", field(report, "Overall Decision", "PENDING"))) == "PASS"
        and normalized(field(report, "Game Feel", "PENDING")) == "PASS"
        and normalized(field(report, "Fun", "PENDING")) == "PASS"
        and normalized(field(report, "Approving user", "PENDING")) not in PENDING_VALUES
        and normalized(field(report, "Decision evidence", "PENDING")) not in PENDING_VALUES
    )


def bootstrap_approval_valid(root: Path) -> bool:
    bootstrap = read_text(root / "docs/sdd/bootstrap-playtest.md")
    return (
        normalized(field(bootstrap, "Lifecycle Status", "AWAITING FIRST PLAYTEST")) == "PASS"
        and normalized(field(bootstrap, "Human Approval", "PENDING")) == "PASS"
        and normalized(field(bootstrap, "Game Feel aprovado", "PENDING")) == "PASS"
        and normalized(field(bootstrap, "Diversão aprovada", "PENDING")) == "PASS"
        and normalized(field(bootstrap, "Estrutura SDD aprovada", "PENDING")) == "PASS"
        and normalized(field(bootstrap, "Evidência da decisão explícita do usuário", "PENDING")) not in PENDING_VALUES
        and normalized(field(bootstrap, "First Playable Feature", "PENDING")) not in PENDING_VALUES
        and normalized(field(bootstrap, "Fingerprint avaliada", "PENDING")) not in PENDING_VALUES
    )


def direct_change_gate(root: Path, change_dir: Path) -> dict[str, Any]:
    change_dir = change_dir.resolve()
    try:
        change_dir.relative_to((root / "docs/sdd/direct-changes").resolve())
    except ValueError:
        return {
            "change_dir": str(change_dir),
            "mode": "check-main",
            "status": "INVALID_CHANGE_PATH",
            "next_role": None,
            "eligible": False,
            "reasons": ["Direct change evidence must live under docs/sdd/direct-changes/."],
            "blockers": ["Use the registered direct-change evidence directory."],
        }

    current_fingerprint = source_fingerprint(root)
    summary_path = change_dir / "change.md"
    summary = read_text(summary_path)
    qa = read_text(change_dir / "qa-report.md")
    human = read_text(change_dir / "human-playtest.md")
    blockers: list[str] = []
    next_role = "MAIN"
    status = "MAIN_ELIGIBLE"
    summary_ready = (
        summary_path.is_file()
        and normalized(field(summary, "Lifecycle Status", "DRAFT")) == "READY"
        and normalized(field(summary, "Change Type", "PENDING")) not in PENDING_VALUES
        and normalized(field(summary, "Summary", "PENDING")) not in PENDING_VALUES
        and normalized(field(summary, "Reason", "PENDING")) not in PENDING_VALUES
    )
    if not summary_ready:
        blockers.append("Record the small change and its reason in change.md.")
        return {
            "change_dir": str(change_dir),
            "mode": "check-main",
            "status": "CHANGE_SUMMARY",
            "next_role": "ORCHESTRATOR",
            "source_fingerprint": current_fingerprint,
            "eligible": False,
            "reasons": blockers,
            "blockers": blockers,
        }
    if not qa:
        blockers = ["QA must create qa-report.md with technical evidence for this direct change."]
        return {
            "change_dir": str(change_dir), "mode": "check-main", "status": "TECHNICAL_QA",
            "next_role": "QA", "source_fingerprint": current_fingerprint, "eligible": False,
            "reasons": blockers, "blockers": blockers,
        }
    qa_result = normalized(field(qa, "Result", "PENDING"))
    if qa_result in {"FAIL", "FAILED"}:
        blockers = ["Fix the QA failures within the direct change scope, then return to QA."]
        return {
            "change_dir": str(change_dir), "mode": "check-main", "status": "TECHNICAL_REMEDIATION",
            "next_role": "DEVELOPER", "source_fingerprint": current_fingerprint, "eligible": False,
            "reasons": blockers, "blockers": blockers,
        }
    if qa_result != "PASS" or field(qa, "Tested Fingerprint", "") != current_fingerprint:
        blockers = ["QA evidence must PASS and match the current playable source fingerprint."]
        return {
            "change_dir": str(change_dir), "mode": "check-main", "status": "TECHNICAL_QA",
            "next_role": "QA", "source_fingerprint": current_fingerprint, "eligible": False,
            "reasons": blockers, "blockers": blockers,
        }
    if not human:
        blockers = ["Record an explicit human playtest approval in human-playtest.md."]
        return {
            "change_dir": str(change_dir), "mode": "check-main", "status": "HUMAN_PLAYTEST",
            "next_role": "USER", "source_fingerprint": current_fingerprint, "eligible": False,
            "reasons": blockers, "blockers": blockers,
        }
    if normalized(field(human, "Result", "PENDING")) in {"FAIL", "FAILED", "REJECTED"}:
        blockers = ["Review the user's playtest feedback and agree any required follow-up before retesting."]
        return {
            "change_dir": str(change_dir), "mode": "check-main", "status": "PLAYTEST_FEEDBACK",
            "next_role": "AGENT_GAME_DESIGNER", "source_fingerprint": current_fingerprint, "eligible": False,
            "reasons": blockers, "blockers": blockers,
        }
    if not valid_human_approval(human) or field(human, "Tested Fingerprint", "") != current_fingerprint:
        blockers = ["A current explicit user PASS for Game Feel and fun is required."]
        return {
            "change_dir": str(change_dir), "mode": "check-main", "status": "HUMAN_PLAYTEST",
            "next_role": "USER", "source_fingerprint": current_fingerprint, "eligible": False,
            "reasons": blockers, "blockers": blockers,
        }
    if not bootstrap_approval_valid(root):
        blockers.append("The first playable human playtest has not explicitly approved the SDD bootstrap.")
        next_role, status = "USER", "BOOTSTRAP_PLAYTEST"
    return {
        "change_dir": str(change_dir),
        "mode": "check-main",
        "status": status,
        "next_role": next_role,
        "source_fingerprint": current_fingerprint,
        "eligible": not blockers,
        "reasons": blockers or ["The direct-change QA, human playtest and bootstrap gates pass."],
        "blockers": blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--route", action="store_true", help="Show the next responsible role (default).")
    mode.add_argument("--check-main", action="store_true", help="Return success only when the local integration gates pass.")
    parser.add_argument("--feature-dir", help="Feature directory under specs/; otherwise auto-detect a single active feature.")
    parser.add_argument("--direct-change-dir", type=Path, help="Evidence directory under docs/sdd/direct-changes/ for a small change without a feature spec.")
    parser.add_argument("--fingerprint", action="store_true", help="Print the current playable source fingerprint.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = args.root.resolve()

    if args.direct_change_dir and not args.check_main:
        parser.error("--direct-change-dir is only valid with --check-main.")
    if args.feature_dir and args.direct_change_dir:
        parser.error("--feature-dir and --direct-change-dir cannot be used together.")
    if args.fingerprint:
        print(source_fingerprint(root))
        return 0
    if args.check_main and args.direct_change_dir:
        payload = direct_change_gate(root, args.direct_change_dir if args.direct_change_dir.is_absolute() else root / args.direct_change_dir)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Status: {payload['status']}")
            print(f"Next responsible role: {payload.get('next_role', 'N/A')}")
            print(f"Change evidence: {payload['change_dir']}")
            for blocker in payload.get("blockers", []):
                print(f"Blocker: {blocker}")
            print(f"Main integration eligible: {'YES' if payload['eligible'] else 'NO'}")
        return 0 if payload["eligible"] else 1
    feature, candidates = discover_feature(root, args.feature_dir)
    if feature is None and candidates:
        payload = {"status": "AMBIGUOUS", "candidates": candidates, "reasons": ["Pass --feature-dir to select the feature being routed."]}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("More than one feature is active. Select one with --feature-dir:")
            print("\n".join(f"- {candidate}" for candidate in candidates))
        return 2
    if feature is None:
        payload = route(root / "specs", "NEEDS_DISCOVERY", "AGENT_GAME_DESIGNER", "No active spec exists; conduct discovery for the next increment.", source_fingerprint(root))
        if args.check_main:
            payload.update({
                "mode": "check-main",
                "eligible": False,
                "blockers": ["No feature package is available for main integration."],
            })
    else:
        payload = main_gate(root, feature) if args.check_main else feature_route(root, feature)
    payload["mode"] = "check-main" if args.check_main else "route"
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Status: {payload['status']}")
        print(f"Next responsible role: {payload.get('next_role', 'N/A')}")
        if payload.get("feature_dir"):
            print(f"Feature: {payload['feature_dir']}")
        for reason in payload.get("reasons", []):
            print(f"Reason: {reason}")
        for blocker in payload.get("blockers", []):
            print(f"Blocker: {blocker}")
        if args.check_main:
            print(f"Main integration eligible: {'YES' if payload['eligible'] else 'NO'}")
    return 0 if not args.check_main or payload.get("eligible", False) else 1


if __name__ == "__main__":
    sys.exit(main())
