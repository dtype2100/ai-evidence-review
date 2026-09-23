# AI Evidence Review — Design

## Intent and boundary

Build a new, independently implemented CLI plus one thin agent skill in the Orca worktree for `ai-evidence-review`. The submission-facing goal is a reproducible example of AI-assisted problem solving, with an essay and one PDF ready for human review by 2026-09-27 17:00 KST. This cannot guarantee selection or replace the two online preliminary rounds. Existing `skhynix`, `skhynix-fab-guardrail`, and Control Tower code are not copied into the product.

## User-visible result

For each curated code-change case, an agent uses the skill to propose findings in a fixed JSON format. The CLI checks that cited locations exist, runs only preapproved local checks, records their actual results, and produces a Markdown evidence card. A human labels each finding as valid, invalid, or unresolved. An aggregate command summarizes the small case set without claiming general performance.

The evidence card distinguishes the agent's claim, source location, observed check output, and human verdict. A passing test is not proof that a claim is correct; a failing test is not automatically attributable to the claim. Unsupported assertions remain visibly unresolved.

## Minimal architecture

- `cases/<id>/case.json`: curated public or user-owned case metadata, source URL and revision, and provenance. Each included fixture has local `tests/` runnable by Python's standard `unittest`; case input cannot specify a command. No secrets or private code are included in a submitted artifact.
- `findings.json`: agent-produced array with case ID, finding ID, file path, line, explanation, and suggested verification. Strict schema; unknown fields or unsafe paths are rejected.
- `review` CLI: `validate` checks the case and finding schema, path containment, source-line existence, and case identity; `check` runs a fixed `python -m unittest discover` command with timeout in the curated local fixture; `report` writes the evidence card; `evaluate` aggregates human labels and check outcomes.
- Agent skill: instructions for analyzing one case, emitting `findings.json`, invoking the CLI, and explicitly abstaining when evidence is insufficient. The skill contains no duplicate business logic.

Use Python 3.12 standard library unless a tested dependency is demonstrably needed. No web server, database, authentication, auto-fix, auto-PR, GitHub publishing, or arbitrary shell command input. The CLI does not invoke an AI API or require an API key; the agent running the skill supplies the AI reasoning.

## Case selection and evaluation

First identify a small set of independently reproducible, legally shareable cases with a known issue or review decision. Public repository cases are preferred; user-owned cases need an explicit disclosure check before inclusion. Do not invent failures. If no credible set can be assembled on 2026-09-24, stop product expansion and report that the proposed portfolio claim is unsupported rather than filling the set with fabricated examples.

Record the denominator for every measure. Report valid findings, invalid findings, unresolved findings, and time to produce an evidence card for the observed cases. Compare against a clearly described no-skill or manual-baseline run only if the same cases and timing method are available. Small-sample results are a demonstration, not a generalized accuracy or industrial-impact claim.

## Safety and failure behavior

Only run checks from curated local fixtures; never clone and execute an arbitrary remote repository from user input. Use the running Python interpreter with fixed `-m unittest discover` arguments, no shell, a fixture-contained cwd, a timeout, and bounded output. Fail closed on missing files or tests. Do not weaken sandboxing to make a check pass. Preserve the original case and result logs after a failure. User edits, existing hooks, and other repositories remain untouched.

## Verification and acceptance

Tests cover malformed JSON, unknown fields, path traversal, mismatched case IDs, nonexistent cited lines, check timeout, check failure, and truthful aggregation. A clean checkout must run the documented example end to end. A separate read-only reviewer checks the actual diff, the case provenance, every number in the report, and the final PDF for unsupported claims. The essay stays within the official 2,000-character limit; the portfolio is one allowed file under 50 MB. Final submission, remote publication, and merging require a separate user decision.

## Milestones

1. 2026-09-24: case provenance and feasibility gate; freeze the minimum case set and expected evidence.
2. 2026-09-25: implement and test the CLI and skill; run the curated cases.
3. 2026-09-26: independent review, error analysis, essay/PDF draft.
4. 2026-09-27 17:00 KST: freeze a verified submission-ready bundle and report residual limits.

After submission, prepare separately for the October online rounds; this project's portfolio result is not equivalent to advancement to the November final.
