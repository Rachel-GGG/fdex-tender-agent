# FDEX Tender Agent contributor instructions

## Scope

This is the owner-controlled repository `iurp/fdex-tender-agent`. It is separate from the FDEX learning system. Read README.md, docs/implementation-status.md and the assigned task before editing.

The baseline supports a bounded DEMO personnel chapter. Preserve the distinction between source facts, proposed actions, supplied human confirmations and simulated approvals. Do not describe the baseline as a complete production bidding system.

## Collaboration

- Link each contributor PR to an Issue. Use a separate branch/worktree for each task.
- A successful bot `/claim` reply establishes primary ownership. Collaborators use `/assist`; unclaimed duplicate work is not automatically a competing task.
- Preserve interfaces unless the task explicitly includes changing them. Record affected modules and a migration plan for interface changes.
- Preserve the source document in docs/requirements-v1.0.md; additions belong in docs/requirements-addendum.md.
- Do not read teacher expected outputs during normal execution or use them as generated results.

## Verification

Run `python -m unittest discover -s tests -v`. Read actual generated JSON and DOCX. Add regression evidence for changed behavior. A structural check is not a visual render or a WorkBuddy runtime test.

## Data and authority

- Only public or synthetic fixtures belong in Git. No real personnel, company certificates, pricing, credentials, databases or run directories.
- Default mode is DEMO. Unsupported modes fail explicitly; never silently substitute DEMO for real inputs.
- Confirmation and release bind specific objects, scope and hashes. A changed input must not inherit unrelated approval.
- Never execute repository secrets or owner SSH credentials while running student code.
- Zephyr/iurp owns product goals and repository authority. The authorized maintainer may review and merge routine student PRs after required checks and current-commit review. Production deployment, real signing/submission and changes outside that scope require separate instructions.
- Changes authored by the maintainer require independent review before a later protected merge; do not mark self-review as independent approval.
