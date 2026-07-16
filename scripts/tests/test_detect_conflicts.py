"""Unit tests for scripts/detect_conflicts.py."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import detect_conflicts  # noqa: E402


FIXTURES = Path(__file__).parent / "fixtures"
CONFLICT_LEFT = FIXTURES / "conflict-left.md"
CONFLICT_RIGHT = FIXTURES / "conflict-right.md"
NO_CONFLICT = FIXTURES / "no-conflict.md"
CROSS_DOMAIN = FIXTURES / "cross-domain.md"
MALFORMED = FIXTURES / "malformed-frontmatter.md"
DEPRECATED = FIXTURES / "deprecated-doc.md"


class TestThresholdParsing(unittest.TestCase):
    def test_invalid_threshold_non_numeric_raises(self):
        with self.assertRaises(ValueError):
            detect_conflicts.parse_threshold("abc")

    def test_invalid_threshold_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            detect_conflicts.parse_threshold("1.2")

    def test_empty_threshold_uses_default(self):
        self.assertEqual(detect_conflicts.parse_threshold(""), 0.50)

    def test_nan_threshold_raises(self):
        with self.assertRaises(ValueError):
            detect_conflicts.parse_threshold("nan")


class TestDetectorBehavior(unittest.TestCase):
    def test_no_conflict_pair_returns_no_conflicts(self):
        report = detect_conflicts.detect_conflicts(
            changed_files=[NO_CONFLICT],
            docs_root=FIXTURES,
            threshold=0.70,
        )
        self.assertEqual(report["conflicts"], [])
        self.assertEqual(report["errors"], [])

    def test_conflict_pair_detected(self):
        report = detect_conflicts.detect_conflicts(
            changed_files=[CONFLICT_LEFT],
            docs_root=FIXTURES,
            threshold=0.50,
        )
        self.assertEqual(len(report["conflicts"]), 1)
        conflict = report["conflicts"][0]
        self.assertEqual(conflict["domain"], "user-authentication")
        self.assertIn("scripts/tests/fixtures/conflict-left.md", conflict["left_file"])
        self.assertIn("scripts/tests/fixtures/conflict-right.md", conflict["right_file"])
        self.assertIn("summary", conflict)

    def test_cross_domain_is_not_compared(self):
        report = detect_conflicts.detect_conflicts(
            changed_files=[CROSS_DOMAIN],
            docs_root=FIXTURES,
            threshold=0.70,
        )
        self.assertEqual(report["conflicts"], [])

    def test_threshold_boundaries_around_known_fixture(self):
        # Conflict-left vs conflict-right yields Jaccard ~0.57 (4 shared / 7 union
        # meaningful tokens). Boundaries verified around that computed score.
        low = detect_conflicts.detect_conflicts(
            changed_files=[CONFLICT_LEFT], docs_root=FIXTURES, threshold=0.55
        )
        equal = detect_conflicts.detect_conflicts(
            changed_files=[CONFLICT_LEFT], docs_root=FIXTURES, threshold=0.57
        )
        high = detect_conflicts.detect_conflicts(
            changed_files=[CONFLICT_LEFT], docs_root=FIXTURES, threshold=0.58
        )

        self.assertEqual(len(low["conflicts"]), 1)
        self.assertEqual(len(equal["conflicts"]), 1)
        self.assertEqual(len(high["conflicts"]), 0)

    def test_malformed_frontmatter_is_reported_as_error(self):
        report = detect_conflicts.detect_conflicts(
            changed_files=[MALFORMED],
            docs_root=FIXTURES,
            threshold=0.70,
        )
        self.assertTrue(report["errors"])

    def test_deprecated_doc_excluded_from_comparison(self):
        # DEPRECATED has the same domain and a negation-bearing sentence similar
        # to CONFLICT_LEFT, but should be excluded from comparisons.
        report = detect_conflicts.detect_conflicts(
            changed_files=[CONFLICT_LEFT],
            docs_root=FIXTURES,
            threshold=0.50,
        )
        for conflict in report["conflicts"]:
            self.assertNotIn("deprecated-doc.md", conflict["left_file"])
            self.assertNotIn("deprecated-doc.md", conflict["right_file"])

    def test_grouped_by_changed_complete_when_both_docs_changed(self):
        # When both conflicting docs are changed files, the conflict must appear
        # in grouped_by_changed under BOTH keys.
        report = detect_conflicts.detect_conflicts(
            changed_files=[CONFLICT_LEFT, CONFLICT_RIGHT],
            docs_root=FIXTURES,
            threshold=0.50,
        )
        if report["conflicts"]:
            self.assertIn(CONFLICT_LEFT.name.replace(".md", ""), str(list(report["grouped_by_changed"].keys())))
            # Both sides should appear as keys
            keys_str = str(list(report["grouped_by_changed"].keys()))
            self.assertIn("conflict-left", keys_str)
            self.assertIn("conflict-right", keys_str)

    def test_deterministic_ordering(self):
        report = detect_conflicts.detect_conflicts(
            changed_files=[CONFLICT_LEFT, CONFLICT_RIGHT],
            docs_root=FIXTURES,
            threshold=0.50,
        )
        pairs = [
            (c["left_file"], c["right_file"], c["score"]) for c in report["conflicts"]
        ]
        self.assertEqual(pairs, sorted(pairs))


class TestCliBehavior(unittest.TestCase):
    def test_cli_writes_machine_readable_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "conflict-report.json"
            rc = detect_conflicts.main(
                [
                    str(CONFLICT_LEFT),
                    "--docs-root",
                    str(FIXTURES),
                    "--threshold",
                    "0.50",
                    "--output",
                    str(output_path),
                ]
            )
            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("conflicts", payload)

    def test_cli_no_args_returns_non_zero(self):
        rc = detect_conflicts.main([])
        self.assertNotEqual(rc, 0)


class TestOverrideParsing(unittest.TestCase):
    def test_override_marker_and_reason_are_parsed(self):
        payload = (
            "Some intro text\n"
            "conflict-override: justified\n"
            "override-reason: Similar claims are time-scoped and non-contradictory.\n"
        )
        result = detect_conflicts.evaluate_override_request(payload)
        self.assertTrue(result["requested"])
        self.assertTrue(result["accepted"])
        self.assertEqual(result["reason"], "Similar claims are time-scoped and non-contradictory.")
        self.assertEqual(result["errors"], [])

    def test_override_missing_reason_is_rejected(self):
        payload = "conflict-override: justified\noverride-reason:   \n"
        result = detect_conflicts.evaluate_override_request(payload)
        self.assertTrue(result["requested"])
        self.assertFalse(result["accepted"])
        self.assertTrue(any("override-reason" in msg for msg in result["errors"]))

    def test_malformed_override_marker_is_blocking(self):
        payload = "conflict-override: yes\noverride-reason: Needed due to duplicate guidance wording.\n"
        result = detect_conflicts.evaluate_override_request(payload)
        self.assertTrue(result["requested"])
        self.assertFalse(result["accepted"])
        self.assertTrue(any("conflict-override" in msg for msg in result["errors"]))


class TestOverrideAuthorization(unittest.TestCase):
    def test_actor_authorized_for_affected_domain(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codeowners = root / ".github" / "CODEOWNERS"
            codeowners.parent.mkdir(parents=True, exist_ok=True)
            codeowners.write_text(
                "* @default-owner\n"
                "docs/user-authentication/ @slf-aobrien\n",
                encoding="utf-8",
            )

            allowed, details = detect_conflicts.is_actor_authorized_for_domains(
                actor="slf-aobrien",
                domains={"user-authentication"},
                codeowners_path=codeowners,
            )
            self.assertTrue(allowed)
            self.assertIn("user-authentication", details)

    def test_actor_not_authorized_for_affected_domain(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codeowners = root / ".github" / "CODEOWNERS"
            codeowners.parent.mkdir(parents=True, exist_ok=True)
            codeowners.write_text(
                "* @default-owner\n"
                "docs/user-authentication/ @slf-aobrien\n",
                encoding="utf-8",
            )

            allowed, details = detect_conflicts.is_actor_authorized_for_domains(
                actor="someone-else",
                domains={"user-authentication"},
                codeowners_path=codeowners,
            )
            self.assertFalse(allowed)
            self.assertEqual(details["user-authentication"], ["slf-aobrien"])


class TestOverrideAuditLogging(unittest.TestCase):
    def test_append_only_audit_log_rejects_rewrites(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            record = {
                "pr_number": "123",
                "repository": "owner/repo",
                "actor": "slf-aobrien",
                "timestamp_utc": "2026-07-14T00:00:00Z",
                "affected_domains": ["user-authentication"],
                "affected_files": ["docs/user-authentication/concepts.md"],
                "conflict_summary": ["Example summary"],
                "reason": "False positive due to temporal wording.",
            }

            first = detect_conflicts.write_override_audit_record(
                audit_root=root,
                record=record,
                pr_number="123",
                run_id="999",
                run_attempt="1",
            )
            self.assertTrue(first.exists())

            with self.assertRaises(FileExistsError):
                detect_conflicts.write_override_audit_record(
                    audit_root=root,
                    record=record,
                    pr_number="123",
                    run_id="999",
                    run_attempt="1",
                )


class TestOverrideCliFlow(unittest.TestCase):
    def _write_codeowners(self, tmpdir: Path, owner: str = "slf-aobrien") -> Path:
        codeowners = tmpdir / "CODEOWNERS"
        codeowners.write_text(
            f"*                          @default-owner\n"
            f"docs/user-authentication/ @{owner}\n",
            encoding="utf-8",
        )
        return codeowners

    def _write_pr_body(self, tmpdir: Path, body: str) -> Path:
        pr_body_path = tmpdir / "pr-body.txt"
        pr_body_path.write_text(body, encoding="utf-8")
        return pr_body_path

    def test_cli_override_accepted_by_authorized_owner_returns_zero_and_writes_audit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codeowners = self._write_codeowners(root)
            pr_body = self._write_pr_body(
                root,
                "conflict-override: justified\noverride-reason: Both docs are time-scoped, not contradictory.\n",
            )
            audit_root = root / "audit"
            output_path = root / "conflict-report.json"

            rc = detect_conflicts.main(
                [
                    str(CONFLICT_LEFT),
                    "--docs-root",
                    str(FIXTURES),
                    "--threshold",
                    "0.50",
                    "--output",
                    str(output_path),
                    "--pr-body-file",
                    str(pr_body),
                    "--actor",
                    "slf-aobrien",
                    "--codeowners",
                    str(codeowners),
                    "--pr-number",
                    "42",
                    "--audit-root",
                    str(audit_root),
                ]
            )

            self.assertEqual(rc, 0)
            audit_files = list(audit_root.glob("*.json"))
            self.assertEqual(len(audit_files), 1)
            record = json.loads(audit_files[0].read_text(encoding="utf-8"))
            self.assertEqual(record["actor"], "slf-aobrien")
            self.assertEqual(record["pr_number"], "42")

    def test_cli_override_rejected_for_unauthorized_actor_returns_one(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codeowners = self._write_codeowners(root)
            pr_body = self._write_pr_body(
                root,
                "conflict-override: justified\noverride-reason: Not a real conflict.\n",
            )
            audit_root = root / "audit"
            output_path = root / "conflict-report.json"

            rc = detect_conflicts.main(
                [
                    str(CONFLICT_LEFT),
                    "--docs-root",
                    str(FIXTURES),
                    "--threshold",
                    "0.50",
                    "--output",
                    str(output_path),
                    "--pr-body-file",
                    str(pr_body),
                    "--actor",
                    "someone-else",
                    "--codeowners",
                    str(codeowners),
                    "--audit-root",
                    str(audit_root),
                ]
            )

            self.assertEqual(rc, 1)
            self.assertFalse(audit_root.exists())

    def test_cli_malformed_override_blocks_even_without_conflicts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codeowners = self._write_codeowners(root)
            pr_body = self._write_pr_body(root, "conflict-override: yes\noverride-reason: Some reason.\n")
            output_path = root / "conflict-report.json"

            rc = detect_conflicts.main(
                [
                    str(NO_CONFLICT),
                    "--docs-root",
                    str(FIXTURES),
                    "--threshold",
                    "0.70",
                    "--output",
                    str(output_path),
                    "--pr-body-file",
                    str(pr_body),
                    "--actor",
                    "slf-aobrien",
                    "--codeowners",
                    str(codeowners),
                ]
            )

            self.assertEqual(rc, 2)

    def test_cli_override_accepted_but_document_errors_present_still_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codeowners = self._write_codeowners(root)
            pr_body = self._write_pr_body(
                root,
                "conflict-override: justified\noverride-reason: Believed to be a false positive.\n",
            )
            audit_root = root / "audit"
            output_path = root / "conflict-report.json"

            rc = detect_conflicts.main(
                [
                    str(CONFLICT_LEFT),
                    str(MALFORMED),
                    "--docs-root",
                    str(FIXTURES),
                    "--threshold",
                    "0.50",
                    "--output",
                    str(output_path),
                    "--pr-body-file",
                    str(pr_body),
                    "--actor",
                    "slf-aobrien",
                    "--codeowners",
                    str(codeowners),
                    "--audit-root",
                    str(audit_root),
                ]
            )

            self.assertEqual(rc, 2)
            self.assertFalse(audit_root.exists())


if __name__ == "__main__":
    unittest.main()
