# Definition of done

A feature is technically complete when:

- spec, plan and tasks match the approved behavior and every task is resolved;
- `implementation-report.md` records changed paths and evidence;
- QA ran applicable gdUnit4 scenarios and recorded results, failures, command, environment and current source fingerprint;
- in-scope failures are fixed or escalated for re-approval;
- converge reports no remaining approved work.

A game increment is eligible for `main` only after the user explicitly approves Game Feel and fun for a Human Playtest matching the current playable fingerprint. For the first playable increment, the user may also approve the SDD bootstrap. Agents cannot provide or infer that approval.

Changes to game scenes, scripts, assets or Godot configuration invalidate QA and playtest evidence when their fingerprint no longer matches. Documentation-only changes do not alter the playable fingerprint.
