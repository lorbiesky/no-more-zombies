---
name: sdd-orchestrate
description: Orchestrate the project's Spec-Driven Development lifecycle for new Godot gameplay features and substantial systems, including Game Designer discovery, conditional UI/UX delegation, QA, user approvals and the human playtest gate.
---

# SDD Orchestrator

Use this skill when the user asks for a new gameplay feature or a substantial
game system, or invokes $sdd-orchestrate explicitly. Small fixes, maintenance
and documentation may use the direct workflow, but still require the human
gate before integration into main.

## Source of truth

- Follow AGENTS.md, docs/sdd/lifecycle.md and the ratified constitution.
- Use the installed upstream Spec Kit v1.1.0 skills and scripts. Do not edit
  their command implementations to encode project roles.
- Feature artifacts live in specs/<feature>/. Always set
  SPECIFY_FEATURE_DIRECTORY explicitly for all Spec Kit steps in that feature.
- Route state comes from feature artifacts. Run
  python3 scripts/validate_operational_workflow.py --route --feature-dir specs/<feature>
  before dispatching the next role.
- Do not create a sample or retrospective gameplay specification for workflow
  setup. Never invent a mechanic or fill an unknown GDD section.

## Roles and handoffs

1. AGENT_GAME_DESIGNER is the only role that asks the user discovery questions
   or makes product-scope decisions. It owns the Epic, full GDD index and game
   modules, functional behavior and final spec.md.
   If the agent tool cannot message the user, the orchestrator relays the
   exact question prepared by the Game Designer without adding its own product
   questions or changing the decision.
2. When UI Impact is YES, AGENT_GAME_DESIGNER sends the SUB_AGENT_UI_UX_DESIGNER
   a concise brief, relevant GDD references, exact section/file ownership and
   expected deliverable. UI/UX returns state rules, navigation, focus, button
   behavior, input capture, displayed data and feedback details for only the
   assigned parts. It never asks the user directly or changes game mechanics.
3. For UI Impact NO, the Game Designer records a concrete reason and marks
   UI/UX not required. Do not dispatch UX with no interface work.
4. TECH_LEAD owns technical research, plan.md, tasks.md and analysis findings.
   It does not redefine requirements.
5. The user must explicitly approve the same package revision of spec, plan
   and tasks before DEVELOPER begins. Record the approval and its evidence in
   approval.md. Scope or material technical changes increment the revision
   and invalidate that approval.
6. DEVELOPER implements approved work and records implementation-report.md.
   Route technical failures back to DEVELOPER only while they remain within
   approved scope; otherwise return the decision to the Game Designer/user.
7. QA owns test creation, execution and qa-report.md. It can write tests/,
   test-only fixtures and its assigned QA report. It cannot edit production
   scenes, scripts, assets, project.godot, GDD or functional specifications.
   Review changed paths at handoff.
8. Only after QA PASS, present the playable build, controls and scenarios to
   the user. Record the user's own Game Feel, fun and overall decision in
   human-playtest.md. Never infer or prefill user PASS.
9. Run $speckit-converge and record convergence.md. Newly identified tasks
   reopen implementation and QA. If playable source changes, both QA and
   human-playtest fingerprints must match the new build.

## Human gate and bootstrap

- Obtain the current playable source fingerprint with
  python3 scripts/validate_operational_workflow.py --fingerprint.
- The QA report and human-playtest report must identify that same fingerprint.
- Only the user can approve Game Feel and fun. A documentation-only change
  does not stale the playable fingerprint; project.godot, scenes/, scripts/
  or assets/ changes do.
- The initial SDD installation remains pending outside main until the first
  playable feature passes QA and Playtest Humano. The user's first playtest
  can approve the bootstrap too, only if the user explicitly names both
  approvals. Then record that decision in docs/sdd/bootstrap-playtest.md.
- Before considering integration, run
  python3 scripts/validate_operational_workflow.py --check-main --feature-dir specs/<feature>.
  A nonzero result means the feature is not eligible. Never commit, merge or
  claim remote branch protection as part of this check.
- For small fixes, maintenance or documentation without a feature spec, record
  change.md, qa-report.md and human-playtest.md under
  docs/sdd/direct-changes/<id>/, then run
  python3 scripts/validate_operational_workflow.py --check-main --direct-change-dir docs/sdd/direct-changes/<id>.
  This local gate still requires current QA and explicit user playtest approval.

## Delegation constraints

Keep no more than three specialists active under the root orchestrator. Pass
each role only the minimum relevant context and disjoint file ownership. Never
have agents edit the same document at the same time. Serialize Godot MCP
calls: its bridge supports one connected client at a time.

Some delegation tools cannot select Codex custom profile names. In that case,
put the full applicable role restrictions from .codex/agents/<ROLE>.toml into
the task prompt, and state that the native profile could not be selected. Do
not claim a configured profile ran when only inline instructions were used.
