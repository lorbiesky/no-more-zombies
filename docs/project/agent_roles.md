# Agent roles

| Role | Responsibility | Assigned writing |
| --- | --- | --- |
| Orchestrator | Routes work, delegates limited scopes and consolidates evidence | `AGENTS.md`, assigned coordination reports |
| AGENT_GAME_DESIGNER | Sole product discovery interface; owns GDD and functional requirements | Epic, game GDD modules, complete feature spec |
| SUB_AGENT_UI_UX_DESIGNER | Reports to Game Designer; defines interface behavior and consistency | Assigned sections in `docs/gdd/ui-ux/` and feature specs |
| TECH_LEAD | Technical research and implementation design | Plan, tasks and technical artifacts |
| DEVELOPER | Implements approved tasks and fixes in-scope failures | Production code and scenes |
| QA | Creates and runs gameplay stability tests; reports evidence | `tests/`, test-only fixtures and assigned QA report |

Specialists route product questions to AGENT_GAME_DESIGNER. QA assesses technical stability, not Game Feel or fun. Only the user can approve a Human Playtest.

Codex profiles are in `.codex/agents/`. If delegation cannot select a profile, include its role instructions in the task brief and disclose that the native profile was not selected. Use at most three active specialists. Serialize Godot MCP calls.
