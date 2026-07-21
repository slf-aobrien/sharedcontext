import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from verify_index_artifacts import verify_artifacts  # noqa: E402


class TestVerifyIndexArtifacts(unittest.TestCase):
    def _write(self, path: Path, obj: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")

    def test_valid_artifacts_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = root / "index" / "build-manifest.json"
            index = root / "index" / "index.json"

            manifest_obj = {
                "build_manifest_id": "abc",
                "schema_version": "1.0",
                "generated_at_utc": "2026-07-16T15:24:56Z",
                "freshness_deadline_utc": "2026-07-16T15:29:56Z",
                "source_commit": "deadbeef",
                "document_count": 1,
                "keyword_count": 2,
            }
            index_obj = {
                "build_manifest_id": "abc",
                "schema_version": "1.0",
                "generated_at_utc": "2026-07-16T15:24:56Z",
                "freshness_deadline_utc": "2026-07-16T15:29:56Z",
                "document_count": 1,
                "keyword_count": 2,
                "documents": [{"id": "d1"}],
                "relationships": {
                    "keyword_documents": {
                        "k1": ["d1"],
                        "k2": ["d1"],
                    }
                },
            }

            self._write(manifest, manifest_obj)
            self._write(index, index_obj)
            self.assertEqual(verify_artifacts(manifest, index), [])

    def test_keyword_count_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = root / "index" / "build-manifest.json"
            index = root / "index" / "index.json"

            self._write(
                manifest,
                {
                    "build_manifest_id": "abc",
                    "schema_version": "1.0",
                    "generated_at_utc": "2026-07-16T15:24:56Z",
                    "freshness_deadline_utc": "2026-07-16T15:29:56Z",
                    "source_commit": "deadbeef",
                    "document_count": 1,
                    "keyword_count": 3,
                },
            )
            self._write(
                index,
                {
                    "build_manifest_id": "abc",
                    "schema_version": "1.0",
                    "generated_at_utc": "2026-07-16T15:24:56Z",
                    "freshness_deadline_utc": "2026-07-16T15:29:56Z",
                    "document_count": 1,
                    "keyword_count": 3,
                    "documents": [{"id": "d1"}],
                    "relationships": {"keyword_documents": {"k1": ["d1"]}},
                },
            )

            errors = verify_artifacts(manifest, index)
            self.assertTrue(any("keyword_count mismatch" in e for e in errors))
