# Evidence for a direct change

Use this for a small fix, maintenance or documentation that does not need a feature spec. Do not write a retrospective spec. Save as `change.md` under `docs/sdd/direct-changes/<id>/` and create the technical QA and Human Playtest records alongside it:

- `change.md`: type, summary, reason, changed files and whether playable content changed.
- `qa-report.md`: technical result and tested fingerprint. For documentation-only changes, describe the review and mark gameplay scenarios N/A.
- `human-playtest.md`: evaluated fingerprint, Game Feel and fun feedback, explicit user decision and its evidence.

QA owns the technical report. The user alone provides Human Playtest approval. The validator requires both reports to match the current fingerprint and the initial game bootstrap to be approved.

After preparing the records, validate with:

    python3 scripts/validate_operational_workflow.py --check-main --direct-change-dir docs/sdd/direct-changes/<id>

## change.md fields

- **Lifecycle Status**: READY
- **Change Type**: [BUG FIX / MAINTENANCE / DOCUMENTATION]
- **Summary**: [What changed]
- **Reason**: [Why it was needed]
- **Files Changed**: [Paths]
- **Playable Source Changed**: [YES / NO]
