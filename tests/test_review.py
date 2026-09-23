import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from review import aggregate, main, render_report, run_check


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case_dir = self.root / "demo"
        self.fixture = self.case_dir / "fixture"
        self.fixture.mkdir(parents=True)
        (self.fixture / "source.py").write_text("value = 1\nprint(value)\n", encoding="utf-8")
        self.case = {
            "id": "demo",
            "source_url": "https://example.org/source",
            "source_revision": "abc123",
            "license": "MIT",
            "description": "test fixture",
            "kind": "illustrative",
        }
        self.finding = {
            "id": "f1",
            "case_id": "demo",
            "path": "source.py",
            "line": 2,
            "claim": "value is printed",
            "verification": "inspect line 2",
        }
        self.findings = self.case_dir / "findings.json"
        self.write_case()
        self.write_findings()

    def write_case(self):
        (self.case_dir / "case.json").write_text(json.dumps(self.case), encoding="utf-8")

    def write_findings(self, findings=None):
        self.findings.write_text(json.dumps([findings or self.finding]), encoding="utf-8")

    def validate(self):
        return main(["validate", str(self.case_dir), str(self.findings)])

    def write_check_test(self, body):
        tests = self.fixture / "tests"
        tests.mkdir(exist_ok=True)
        (tests / "__init__.py").write_text("", encoding="utf-8")
        (tests / "test_source.py").write_text(body, encoding="utf-8")

    def test_valid_finding_is_accepted(self):
        self.assertEqual(self.validate(), 0)

    def test_parent_escape_is_rejected(self):
        self.finding["path"] = "../secret"
        self.write_findings()
        self.assertNotEqual(self.validate(), 0)

    def test_symlink_escape_is_rejected(self):
        outside = self.root / "outside.py"
        outside.write_text("secret = 1\n", encoding="utf-8")
        (self.fixture / "link.py").symlink_to(outside)
        self.finding["path"] = "link.py"
        self.finding["line"] = 1
        self.write_findings()
        self.assertNotEqual(self.validate(), 0)

    def test_missing_line_is_rejected(self):
        self.finding["line"] = 3
        self.write_findings()
        self.assertNotEqual(self.validate(), 0)

    def test_wrong_case_id_is_rejected(self):
        self.finding["case_id"] = "other"
        self.write_findings()
        self.assertNotEqual(self.validate(), 0)

    def test_unknown_case_key_is_rejected(self):
        self.case["command"] = "echo unsafe"
        self.write_case()
        self.assertNotEqual(self.validate(), 0)

    def test_unknown_finding_key_is_rejected(self):
        self.finding["extra"] = "x"
        self.write_findings()
        self.assertNotEqual(self.validate(), 0)

    def test_malformed_json_is_rejected(self):
        self.findings.write_text("[broken", encoding="utf-8")
        self.assertNotEqual(self.validate(), 0)

    def test_boolean_line_is_rejected(self):
        self.finding["line"] = True
        self.write_findings()
        self.assertNotEqual(self.validate(), 0)

    def test_passing_check_uses_fixed_command_and_writes_result(self):
        self.write_check_test("import unittest\nclass Check(unittest.TestCase):\n    def test_ok(self): self.assertTrue(True)\n")
        self.assertEqual(main(["check", str(self.case_dir)]), 0)
        result = json.loads((self.case_dir / "check.json").read_text(encoding="utf-8"))
        self.assertEqual(result["argv"], [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."])
        self.assertEqual(result["exit_code"], 0)
        self.assertFalse(result["timed_out"])

    def test_failed_check_is_recorded(self):
        self.write_check_test("import unittest\nclass Check(unittest.TestCase):\n    def test_bad(self): self.assertTrue(False)\n")
        result = run_check(self.case_dir)
        self.assertEqual(result["exit_code"], 1)
        self.assertFalse(result["timed_out"])
        self.assertIn("FAILED", result["stderr"])

    def test_hanging_check_times_out(self):
        self.write_check_test("import time\nimport unittest\nclass Check(unittest.TestCase):\n    def test_slow(self): time.sleep(5)\n")
        result = run_check(self.case_dir, timeout_seconds=1)
        self.assertTrue(result["timed_out"])
        self.assertNotEqual(result["exit_code"], 0)

    def test_check_refuses_missing_tests(self):
        with self.assertRaises(ValueError):
            run_check(self.case_dir)

    def test_report_separates_claim_check_and_human_verdict(self):
        check = {"case_id": "demo", "argv": [sys.executable], "exit_code": 0,
                 "timed_out": False, "duration_ms": 10, "stdout": "OK", "stderr": ""}
        report = render_report(self.case, [self.finding], check, {"f1": "invalid"})
        self.assertIn("https://example.org/source", report)
        self.assertIn("source.py:2", report)
        self.assertIn("## AI claim", report)
        self.assertIn("## Observed check", report)
        self.assertIn("## Human verdict", report)
        self.assertIn("invalid", report)
        self.assertIn("exit code: 0", report)
        self.assertIn("illustrative", report)

    def test_zero_denominator_is_unknown(self):
        summary = aggregate([{"kind": "real", "verdicts": {"f1": "unresolved"},
                              "check": {"exit_code": 0}}])
        self.assertIsNone(summary["precision"])
        self.assertEqual(summary["sample_size"], 0)
        self.assertEqual(summary["unresolved"], 1)

    def test_illustrative_finding_is_not_counted(self):
        summary = aggregate([
            {"kind": "illustrative", "verdicts": {"f1": "valid"}, "check": {"exit_code": 0}},
            {"kind": "real", "verdicts": {"f2": "invalid"}, "check": {"exit_code": 0}},
        ])
        self.assertEqual(summary["valid"], 0)
        self.assertEqual(summary["invalid"], 1)
        self.assertEqual(summary["sample_size"], 1)
        self.assertEqual(summary["precision"], 0.0)

    def test_report_command_rejects_missing_human_verdict(self):
        check = {"case_id": "demo", "argv": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."], "exit_code": 0,
                 "timed_out": False, "duration_ms": 10, "stdout": "OK", "stderr": ""}
        (self.case_dir / "check.json").write_text(json.dumps(check), encoding="utf-8")
        verdicts = self.case_dir / "verdicts.json"
        verdicts.write_text("{}", encoding="utf-8")
        self.assertNotEqual(main(["report", str(self.case_dir), str(self.findings), str(verdicts)]), 0)

    def test_evaluate_prints_json_summary(self):
        self.case["kind"] = "real"
        self.write_case()
        check = {"case_id": "demo", "argv": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."], "exit_code": 0,
                 "timed_out": False, "duration_ms": 10, "stdout": "OK", "stderr": ""}
        (self.case_dir / "check.json").write_text(json.dumps(check), encoding="utf-8")
        (self.case_dir / "verdicts.json").write_text(json.dumps({"f1": "valid"}), encoding="utf-8")
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["evaluate", str(self.case_dir)]), 0)
        self.assertEqual(json.loads(output.getvalue())["precision"], 1.0)


if __name__ == "__main__":
    unittest.main()
