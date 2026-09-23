---
name: ai-evidence-review
description: Use when reviewing a curated local code-change case for an evidence-based portfolio or audit.
---

# AI Evidence Review

Use the repository's `review.py` as the source of truth for schemas and checks. This skill supplies the agent's analysis, not a new validator.

1. Read `README.md`, the selected `case.json`, and the local fixture source and tests. Check provenance and inspect executable test code before running it. Do not clone or execute an arbitrary remote repository.
2. Write `findings.json` as the exact array schema in the README. Each claim needs an existing fixture path and 1-based line plus a concrete verification idea. Use `[]` when evidence is insufficient; do not invent a finding to improve a score.
3. Run `python3 review.py validate CASE_DIR FINDINGS_JSON`, then `python3 review.py check CASE_DIR` only for a vetted local fixture. Keep `check.json` and failures intact. A passing check does not establish an individual claim.
4. A human reviewer supplies `verdicts.json`. Do not create or change human labels from model judgment. Until the verdicts exist, stop and report that adjudication is pending. Then run `python3 review.py report CASE_DIR FINDINGS_JSON VERDICTS_JSON` and, for a case set, `python3 review.py evaluate CASE_DIR...`.

In the handoff, separate **AI claim**, **observed check**, and **human verdict**. Reserve `valid` and `invalid` for the human verdict field; describe your own reading as support or uncertainty. Label illustrative examples and exclude them from real-case metrics. State every denominator and do not generalize a small demonstration into model accuracy or industrial impact.
