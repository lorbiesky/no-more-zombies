# Multi-agent SDD lifecycle

## Roles

- The Orchestrator routes work from artifact state, delegates bounded tasks and consolidates evidence.
- AGENT_GAME_DESIGNER is the sole interface for product discovery and decisions. It owns each Epic, modular GDD, functional spec and UI/UX delegation decision.
- SUB_AGENT_UI_UX_DESIGNER reports to the Game Designer and documents only assigned UI/UX behavior and patterns.
- TECH_LEAD prepares architecture, plan and tasks.
- DEVELOPER implements the approved package.
- QA creates and runs technical gameplay tests and records evidence.
- The user approves the package before implementation and the Human Playtest before game changes are eligible for `main`.

## Stages

1. The Game Designer leads discovery, creates an Epic and updates relevant GDD modules.
2. Specify the feature and clarify remaining questions. When UI Impact is YES, incorporate the assigned UX work before completing the spec.
3. TECH_LEAD creates plan and tasks, then runs analyze. Record package revision, analysis and the user's approval evidence in `approval.md`.
4. Implement only after explicit user approval of the matching package.
5. QA creates and runs gdUnit4 tests and reports the source fingerprint. In-scope defects return to DEVELOPER and reopen QA.
6. After QA PASS, present controls and scenarios to the user. Record the user's explicit Human Playtest decision about Game Feel and fun.
7. Run converge. New tasks return to implementation and QA; playable changes also require another Human Playtest.
8. The validator marks a feature eligible for `main` only when its package, tasks, current QA, current Human Playtest and convergence are approved.

Small fixes, maintenance and documentation may proceed without a feature spec. Record the change, QA and Human Playtest separately under `docs/sdd/direct-changes/<id>/`. The local validator still requires current user approval before changes enter `main`.

## Delegation and context

Pass each agent only relevant context, expected output and files it may change. Do not allow simultaneous writers on one artifact. Keep no more than three specialists active. Serialize Godot MCP access because its bridge accepts one client at a time.

If the sub-agent tool cannot select a profile, include the matching `.codex/agents/<ROLE>.toml` instructions in the delegation brief and disclose the limitation.

## Initial game bootstrap gate

Every generated game starts with the SDD bootstrap and Human Playtest approvals pending. Its first playable increment may also approve the SDD structure only when the user explicitly names both approvals. Record that decision in `docs/sdd/bootstrap-playtest.md`.
