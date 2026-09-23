# AI Evidence Review

A small, standard-library CLI for separating an AI code-review claim from an observed test result and a human verdict. Python 3.12+ is required. The CLI does not call a model API.

## Run the illustrative case

From this repository root:

```sh
python3 review.py validate cases/demo cases/demo/findings.json
python3 review.py check cases/demo
python3 review.py report cases/demo cases/demo/findings.json cases/demo/verdicts.json
python3 review.py evaluate cases/demo
python3 -m unittest discover -s tests -v
```

`check` writes `cases/demo/check.json`; `report` writes `cases/demo/report.md`. The example is deliberately **illustrative**. Its existing zero-rate test passes while the claim about positive rates remains unadjudicated. The `unresolved` verdict is a placeholder, not a human finding. `evaluate` excludes illustrative cases, so this example supplies no accuracy measurement.

## Run the public-source candidate

The [urllib3 candidate](cases/urllib3-fingerprint-5211/case.json) is not an admitted portfolio result. Its isolated pre-fix function excerpt uses local stand-ins; the expected `check` exit code is **1** because the test exposes `binascii.Error`. Inspect the fixture before running it.

```sh
python3 review.py validate cases/urllib3-fingerprint-5211 cases/urllib3-fingerprint-5211/findings.json
python3 review.py check cases/urllib3-fingerprint-5211
python3 review.py report cases/urllib3-fingerprint-5211 cases/urllib3-fingerprint-5211/findings.json cases/urllib3-fingerprint-5211/verdicts.json
python3 review.py evaluate cases/urllib3-fingerprint-5211
```

Run `check` again on each machine, after changing Python interpreters, or after editing case metadata: stored results identify the interpreter and hash both `case.json` and the fixture. `check.json` and `report.md` are local, ignored outputs and may contain absolute paths; inspect them before sharing. This case has one `unresolved` finding, so the adjudicated sample size is zero and precision is `null`. See [the evidence gate](evidence/README.md) before using it in a submission.

## Input contract

Each case has `case.json` with exactly `id`, `source_url`, `source_revision`, `license`, `description`, and `kind` (`illustrative` or `real`), plus `fixture/` with `tests/`. `findings.json` is an array of objects with exactly `id`, `case_id`, `path`, `line`, `claim`, and `verification`. Lines are 1-based and paths must resolve inside `fixture/`. `verdicts.json` maps each finding ID to exactly one human label: `valid`, `invalid`, or `unresolved`. The CLI rejects unknown fields and mismatched IDs.

`check` runs only the current Python interpreter's fixed `unittest discover` command with a 30-second timeout and records the actual exit code, duration, truncated output, and digests of `case.json` and the fixture. `report` and `evaluate` reject that result if either has changed; rerun `check` after editing a case. Fixture symlinks and symlinked output files are rejected. It never executes a command supplied by JSON. **Python tests are executable code:** only run `check` on local fixtures whose contents you have vetted. Do not clone and run an arbitrary repository. A green test is not proof that an AI claim is true, and a red test does not automatically establish causation.

`evaluate` reads each case's `findings.json`, `verdicts.json`, and `check.json`. It counts real cases only; `sample_size` is the number of valid-plus-invalid findings, excluding unresolved findings. Precision is `null` when that denominator is zero. Small case counts are demonstrations, not general accuracy claims.

No auto-fix, server, database, PR creation, or publication is included. Do not include private code or secrets in portfolio evidence. Publication and submission require a separate owner decision.

## Submission drafts

The [AI experience answer](portfolio/ai-experience.txt) and [two-page portfolio PDF](output/pdf/AI-Evidence-Review-Portfolio.pdf) are review drafts, not submitted results. The [PDF source](portfolio/ai-evidence-review.typ) can be rebuilt with `typst compile portfolio/ai-evidence-review.typ output/pdf/AI-Evidence-Review-Portfolio.pdf`. The answer is 904 characters and the PDF is 72,101 bytes, within the [official application](https://skhynix-hackathon.com/ai-2026/apply) limits of 50–2,000 characters and one optional file up to 50 MB. The public candidate remains unresolved, so the draft makes no accuracy claim. Review the first-person answer and all evidence before using either artifact in an application.
