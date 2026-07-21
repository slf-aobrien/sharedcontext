#!/usr/bin/env python3
"""Verify consistency between index/build-manifest.json and index/index.json.

Usage:
    python3 scripts/verify_index_artifacts.py \
      [--manifest index/build-manifest.json] \
      [--index index/index.json]

Exit codes:
  0 - verification passed
  1 - verification failed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


_REQUIRED_MANIFEST_KEYS = {
    "build_manifest_id",
    "schema_version",
    "generated_at_utc",
    "freshness_deadline_utc",
    "source_commit",
    "document_count",
    "keyword_count",
}

_REQUIRED_INDEX_KEYS = {
    "build_manifest_id",
    "schema_version",
    "generated_at_utc",
    "freshness_deadline_utc",
    "document_count",
    "keyword_count",
    "documents",
    "relationships",
}


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return data


def verify_artifacts(manifest_path: Path, index_path: Path) -> list[str]:
    """Return a list of verification errors (empty list means pass)."""
    errors: list[str] = []

    if not manifest_path.exists():
        return [f"missing file: {manifest_path}"]
    if not index_path.exists():
        return [f"missing file: {index_path}"]

    try:
        manifest = _load_json(manifest_path)
    except Exception as exc:  # noqa: BLE001
        return [f"failed to parse manifest JSON: {exc}"]

    try:
        index = _load_json(index_path)
    except Exception as exc:  # noqa: BLE001
        return [f"failed to parse index JSON: {exc}"]

    missing_manifest = sorted(_REQUIRED_MANIFEST_KEYS - set(manifest.keys()))
    if missing_manifest:
        errors.append(
            f"manifest missing required keys: {', '.join(missing_manifest)}"
        )

    missing_index = sorted(_REQUIRED_INDEX_KEYS - set(index.keys()))
    if missing_index:
        errors.append(f"index missing required keys: {', '.join(missing_index)}")

    if errors:
        return errors

    if manifest.get("build_manifest_id") != index.get("build_manifest_id"):
        errors.append("build_manifest_id mismatch between manifest and index")

    if manifest.get("schema_version") != index.get("schema_version"):
        errors.append("schema_version mismatch between manifest and index")

    documents = index.get("documents")
    if not isinstance(documents, list):
        errors.append("index.documents must be a list")
        return errors

    relationships = index.get("relationships")
    if not isinstance(relationships, dict):
        errors.append("index.relationships must be an object")
        return errors

    keyword_documents = relationships.get("keyword_documents")
    if not isinstance(keyword_documents, dict):
        errors.append("index.relationships.keyword_documents must be an object")
        return errors

    manifest_doc_count = manifest.get("document_count")
    if not isinstance(manifest_doc_count, int):
        errors.append("manifest.document_count must be an integer")
    elif manifest_doc_count != len(documents):
        errors.append(
            "document_count mismatch: "
            f"manifest={manifest_doc_count}, index={len(documents)}"
        )

    manifest_keyword_count = manifest.get("keyword_count")
    if not isinstance(manifest_keyword_count, int):
        errors.append("manifest.keyword_count must be an integer")
    elif manifest_keyword_count != len(keyword_documents):
        errors.append(
            "keyword_count mismatch: "
            f"manifest={manifest_keyword_count}, index={len(keyword_documents)}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify build-manifest and index artifact consistency."
    )
    parser.add_argument(
        "--manifest",
        default="index/build-manifest.json",
        help="Path to build-manifest.json",
    )
    parser.add_argument(
        "--index",
        default="index/index.json",
        help="Path to index.json",
    )
    args = parser.parse_args()

    errors = verify_artifacts(Path(args.manifest), Path(args.index))
    if errors:
        print("Artifact verification failed:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    print("Artifact verification passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
