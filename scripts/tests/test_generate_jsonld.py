"""
Unit tests for scripts/generate_jsonld.py.

Run with:
    python3 -m unittest discover scripts/tests
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure scripts/ is importable regardless of cwd.
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from generate_jsonld import (  # noqa: E402
    BSC_NAMESPACE,
    build_jsonld,
    generate_sidecar,
    parse_front_matter,
)

FIXTURES = Path(__file__).parent / "fixtures"
VALID_FIXTURE = FIXTURES / "valid-concepts.md"
MISSING_TITLE_FIXTURE = FIXTURES / "missing-title.md"


class TestParseFrontMatter(unittest.TestCase):
    def test_valid_document_parses_all_fields(self):
        fm = parse_front_matter(VALID_FIXTURE)
        self.assertEqual(fm["title"], "User Authentication Concepts")
        self.assertEqual(fm["domain"], "user-authentication")
        self.assertIn("authentication", fm["keywords"])
        self.assertIsNone(fm.get("validated-on"))

    def test_missing_title_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            parse_front_matter(MISSING_TITLE_FIXTURE)
        self.assertIn("title", str(ctx.exception))

    def test_no_front_matter_raises_value_error(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write("# No front-matter here\n")
            tmp = Path(f.name)
        try:
            with self.assertRaises(ValueError):
                parse_front_matter(tmp)
        finally:
            tmp.unlink(missing_ok=True)

    def test_malformed_yaml_raises_value_error(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write("---\ntitle: [unclosed\n---\n")
            tmp = Path(f.name)
        try:
            with self.assertRaises(ValueError):
                parse_front_matter(tmp)
        finally:
            tmp.unlink(missing_ok=True)


class TestBuildJsonLD(unittest.TestCase):
    def setUp(self):
        self.fm = parse_front_matter(VALID_FIXTURE)
        self.source_path = "docs/user-authentication/concepts.md"
        self.source_hash = "sha256:abc123"

    def test_context_present(self):
        doc = build_jsonld(self.fm, self.source_path, self.source_hash)
        self.assertIn("@context", doc)
        ctx = doc["@context"]
        self.assertIn("@vocab", ctx)
        self.assertIn("dc", ctx)
        self.assertIn("bsc", ctx)

    def test_type_is_digital_document(self):
        doc = build_jsonld(self.fm, self.source_path, self.source_hash)
        self.assertEqual(doc["@type"], "DigitalDocument")

    def test_id_derived_from_source_path(self):
        doc = build_jsonld(self.fm, self.source_path, self.source_hash)
        self.assertEqual(doc["@id"], "bsc:docs/user-authentication/concepts")

    def test_all_required_fields_present(self):
        doc = build_jsonld(self.fm, self.source_path, self.source_hash)
        required = [
            "dc:title",
            "dc:description",
            "dc:subject",
            "dc:created",
            "dc:modified",
            "dc:contributor",
            "contentStatus",
            "bsc:domain",
            "bsc:validated_on",
            "bsc:source_path",
            "bsc:source_hash",
            "bsc:schema_version",
        ]
        for field in required:
            self.assertIn(field, doc, f"Missing field: {field}")

    def test_validated_on_null_maps_to_json_null(self):
        doc = build_jsonld(self.fm, self.source_path, self.source_hash)
        # Must be None (JSON null), not the string "null" or missing.
        self.assertIn("bsc:validated_on", doc)
        self.assertIsNone(doc["bsc:validated_on"])

    def test_keywords_is_list(self):
        doc = build_jsonld(self.fm, self.source_path, self.source_hash)
        self.assertIsInstance(doc["dc:subject"], list)


class TestGenerateSidecar(unittest.TestCase):
    def test_valid_document_produces_sidecar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_md = Path(tmpdir) / "concepts.md"
            tmp_md.write_bytes(VALID_FIXTURE.read_bytes())

            result = generate_sidecar(tmp_md)
            self.assertEqual(result, tmp_md.with_suffix(".jsonld"))
            self.assertTrue(result.exists())

            content = result.read_text(encoding="utf-8")
            doc = json.loads(content)

            self.assertEqual(doc["@type"], "DigitalDocument")
            self.assertIn("@context", doc)

    def test_source_hash_matches_sha256_of_file_bytes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_md = Path(tmpdir) / "concepts.md"
            raw = VALID_FIXTURE.read_bytes()
            tmp_md.write_bytes(raw)

            generate_sidecar(tmp_md)
            sidecar = tmp_md.with_suffix(".jsonld")
            doc = json.loads(sidecar.read_text(encoding="utf-8"))

            expected_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
            self.assertEqual(doc["bsc:source_hash"], expected_hash)

    def test_source_path_is_relative_not_absolute(self):
        """When a repo-root-relative path is passed, source_path in the sidecar is relative."""
        # Simulate the CI workflow: run from repo root, pass a relative path.
        import os

        original_cwd = os.getcwd()
        repo_root = Path(__file__).resolve().parent.parent.parent  # bmadSharedContext/
        try:
            os.chdir(repo_root)
            relative_input = Path("scripts/tests/fixtures/valid-concepts.md")
            sidecar_path = generate_sidecar(relative_input)
            try:
                doc = json.loads(sidecar_path.read_text(encoding="utf-8"))
                self.assertFalse(
                    doc["bsc:source_path"].startswith("/"),
                    f"source_path should not be absolute for relative input: {doc['bsc:source_path']}",
                )
                self.assertEqual(
                    doc["bsc:source_path"], "scripts/tests/fixtures/valid-concepts.md"
                )
            finally:
                sidecar_path.unlink(missing_ok=True)
        finally:
            os.chdir(original_cwd)

    def test_missing_required_field_raises_and_no_sidecar_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_md = Path(tmpdir) / "missing-title.md"
            tmp_md.write_bytes(MISSING_TITLE_FIXTURE.read_bytes())

            with self.assertRaises(ValueError) as ctx:
                generate_sidecar(tmp_md)
            self.assertIn("title", str(ctx.exception))

            sidecar = tmp_md.with_suffix(".jsonld")
            self.assertFalse(
                sidecar.exists(),
                "No sidecar should be written when required field is missing",
            )

    def test_sidecar_output_ends_with_newline(self):
        """Sidecars are written with a trailing newline (human-readable convention)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_md = Path(tmpdir) / "concepts.md"
            tmp_md.write_bytes(VALID_FIXTURE.read_bytes())

            generate_sidecar(tmp_md)
            raw = (tmp_md.with_suffix(".jsonld")).read_text(encoding="utf-8")
            self.assertTrue(raw.endswith("\n"))

    def test_sidecar_is_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_md = Path(tmpdir) / "concepts.md"
            tmp_md.write_bytes(VALID_FIXTURE.read_bytes())

            generate_sidecar(tmp_md)
            sidecar = tmp_md.with_suffix(".jsonld")
            # Should not raise
            json.loads(sidecar.read_text(encoding="utf-8"))


class TestMainEntryPoint(unittest.TestCase):
    """Test main() via generate_sidecar logic without subprocess overhead."""

    def test_no_args_exits_one(self):
        import generate_jsonld as gjl

        original_argv = sys.argv
        sys.argv = ["generate_jsonld.py"]
        try:
            result = gjl.main()
            self.assertEqual(result, 1)
        finally:
            sys.argv = original_argv

    def test_one_valid_file_exits_zero(self):
        import generate_jsonld as gjl

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_md = Path(tmpdir) / "concepts.md"
            tmp_md.write_bytes(VALID_FIXTURE.read_bytes())

            original_argv = sys.argv
            sys.argv = ["generate_jsonld.py", str(tmp_md)]
            try:
                result = gjl.main()
                self.assertEqual(result, 0)
            finally:
                sys.argv = original_argv

    def test_invalid_file_exits_one(self):
        import generate_jsonld as gjl

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_md = Path(tmpdir) / "missing-title.md"
            tmp_md.write_bytes(MISSING_TITLE_FIXTURE.read_bytes())

            original_argv = sys.argv
            sys.argv = ["generate_jsonld.py", str(tmp_md)]
            try:
                result = gjl.main()
                self.assertEqual(result, 1)
            finally:
                sys.argv = original_argv

    def test_mixed_files_continues_and_exits_one(self):
        """One bad file does not abort the batch; good files succeed; exit code is 1."""
        import generate_jsonld as gjl

        with tempfile.TemporaryDirectory() as tmpdir:
            valid_md = Path(tmpdir) / "valid.md"
            valid_md.write_bytes(VALID_FIXTURE.read_bytes())

            bad_md = Path(tmpdir) / "bad.md"
            bad_md.write_bytes(MISSING_TITLE_FIXTURE.read_bytes())

            original_argv = sys.argv
            sys.argv = ["generate_jsonld.py", str(valid_md), str(bad_md)]
            try:
                result = gjl.main()
                self.assertEqual(result, 1)
            finally:
                sys.argv = original_argv

            # The valid file's sidecar must still have been written.
            self.assertTrue(valid_md.with_suffix(".jsonld").exists())


if __name__ == "__main__":
    unittest.main()
