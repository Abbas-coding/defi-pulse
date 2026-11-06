# Decision Register

## Status Definitions

**Baseline** means retained from the context, not newly verified. **Open** means a choice or fact still needs evidence. **Proposed** means a departure has been discussed but not approved. The user requested consultation before changes to the context are adopted.

| ID | Decision | Status | Resolution/evidence needed |
|---|---|---|---|
| D01 | Ethereum Mainnet, Uniswap v3, TOKEN/WETH | Baseline | Verify source and WETH identity during discovery |
| D02 | One canonical pool per token | Baseline; algorithm open | Verify earliest-pool lookup beyond candidate date range |
| D03 | Full available 1h/6h/24h histories | Baseline | Quantify safe hourly coverage; determine need for events |
| D04 | Common hour-24→day-8, ≥80% USD-TVL decline | Baseline | Freeze exact endpoint reconstruction and definition version |
| D05 | Verified zero day-8 TVL | Open; user decision required | Formula implies positive label; context tests reject zero outcome. Proposed distinction: valid measured zero versus invalid/missing zero |
| D06 | The Graph as primary source | Baseline preference | Live endpoint, schema, historical access, free terms, actual account availability |
| D07 | 20–30-pool pilot before scale-up | Baseline | Review measured completeness, costs, and selection losses |
| D08 | 300–1,000-pool target | Conditional baseline | Usable class counts and temporal coverage, not nominal pool count |
| D09 | Sampling dates, eligibility thresholds, staleness | Open | Pilot evidence; document before full extraction |
| D10 | Calibration and risk bands | Conditional baseline | Separate permitted validation data and adequate class counts |
| D11 | 48h/72h observation comparison | Proposed, not approved | User approval and choice of common versus shifted target; acknowledge ongoing-outcome information |
| D12 | Instructor approval and actual rubric | Unverified | Team confirmation and course documents before formal build |
| D13 | Final model and SHAP display semantics | Open | Evaluation and compatibility; distinguish estimator score from calibrated output |
| D14 | Python version, lock tool, exact dependencies | Open implementation detail | Environment inspection and compatible reproducible setup |

## Change Procedure

For a departure, record the proposed change, reason, evidence, alternatives, and impact on claims, workload, and comparability. Ask the user before adopting it. If instructor-approved deliverables are affected, establish whether instructor agreement is also needed.

Record approvals with date and scope. Then update affected documentation and version any changed data/experiment contracts. Do not relabel a proposal as approved because implementation would be convenient.

## Known Document Discrepancies

- The original `AGENTS.md` describes the initial README-only scaffold. It remains unchanged under the user's preservation instruction; this documentation index describes the newer planning files.
- The context handoff references `PROJECT_CONTEXT.md`; the actual reference file is `DEFI_PULSE_CODEX_PROJECT_CONTEXT.md`.
- Zero outcome handling is internally inconsistent as described in D05. Neither interpretation has been silently selected.
- The context calls several decisions locked; the user's later instruction permits reconsideration with prior consultation. Retain the baseline until a change is approved.
