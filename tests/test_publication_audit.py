"""The publication guard is a safety control, so it needs tests of its own.

A guard that has never been shown to fire is decoration. These tests prove that
the audit rejects the three mistakes that would actually leak something, and
that it stays quiet on an ordinary file.

The fixtures are assembled at runtime instead of being written as literals. If
this file contained a realistic-looking key or local path, the audit would flag
its own test suite, and the usual reaction to that is to add an exemption for
the tests folder. An exemption is worse than the inconvenience: it creates one
tracked location where a real secret would never be reported.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_publication import audit

BACKSLASH = chr(92)
FAKE_KEY = "{" + '"api' + '_key": ' + '"abc123def456ghi"' + "}"
FAKE_WINDOWS_PATH = "C:" + BACKSLASH + "Users" + BACKSLASH + "someone" + BACKSLASH + "projects"


class PublicationAuditTests(unittest.TestCase):
    def test_ordinary_file_produces_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "notes.md"
            path.write_text("Synthetic episode data only.\n", encoding="utf-8")
            self.assertEqual(audit([path], root), [])

    def test_secret_written_as_json_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "settings.json"
            path.write_text(FAKE_KEY, encoding="utf-8")
            findings = audit([path], root)
            self.assertTrue(any("credential assignment" in item for item in findings))

    def test_local_windows_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "README.md"
            path.write_text(f"Run it from {FAKE_WINDOWS_PATH}", encoding="utf-8")
            findings = audit([path], root)
            self.assertTrue(any("Windows user path" in item for item in findings))

    def test_forbidden_filename_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / ".env"
            path.write_text("EMPTY\n", encoding="utf-8")
            findings = audit([path], root)
            self.assertTrue(any("forbidden filename" in item for item in findings))

    def test_the_audit_does_not_exempt_its_own_test_suite(self) -> None:
        """The guard must still inspect this file like any other tracked file."""
        here = Path(__file__).resolve()
        self.assertEqual(audit([here], here.parent), [])


if __name__ == "__main__":
    unittest.main()
