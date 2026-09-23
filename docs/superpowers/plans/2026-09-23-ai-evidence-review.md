# AI Evidence Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small Python CLI and one agent skill that distinguish AI code-review claims from observed checks and human verdicts, then produce a reproducible evidence report.

**Architecture:** Curated local cases contain a source fixture, `unittest` checks, and provenance. The agent skill emits structured findings; the CLI validates them, runs a fixed check command, writes a report, and aggregates labeled outcomes. No model API is embedded in the CLI.

**Tech Stack:** Python 3.12+ standard library, `unittest`, Markdown, JSON.

**Spec:** `docs/superpowers/specs/2026-09-23-ai-evidence-review-design.md`

## Global Constraints

- Work only in the Orca worktree for the new `ai-evidence-review` repository; do not copy code from existing SK hynix or Control Tower projects.
- No web server, database, authentication, auto-fix, auto-PR, GitHub publishing, or arbitrary shell command input.
- `check` runs the current Python interpreter with fixed `-m unittest discover -s tests -t .` arguments inside a curated fixture; never execute a command supplied by JSON.
- Do not weaken sandboxing. Preserve case inputs and logs after failure. No private code or secrets in submitted artifacts.
- Final essay and single-file PDF target 2026-09-27 17:00 KST. Submission and remote publication remain outside this plan.
- Git status, staging, commit, and push operations are directed to Copilot CLI through Orca; no push is planned.

## File map

- `review.py`: CLI parsing, strict JSON validation, fixed check execution, Markdown reporting, and aggregation. One file keeps this small tool inspectable.
- `tests/test_review.py`: CLI and trust-boundary tests using temporary case directories.
- `cases/demo/`: clearly labeled illustrative fixture for an end-to-end smoke test; excluded from outcome metrics by its `kind` field.
- `.agents/skills/ai-evidence-review/SKILL.md`: thin instructions to produce the finding JSON, run the CLI, and abstain when evidence is lacking.
- `README.md`: exact commands, schema, safety boundary, and interpretation of results.
- `evidence/`: only verified, attributable case records and generated reports admitted after the case-provenance gate.

## Review Focus

1. A finding path such as `../secret` or a symlink escapes the fixture: validation rejects it before reading.
2. A case JSON includes a shell command or unknown key: strict parsing rejects it; checks remain fixed.
3. A check hangs: timeout returns a recorded failure without deleting inputs or weakening isolation.
4. A passing check accompanies a false AI claim: report keeps check outcome and human verdict separate.
5. No valid finding is produced: evaluation shows a zero denominator as “not measured,” never 100% precision.

---

### Task 1: Strict case and finding validation

**Files:** Create `review.py`, `tests/test_review.py`.

**Interfaces:** Produce `load_case(case_dir: Path) -> dict`, `load_findings(path: Path, case: dict, fixture: Path) -> list[dict]`, and `main(argv: list[str] | None = None) -> int` with a `validate <case_dir> <findings_json>` subcommand. A case JSON has exactly `id`, `source_url`, `source_revision`, `license`, `description`, and `kind` (`illustrative` or `real`). Finding objects have exactly `id`, `case_id`, `path`, `line`, `claim`, and `verification`.

- [ ] **Step 1: Write failing tests.** Use `tempfile.TemporaryDirectory` to create `case.json`, `fixture/source.py`, and `findings.json`. Assert a valid finding returns `0`; a `../secret`, a symlink outside fixture, missing source line, wrong case ID, extra JSON key, or malformed JSON returns nonzero.

```python
def test_rejects_escape(self):
    finding = {"id":"f1","case_id":"demo","path":"../secret","line":1,"claim":"x","verification":"inspect"}
    self.write_findings([finding])
    self.assertNotEqual(main(["validate", str(self.case_dir), str(self.findings)]), 0)
```

- [ ] **Step 2: Run** `python3 -m unittest tests.test_review -v`; expect failure because `review` does not exist.
- [ ] **Step 3: Implement** JSON decoding with `json.load`, exact-key checks, string/integer type checks, `Path.resolve().is_relative_to(fixture.resolve())`, file check, and 1-based line bounds. Catch validation errors in `main` and return `2` with a concise stderr message.

```python
def _inside(root: Path, child: Path) -> bool:
    return child.resolve().is_relative_to(root.resolve())
```

- [ ] **Step 4: Run** `python3 -m unittest tests.test_review -v`; expect all validation tests to pass.
- [ ] **Step 5: Ask Copilot CLI** to run `git diff --check`, stage only Task 1 files, and commit `feat: validate review evidence inputs`.

### Task 2: Fixed, bounded check runner

**Files:** Modify `review.py`; extend `tests/test_review.py`.

**Interfaces:** Produce `run_check(case_dir: Path, timeout_seconds: int = 30) -> dict` returning `case_id`, `argv`, `exit_code`, `timed_out`, `duration_ms`, `stdout`, and `stderr`. `check <case_dir>` writes fixed `check.json` under that case directory. The argv is always `[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."]`.

- [ ] **Step 1: Write failing tests.** Create one passing fixture test, one failing fixture test, and one sleeping fixture test with a one-second timeout. Assert exit code and timeout are recorded; add a case JSON `command` key and assert it is rejected by Task 1 validation.

```python
def test_failed_check_is_recorded(self):
    result = run_check(self.case_dir)
    self.assertEqual(result["exit_code"], 1)
    self.assertFalse(result["timed_out"])
```

- [ ] **Step 2: Run** `python3 -m unittest tests.test_review -v`; expect the new tests to fail because `run_check` is missing.
- [ ] **Step 3: Implement** `subprocess.run(..., cwd=fixture, shell=False, timeout=timeout_seconds, capture_output=True, text=True)`. Refuse missing `fixture/tests`; truncate each captured stream to 16 KiB; use `time.monotonic` for duration. On `TimeoutExpired`, record `timed_out: true` and a nonzero outcome.
- [ ] **Step 4: Run** the full `unittest` command; after Task 4 adds the demo, also run `python3 review.py check cases/demo`. Until then, run the temporary-fixture test only.
- [ ] **Step 5: Ask Copilot CLI** to diff-check and commit only Task 2 changes as `feat: run bounded case checks`.

### Task 3: Evidence report and truthful aggregation

**Files:** Modify `review.py`; extend `tests/test_review.py`.

**Interfaces:** Produce `render_report(case: dict, findings: list[dict], check: dict, verdicts: dict) -> str` and `aggregate(records: list[dict]) -> dict`. Verdict values are exactly `valid`, `invalid`, or `unresolved`. `report <case_dir> <findings_json> <verdicts_json>` reads fixed `check.json` and writes fixed `report.md` under the case directory. `evaluate <case_dir>...` prints JSON counts and precision only when `valid + invalid > 0`; illustrative cases are excluded.

- [ ] **Step 1: Write failing tests.** Assert report includes source attribution, claim, observed check outcome, and verdict in separate fields. Assert a passing check plus invalid verdict stays invalid. Assert zero adjudicated findings yields `precision: null` and `sample_size: 0`.

```python
def test_zero_denominator_is_unknown(self):
    self.assertIsNone(aggregate([{"verdicts":{"f1":"unresolved"}}])["precision"])
```

- [ ] **Step 2: Run** `python3 -m unittest tests.test_review -v`; expect new tests to fail.
- [ ] **Step 3: Implement** Markdown escaping for user-provided text, explicit `Observed check` and `Human verdict` headings, and `precision = valid / (valid + invalid)` only for a nonzero denominator. Never infer validity from test exit code.
- [ ] **Step 4: Run** the full test suite; expect all tests to pass.
- [ ] **Step 5: Ask Copilot CLI** to diff-check and commit only Task 3 files as `feat: report evidence with human verdicts`.

### Task 4: Thin skill, illustrative demo, and operator documentation

**Files:** Create `.agents/skills/ai-evidence-review/SKILL.md`, `cases/demo/case.json`, `cases/demo/fixture/source.py`, `cases/demo/fixture/tests/test_source.py`, `README.md`; extend `tests/test_review.py` with a clean-checkout smoke test.

**Interfaces:** The skill tells an agent to inspect one curated case, write finding JSON matching Task 1, call `validate`, `check`, `report`, and avoid unsupported claims. The demo is marked illustrative in every output and never counted as a measured real-world result.

- [ ] **Step 1: Write a failing smoke test** that invokes `main(["validate", ...])`, `main(["check", ...])`, and `main(["report", ...])` on `cases/demo`, then asserts the report exists and labels the case `illustrative`.
- [ ] **Step 2: Run** the smoke test; expect failure because demo assets and skill are absent.
- [ ] **Step 3: Add** the minimal demo fixture, README commands, and skill instructions. Keep the skill under one page; it delegates all validation to the CLI and tells the agent to abstain if no finding is supported.
- [ ] **Step 4: Run** `python3 -m unittest discover -s tests -v`, the README example, and `git diff --check`; expect success. Inspect the generated Markdown manually for source/check/verdict separation.
- [ ] **Step 5: Ask Copilot CLI** to stage only Task 4 files and commit `docs: add review skill and reproducible demo`.

### Task 5: Real-case feasibility and submission evidence gate

**Files:** Add only verified case files under `evidence/`; create `evidence/README.md`; later create essay and PDF source only if at least one attributable real case passes the gate.

**Interfaces:** A case record must name source URL, exact revision, permission to share, reproduction command, observed result, and human adjudication. Its report links to the corresponding CLI output and states sample count and limits.

- [ ] **Step 1: Identify** real, legally shareable candidate cases. Reject cases with uncertain provenance or private code before copying any content.
- [ ] **Step 2: Reproduce** each selected case with the fixed check route or document why it cannot be admitted. Do not include unreproducible cases in quantitative claims.
- [ ] **Step 3: Run** the AI skill on admitted cases, then the CLI validation/check/report flow. Have a fresh read-only reviewer adjudicate findings independently of the author.
- [ ] **Step 4: Count** only adjudicated cases; state denominators and unresolved results. If no real case is admissible by 2026-09-24, stop feature expansion and report the evidence gap instead of manufacturing a result.
- [ ] **Step 5: Produce** essay and one PDF only from verified claims; check character count, file type/size, links, and visible rendering before the 2026-09-27 17:00 KST freeze. Do not submit or publish automatically.

## Final verification

Run `python3 -m unittest discover -s tests -v` and `git diff --check` from the exact final revision. A fresh read-only reviewer inspects the full diff and independently checks every portfolio number against the case records. Preserve the worktree, reports, and all failed runs for user review.
