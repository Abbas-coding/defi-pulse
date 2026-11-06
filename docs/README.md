# DeFi Pulse Project Documentation

Status: planning baseline, prepared 2026-11-06. The repository currently contains documentation only. No source access, dataset, model, or performance result has been verified.

These documents develop the [project context](../DEFI_PULSE_CODEX_PROJECT_CONTEXT.md) into an actionable engineering and research plan. The context remains a reference, not an immutable specification. Departures require user approval before adoption; open choices are recorded explicitly.

## Reading Order

1. [Project plan](plan.md): objectives, scope, milestones, and acceptance gates.
2. [Architecture](architecture.md): components, dependencies, and artifact flow.
3. [Data design](data_design.md): sampling, collection, temporal semantics, and table contracts.
4. [Research methodology](methodology.md): labels, features, comparisons, and evaluation.
5. [Implementation](implementation.md): concrete work packages and verification.
6. [Demo design](design.md): historical exploration and prediction experience.
7. [Decisions](decisions.md): baseline commitments, unresolved questions, and proposed changes.
8. [Feasibility checklist](feasibility.md): evidence required before scaling collection.

## Working Rules

- Treat proposed paths and commands as designs until implementation makes them executable.
- Record measured facts separately from assumptions and targets.
- Keep the 1h/6h/24h histories and common outcome as the baseline; later windows remain a proposal.
- Obtain user agreement before adopting departures from the context. Verify instructor approval before formal graded implementation; this documentation does not establish that approval.
- Update the relevant document when an approved decision changes. Keep experiment definitions versioned so old results remain interpretable.
- Preserve the original context and `AGENTS.md` unless separately authorized to edit them.
