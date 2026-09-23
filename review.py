"""Validate and record evidence for curated code-review cases."""

import json
import sys
from pathlib import Path


CASE_KEYS = {"id", "source_url", "source_revision", "license", "description", "kind"}
FINDING_KEYS = {"id", "case_id", "path", "line", "claim", "verification"}


def _read_json(path: Path):
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {path}: {error}") from error


def _inside(root: Path, child: Path) -> bool:
    return child.resolve().is_relative_to(root.resolve())


def load_case(case_dir: Path) -> dict:
    case = _read_json(case_dir / "case.json")
    if not isinstance(case, dict) or set(case) != CASE_KEYS:
        raise ValueError("case.json must contain exactly the case fields")
    if any(not isinstance(case[key], str) or not case[key].strip() for key in CASE_KEYS):
        raise ValueError("case fields must be nonempty strings")
    if case["kind"] not in {"illustrative", "real"}:
        raise ValueError("case kind must be illustrative or real")
    fixture = case_dir / "fixture"
    if not fixture.is_dir() or not _inside(case_dir, fixture):
        raise ValueError("fixture must be a directory inside the case")
    return case


def load_findings(path: Path, case: dict, fixture: Path) -> list[dict]:
    findings = _read_json(path)
    if not isinstance(findings, list):
        raise ValueError("findings must be a JSON array")
    seen = set()
    for finding in findings:
        if not isinstance(finding, dict) or set(finding) != FINDING_KEYS:
            raise ValueError("each finding must contain exactly the finding fields")
        for key in FINDING_KEYS - {"line"}:
            if not isinstance(finding[key], str) or not finding[key].strip():
                raise ValueError(f"finding {key} must be a nonempty string")
        if type(finding["line"]) is not int or finding["line"] < 1:
            raise ValueError("finding line must be a positive integer")
        if finding["case_id"] != case["id"]:
            raise ValueError("finding case_id does not match case")
        if finding["id"] in seen:
            raise ValueError("duplicate finding id")
        seen.add(finding["id"])
        relative = Path(finding["path"])
        source = fixture / relative
        if relative.is_absolute() or not _inside(fixture, source) or not source.is_file():
            raise ValueError("finding path is not a fixture file")
        try:
            lines = source.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as error:
            raise ValueError(f"cannot read finding source: {error}") from error
        if finding["line"] > len(lines):
            raise ValueError("finding line does not exist")
    return findings


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 3 or args[0] != "validate":
        print("usage: review.py validate CASE_DIR FINDINGS_JSON", file=sys.stderr)
        return 2
    case_dir = Path(args[1])
    try:
        case = load_case(case_dir)
        load_findings(Path(args[2]), case, case_dir / "fixture")
    except ValueError as error:
        print(f"invalid evidence: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
