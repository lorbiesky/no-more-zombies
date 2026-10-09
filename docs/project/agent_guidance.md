# Multi-agent execution guidance

- Read `scripts/validate_operational_workflow.py` to determine the current feature state.
- Give each agent only the relevant brief, references, expected output and files it may edit.
- Keep one active writer per artifact and hand off ownership when another role needs to edit it.
- The Game Designer prepares and conducts product discovery. If the agent tool cannot message the user, the orchestrator relays the Game Designer's exact prepared question. Other roles send questions to the Game Designer and do not ask the user directly about product decisions.
- Review each agent's diff against its assigned responsibilities.
- Only the user can approve a feature package or Human Playtest. Record the decision only after the user states it explicitly.
- Use one Godot MCP client at a time; the bridge accepts a single connection.
