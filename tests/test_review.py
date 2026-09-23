import json
import tempfile
import unittest
from pathlib import Path

from review import main


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


if __name__ == "__main__":
    unittest.main()
