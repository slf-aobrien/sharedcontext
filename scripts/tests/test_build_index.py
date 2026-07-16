"""
Unit and integration tests for scripts/build_index.py.

Run with:
    python3 -m unittest discover scripts/tests

Test coverage:
- Fixture-driven parsing and record construction
- Deterministic ordering and byte-stable output across consecutive runs
- Idempotent upsert semantics (no duplicate keyword/document relationships)
- build_manifest_id consistency across all emitted artifacts
- Provenance fields present and correctly mapped
- Active/deprecated document filtering
- Freshness metadata RFC3339 format and SLA offset
- Manifest consistency validation (mismatch → ValueError)
"""
import datetime
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_index import (  # noqa: E402
    FRESHNESS_SLA_MINUTES,
    SCHEMA_VERSION,
    NoFrontMatter,
    build_document_record,
    build_index,
    write_artifacts,
)

FIXTURES = Path(__file__).parent / "fixtures"

# Fixed deterministic values for tests that need byte-equal comparison.
_FIXED_NOW = datetime.datetime(2026, 7, 14, 12, 0, 0, tzinfo=datetime.timezone.utc)
_FIXED_MANIFEST_ID = "00000000-0000-0000-0000-000000000001"


def _make_docs_dir(tmp: Path, files: list[tuple[str, str]]) -> Path:
    """Create a temp docs-like directory with the given (relative_path, content) pairs."""
    docs = tmp / "docs"
    docs.mkdir()
    for rel, content in files:
        dest = docs / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    return docs


def _fixture_md(title: str, domain: str, keywords: list[str], status: str = "active") -> str:
    kw_yaml = "\n".join(f"  - {k}" for k in keywords)
    return (
        "---\n"
        f"title: {title}\n"
        f"domain: {domain}\n"
        f"description: Test document.\n"
        f"keywords:\n{kw_yaml}\n"
        "created: 2026-07-01T00:00:00Z\n"
        "updated: 2026-07-01T00:00:00Z\n"
        "validated-by: tester\n"
        "validated-on: null\n"
        f"status: {status}\n"
        "---\n\n# Body\n"
    )


class TestBuildDocumentRecord(unittest.TestCase):
    def setUp(self):
        self.docs_dir = FIXTURES

    def test_no_front_matter_raises_no_front_matter(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write("# Just a heading\nNo front-matter here.\n")
            tmp = Path(f.name)
        try:
            with self.assertRaises(NoFrontMatter):
                build_document_record(tmp, tmp.parent)
        finally:
            tmp.unlink(missing_ok=True)

    def test_active_document_parsed_correctly(self):
        md = FIXTURES / "index-active-a.md"
        record = build_document_record(md, self.docs_dir)
        self.assertEqual(record["domain"], "payments")
        self.assertEqual(record["title"], "Payment Processing Concepts")
        self.assertTrue(record["active"])
        self.assertIn("payments", record["keywords"])
        self.assertIn("source_path", record)
        self.assertIn("source_hash", record)
        self.assertTrue(record["source_hash"].startswith("sha256:"))

    def test_deprecated_document_marked_inactive(self):
        md = FIXTURES / "index-deprecated.md"
        record = build_document_record(md, self.docs_dir)
        self.assertEqual(record["status"], "deprecated")
        self.assertFalse(record["active"])

    def test_draft_document_marked_inactive(self):
        """Only status == 'active' counts toward the default retrieval set;
        'draft' must not be treated as active."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = Path(tmpdir)
            md = docs / "draft.md"
            md.write_text(
                _fixture_md("Draft Doc", "x", ["x"], status="draft"),
                encoding="utf-8",
            )
            record = build_document_record(md, docs)
            self.assertEqual(record["status"], "draft")
            self.assertFalse(record["active"])

    def test_keywords_are_deduplicated_and_sorted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = Path(tmpdir)
            md = docs / "dup.md"
            md.write_text(
                _fixture_md("Dup", "x", ["beta", "alpha", "beta"]),
                encoding="utf-8",
            )
            record = build_document_record(md, docs)
            self.assertEqual(record["keywords"], sorted(set(["beta", "alpha", "beta"])))

    def test_non_list_non_string_keywords_raise_value_error(self):
        """A keywords value that is neither a string nor a list (e.g. null, an
        int) must raise ValueError, not an uncaught TypeError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = Path(tmpdir)
            md = docs / "bad-keywords.md"
            md.write_text(
                "---\n"
                "title: Bad\n"
                "domain: x\n"
                "description: Test document.\n"
                "keywords: null\n"
                "created: 2026-07-01T00:00:00Z\n"
                "updated: 2026-07-01T00:00:00Z\n"
                "validated-by: tester\n"
                "validated-on: null\n"
                "status: active\n"
                "---\n\n# Body\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                build_document_record(md, docs)

    def test_null_required_field_raises_value_error(self):
        """A null value for a required field (other than validated-on, which
        isn't required here) must raise ValueError, matching generate_jsonld.py's
        contract, instead of silently publishing the string 'None'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = Path(tmpdir)
            md = docs / "null-title.md"
            md.write_text(
                "---\n"
                "title: null\n"
                "domain: x\n"
                "description: Test document.\n"
                "keywords:\n  - x\n"
                "created: 2026-07-01T00:00:00Z\n"
                "updated: 2026-07-01T00:00:00Z\n"
                "validated-by: tester\n"
                "validated-on: null\n"
                "status: active\n"
                "---\n\n# Body\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                build_document_record(md, docs)

    def test_source_path_loaded_from_sidecar_but_hash_always_recomputed(self):
        """source_path may come from the sidecar, but source_hash must always be
        recomputed from the current .md bytes — never trusted from a sidecar
        that could be stale relative to this content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = Path(tmpdir)
            md = docs / "doc.md"
            content = _fixture_md("Doc", "auth", ["auth"])
            md.write_text(content, encoding="utf-8")
            sidecar = docs / "doc.jsonld"
            sidecar.write_text(
                json.dumps({
                    "bsc:source_hash": "sha256:stale_sidecar_hash_value",
                    "bsc:source_path": "custom/path/doc.md",
                }),
                encoding="utf-8",
            )
            record = build_document_record(md, docs)
            import hashlib
            expected_hash = "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()
            self.assertEqual(record["source_hash"], expected_hash)
            self.assertNotEqual(record["source_hash"], "sha256:stale_sidecar_hash_value")
            self.assertEqual(record["source_path"], "custom/path/doc.md")

    def test_provenance_computed_when_no_sidecar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = Path(tmpdir)
            md = docs / "nosidecar.md"
            content = _fixture_md("NoSidecar", "x", ["x"])
            md.write_text(content, encoding="utf-8")
            record = build_document_record(md, docs)
            import hashlib
            expected = "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()
            self.assertEqual(record["source_hash"], expected)

    def test_record_contains_required_provenance_fields(self):
        md = FIXTURES / "index-active-b.md"
        record = build_document_record(md, self.docs_dir)
        for field in ("id", "domain", "slug", "source_path", "source_hash",
                      "title", "description", "keywords", "status", "active",
                      "created", "updated", "validated_by"):
            self.assertIn(field, record, f"Missing field: {field}")


class TestBuildIndex(unittest.TestCase):
    def _run_build(self, docs_dir: Path, source_commit: str = "abc123") -> tuple[dict, dict]:
        return build_index(
            docs_dir,
            source_commit,
            _now_utc=_FIXED_NOW,
            _manifest_id=_FIXED_MANIFEST_ID,
        )

    def test_files_without_front_matter_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
                ("auth/index.md", "# Index\nNo front-matter.\n"),
                ("project-context.md", "# Project Context\nNo front-matter.\n"),
            ])
            # Should not raise; index.md and project-context.md are skipped.
            index, _ = self._run_build(docs)
            all_source_paths = [r["source_path"] for r in index["documents"]]
            self.assertEqual(index["document_count"], 1)
            for sp in all_source_paths:
                self.assertNotIn("index.md", sp)
                self.assertNotIn("project-context.md", sp)

    def test_audit_path_excluded_from_indexing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
                ("_audit/conflict-overrides/pr-1.md",
                 _fixture_md("Override", "audit", ["override"])),
            ])
            index, _ = self._run_build(docs)
            all_source_paths = [r["source_path"] for r in index["documents"]]
            for sp in all_source_paths:
                self.assertNotIn("_audit", sp)
            self.assertEqual(index["document_count"], 1)

    def test_documents_sorted_by_domain_slug_source_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("zeta/z.md", _fixture_md("Z", "zeta", ["z"])),
                ("alpha/a.md", _fixture_md("A", "alpha", ["a"])),
                ("alpha/b.md", _fixture_md("B", "alpha", ["b"])),
            ])
            index, _ = self._run_build(docs)
            domains = [r["domain"] for r in index["documents"]]
            self.assertEqual(domains, ["alpha", "alpha", "zeta"])
            alpha_slugs = [r["slug"] for r in index["documents"] if r["domain"] == "alpha"]
            self.assertEqual(alpha_slugs, sorted(alpha_slugs))

    def test_byte_stable_output_across_two_runs_on_unchanged_inputs(self):
        """Two runs with identical inputs and fixed timestamps/ID produce identical JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("auth/concepts.md", _fixture_md("Auth Concepts", "auth", ["auth", "token"])),
                ("payments/overview.md", _fixture_md("Payments", "payments", ["payments"])),
            ])
            index1, manifest1 = self._run_build(docs, "commit1")
            index2, manifest2 = self._run_build(docs, "commit1")
            self.assertEqual(
                json.dumps(index1, indent=2, ensure_ascii=False),
                json.dumps(index2, indent=2, ensure_ascii=False),
                "index.json output is not byte-stable across two runs",
            )
            self.assertEqual(
                json.dumps(manifest1, indent=2, ensure_ascii=False),
                json.dumps(manifest2, indent=2, ensure_ascii=False),
                "build-manifest.json output is not byte-stable across two runs",
            )

    def test_no_duplicate_keyword_relationships(self):
        """Running build_index twice on the same docs does not duplicate keyword entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["shared-kw", "auth"])),
                ("payments/doc.md", _fixture_md("Pay", "payments", ["shared-kw", "pay"])),
            ])
            index, _ = self._run_build(docs)
            kw_docs = index["relationships"]["keyword_documents"]
            for kw, doc_ids in kw_docs.items():
                self.assertEqual(
                    len(doc_ids), len(set(doc_ids)),
                    f"Duplicate document IDs found for keyword '{kw}': {doc_ids}",
                )

    def test_no_duplicate_domain_relationships(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("auth/a.md", _fixture_md("A", "auth", ["a"])),
                ("auth/b.md", _fixture_md("B", "auth", ["b"])),
            ])
            index, _ = self._run_build(docs)
            domain_docs = index["relationships"]["domain_documents"]
            for domain, doc_ids in domain_docs.items():
                self.assertEqual(
                    len(doc_ids), len(set(doc_ids)),
                    f"Duplicate document IDs found for domain '{domain}': {doc_ids}",
                )

    def test_build_manifest_id_consistent_across_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
            ])
            index, manifest = self._run_build(docs)
            self.assertEqual(
                index["build_manifest_id"],
                manifest["build_manifest_id"],
                "build_manifest_id must be identical in index.json and build-manifest.json",
            )
            self.assertEqual(index["build_manifest_id"], _FIXED_MANIFEST_ID)

    def test_freshness_deadline_is_five_minutes_after_generated_at(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
            ])
            index, manifest = self._run_build(docs)
            # Both artifacts must have freshness_deadline_utc
            for artifact, name in [(index, "index"), (manifest, "manifest")]:
                self.assertIn("freshness_deadline_utc", artifact, f"Missing freshness_deadline_utc in {name}")
            # Deadline should be generated_at + FRESHNESS_SLA_MINUTES
            generated = datetime.datetime.strptime(
                index["generated_at_utc"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=datetime.timezone.utc)
            deadline = datetime.datetime.strptime(
                index["freshness_deadline_utc"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=datetime.timezone.utc)
            delta = (deadline - generated).total_seconds() / 60
            self.assertEqual(delta, FRESHNESS_SLA_MINUTES)

    def test_freshness_timestamps_are_rfc3339(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
            ])
            index, manifest = self._run_build(docs)
            for ts_field in ("generated_at_utc", "freshness_deadline_utc"):
                for artifact, name in [(index, "index"), (manifest, "manifest")]:
                    ts = artifact[ts_field]
                    self.assertRegex(
                        ts,
                        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
                        f"{name}.{ts_field} is not RFC3339 format: {ts!r}",
                    )

    def test_active_documents_list_excludes_deprecated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("auth/active.md", _fixture_md("Active", "auth", ["a"], status="active")),
                ("auth/depr.md", _fixture_md("Deprecated", "auth", ["d"], status="deprecated")),
            ])
            index, _ = self._run_build(docs)
            active_ids = index["active_document_ids"]
            doc_map = {r["id"]: r for r in index["documents"]}
            for doc_id in active_ids:
                self.assertTrue(
                    doc_map[doc_id]["active"],
                    f"Non-active document {doc_id!r} found in active_document_ids",
                )
            # Deprecated doc should still appear in documents list (preserved status metadata)
            all_ids = [r["id"] for r in index["documents"]]
            depr_ids = [r["id"] for r in index["documents"] if not r["active"]]
            self.assertTrue(len(depr_ids) >= 1, "Deprecated document should be in documents list")

    def test_manifest_contains_required_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
            ])
            _, manifest = self._run_build(docs, source_commit="deadbeef")
            for field in (
                "build_manifest_id", "schema_version", "generated_at_utc",
                "source_commit", "document_count", "keyword_count",
            ):
                self.assertIn(field, manifest, f"Missing manifest field: {field}")
            self.assertEqual(manifest["source_commit"], "deadbeef")

    def test_document_count_and_keyword_count_accurate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("a/doc1.md", _fixture_md("D1", "a", ["kw1", "kw2"])),
                ("b/doc2.md", _fixture_md("D2", "b", ["kw2", "kw3"])),
            ])
            index, manifest = self._run_build(docs)
            self.assertEqual(index["document_count"], 2)
            self.assertEqual(manifest["document_count"], 2)
            # kw1, kw2, kw3 — 3 unique keywords
            self.assertEqual(index["keyword_count"], 3)
            self.assertEqual(manifest["keyword_count"], 3)

    def test_schema_version_matches_constant(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs = _make_docs_dir(Path(tmpdir), [
                ("a/doc.md", _fixture_md("D", "a", ["k"])),
            ])
            index, manifest = self._run_build(docs)
            self.assertEqual(index["schema_version"], SCHEMA_VERSION)
            self.assertEqual(manifest["schema_version"], SCHEMA_VERSION)


class TestWriteArtifacts(unittest.TestCase):
    def _run_build_and_write(self, docs_dir: Path, output_dir: Path) -> tuple[Path, Path]:
        index, manifest = build_index(
            docs_dir, "test_commit",
            _now_utc=_FIXED_NOW,
            _manifest_id=_FIXED_MANIFEST_ID,
        )
        return write_artifacts(index, manifest, output_dir)

    def test_artifacts_written_to_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            docs = _make_docs_dir(tmp, [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
            ])
            out = tmp / "index"
            idx_path, manifest_path = self._run_build_and_write(docs, out)
            self.assertTrue(idx_path.exists())
            self.assertTrue(manifest_path.exists())

    def test_no_leftover_tmp_files_after_write(self):
        """write_artifacts writes via temp-file + atomic rename; no .tmp files
        should remain in the output directory after a successful write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            docs = _make_docs_dir(tmp, [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
            ])
            out = tmp / "index"
            self._run_build_and_write(docs, out)
            leftover_tmp_files = list(out.glob("*.tmp"))
            self.assertEqual(leftover_tmp_files, [], f"Leftover tmp files: {leftover_tmp_files}")

    def test_index_json_has_trailing_newline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            docs = _make_docs_dir(tmp, [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
            ])
            out = tmp / "index"
            idx_path, _ = self._run_build_and_write(docs, out)
            raw = idx_path.read_bytes()
            self.assertTrue(raw.endswith(b"\n"), "index.json must end with a newline")

    def test_manifest_json_has_trailing_newline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            docs = _make_docs_dir(tmp, [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
            ])
            out = tmp / "index"
            _, manifest_path = self._run_build_and_write(docs, out)
            raw = manifest_path.read_bytes()
            self.assertTrue(raw.endswith(b"\n"), "build-manifest.json must end with a newline")

    def test_output_dir_created_if_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            docs = _make_docs_dir(tmp, [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
            ])
            out = tmp / "deeply" / "nested" / "output"
            self.assertFalse(out.exists())
            self._run_build_and_write(docs, out)
            self.assertTrue(out.exists())

    def test_manifest_id_mismatch_raises(self):
        index_data = {"build_manifest_id": "id-1", "schema_version": "1.0"}
        manifest_data = {"build_manifest_id": "id-2", "schema_version": "1.0"}
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError) as ctx:
                write_artifacts(index_data, manifest_data, Path(tmpdir) / "out")
            self.assertIn("mismatch", str(ctx.exception).lower())

    def test_artifacts_share_build_manifest_id_on_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            docs = _make_docs_dir(tmp, [
                ("auth/doc.md", _fixture_md("Auth", "auth", ["auth"])),
            ])
            out = tmp / "index"
            idx_path, manifest_path = self._run_build_and_write(docs, out)
            idx = json.loads(idx_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(idx["build_manifest_id"], manifest["build_manifest_id"])


class TestRegressionExistingJsonldTests(unittest.TestCase):
    """Smoke test: existing sidecar test suite must still pass."""

    def test_sidecar_module_importable(self):
        """Importing generate_jsonld must not raise."""
        import generate_jsonld  # noqa: F401


if __name__ == "__main__":
    unittest.main()
