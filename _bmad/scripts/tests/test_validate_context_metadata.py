"""Contract tests for context document metadata validation."""
import importlib.util
import sys
import tempfile
from pathlib import Path
import unittest

_SPEC = importlib.util.spec_from_file_location(
    "validate_context_metadata",
    Path(__file__).resolve().parent.parent / "validate_context_metadata.py",
)
validate_context_metadata = importlib.util.module_from_spec(_SPEC)
sys.modules["validate_context_metadata"] = validate_context_metadata
_SPEC.loader.exec_module(validate_context_metadata)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "context_docs"


def _fixture(name: str) -> Path:
    return FIXTURES / name


class ValidateContextMetadataTests(unittest.TestCase):
    def test_valid_document_passes_with_no_errors(self):
        result = validate_context_metadata.validate_paths([_fixture("valid.md")])
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["deprecated"], [])
        self.assertEqual(result["helpers"], [])

    def test_missing_required_field_reports_file_and_field(self):
        result = validate_context_metadata.validate_paths([_fixture("missing-title.md")])
        self.assertFalse(result["ok"])
        self.assertTrue(any(
            e["file"].endswith("missing-title.md") and e["field"] == "title" and "missing required field" in e["message"]
            for e in result["errors"]
        ))

    def test_invalid_status_is_rejected_with_field_diagnostic(self):
        result = validate_context_metadata.validate_paths([_fixture("invalid-status.md")])
        self.assertFalse(result["ok"])
        self.assertTrue(any(e["field"] == "status" and "must be one of" in e["message"] for e in result["errors"]))

    def test_invalid_timestamp_is_rejected_with_field_diagnostic(self):
        result = validate_context_metadata.validate_paths([_fixture("invalid-created-timestamp.md")])
        self.assertFalse(result["ok"])
        self.assertTrue(any(e["field"] == "created" and "RFC3339 UTC" in e["message"] for e in result["errors"]))

    def test_validated_on_can_be_null_for_unvalidated_documents(self):
        result = validate_context_metadata.validate_paths([_fixture("validated-on-null.md")])
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])

    def test_deprecated_document_is_valid_but_flagged(self):
        result = validate_context_metadata.validate_paths([_fixture("deprecated-valid.md")])
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["deprecated"]), 1)
        self.assertTrue(result["deprecated"][0].endswith("deprecated-valid.md"))

    def test_flow_style_keywords_are_rejected_with_actionable_message(self):
        result = validate_context_metadata.validate_paths([_fixture("flow-style-keywords.md")])
        self.assertFalse(result["ok"])
        self.assertTrue(any(
            e["field"] == "keywords" and "must use block-list YAML for consistency" in e["message"]
            for e in result["errors"]
        ))
        self.assertTrue(any(
            "x-bmad-authoring-conventions" in msg and "keywords_yaml_example" in msg
            for msg in result["helpers"]
        ))

    def test_nonexistent_input_path_is_reported_explicitly(self):
        result = validate_context_metadata.validate_inputs(["/tmp/definitely-not-here-context.md"])
        self.assertFalse(result["ok"])
        self.assertTrue(any(
            e["field"] == "path"
            and e["file"].endswith("definitely-not-here-context.md")
            and "does not exist" in e["message"]
            for e in result["errors"]
        ))

    def test_multiline_yaml_block_scalar_is_reported_explicitly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "multiline.md"
            path.write_text(
                "---\n"
                "title: Example\n"
                "domain: user-authentication\n"
                "description: |\n"
                "  first line\n"
                "  second line\n"
                "keywords:\n"
                "  - schema\n"
                "created: 2026-07-08T00:00:00Z\n"
                "updated: 2026-07-08T00:00:00Z\n"
                "validated-by: Aaron\n"
                "validated-on: null\n"
                "status: draft\n"
                "---\n",
                encoding="utf-8",
            )

            result = validate_context_metadata.validate_paths([path])

        self.assertFalse(result["ok"])
        self.assertTrue(any(
            e["field"] == "description" and "block scalars are not supported" in e["message"]
            for e in result["errors"]
        ))

    def test_flow_style_keywords_still_produce_authoring_convention_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "flow-keywords.md"
            path.write_text(
                "---\n"
                "title: Example\n"
                "domain: user-authentication\n"
                "description: Example document\n"
                "keywords: [schema, metadata]\n"
                "created: 2026-07-08T00:00:00Z\n"
                "updated: 2026-07-08T00:00:00Z\n"
                "validated-by: Aaron\n"
                "validated-on: null\n"
                "status: draft\n"
                "---\n",
                encoding="utf-8",
            )

            result = validate_context_metadata.validate_paths([path])

        self.assertFalse(result["ok"])
        self.assertTrue(any(
            e["field"] == "keywords" and "block-list YAML for consistency" in e["message"]
            for e in result["errors"]
        ))

    def test_invalid_utf8_file_is_reported_as_file_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad-encoding.md"
            with path.open("wb") as handle:
                handle.write(b"---\n")
                handle.write(b"title: invalid\n")
                handle.write(b"description: ")
                handle.write(bytes([0xff, 0xfe]))
                handle.write(b"\n")
                handle.write(b"---\n")

            result = validate_context_metadata.validate_paths([path])

        self.assertFalse(result["ok"])
        self.assertTrue(any(
            e["field"] == "file" and "not valid UTF-8" in e["message"]
            for e in result["errors"]
        ))


if __name__ == "__main__":
    unittest.main()
