# {{PROJECT_NAME}} — Initial Engineering Constitution

This file provides inherited engineering defaults for the project template. The user and Game Designer should review or amend them as the game takes shape. It records no user ratification.

## Principles

### I. Small, playable increments
Prefer the smallest increment that can be experienced and evaluated. Split large features into independent deliveries and avoid speculative scope.

### II. Idiomatic Godot composition
Build systems primarily from composed Nodes and Scenes. Separate deterministic logic from engine integration when useful for testing. Use Resources for reusable data and Autoloads only for genuinely global services or state with explicit dependencies.

### III. Typed, cohesive GDScript
Prefer typed GDScript, cohesive scripts and clear responsibilities. Avoid tight scene coupling and implicit global dependencies.

### IV. Approved artifacts define scope
The approved spec, plan and tasks govern feature behavior and scope. Do not silently change approved requirements or material technical decisions. Return such changes for review before continuing.

### V. Clear role ownership and escalation
Each agent inspects relevant context, stays within its role and makes unresolved decisions visible. AGENT_GAME_DESIGNER is the sole interface for product discovery and decisions; specialists route questions and proposals through it.

### VI. Technical evidence and human playtest
Automate deterministic checks where useful, including input, signals and scene or Node lifecycle. QA demonstrates technical stability. The user evaluates Game Feel and fun through an explicit Human Playtest. No agent may substitute for or infer that approval.

## Initial technical defaults

- Engine: Godot 4.7; language: GDScript.
- Scene and gameplay tests use gdUnit4 6.2.1.
- Serialize Godot MCP calls because its bridge accepts one connected client.
- Create feature specifications on demand under `specs/`.
- Keep the GDD modular and record only discovered decisions.

## Workflow

Follow `docs/sdd/lifecycle.md`. The user approves the spec, plan and tasks before implementation, and approves a current Human Playtest before game changes are eligible for `main`. QA and Human Playtest are independent gates.

## Change history

This is an initial template policy, not a ratified game constitution. Record future amendments with their reason and approval status.
