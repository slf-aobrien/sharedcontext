#!/usr/bin/env python3
"""
Build a deterministic full-snapshot index from docs/**/*.md and docs/**/*.jsonld.

Produces two publication artifacts per run:
  OUTPUT_DIR/index.json           — full document index with relationships
  OUTPUT_DIR/build-manifest.json  — build provenance and freshness SLA marker

Both artifacts carry an identical build_manifest_id that ties this snapshot run.

Usage:
    python3 scripts/build_index.py [--docs-dir DOCS_DIR] [--output-dir OUTPUT_DIR]
                                    [--source-commit SHA]

Exit codes:
  0 — success
  1 — one or more documents failed to parse, or artifact consistency validation failed

Determinism contract:
  Given identical input documents and fixed _now_utc/_manifest_id parameters, this
  script produces byte-identical output across consecutive runs.  Ordering is
  stable: documents sorted by (domain, slug, source_path); relationship map keys
  and values sorted lexicographically.

Freshness SLA:
  freshness_deadline_utc = generated_at_utc + FRESHNESS_SLA_MINUTES minutes.
  Both artifacts carry this field so Epic 3 retrieval can surface SLA compliance
  without reworking the publication schema.
"""
import argparse
import datetime
import hashlib
import json
import sys
import uuid
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

SCHEMA_VERSION = "1.0"
FRESHNESS_SLA_MINUTES = 5

_REQUIRED_FIELDS = [
    "title",
    "domain",
    "description",
    "keywords",
    "created",
    "updated",
    "validated-by",
    "status",
]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


class NoFrontMatter(Exception):
    """Raised when a markdown file has no YAML front-matter block at all.

    This is not an error — the file is simply not a context document and
    should be silently skipped by the index builder.
    """


def parse_front_matter(path: Path) -> dict:
    """Parse YAML front-matter from a markdown file.

    Uses yaml.safe_load exclusively — yaml.load() without a Loader is an OWASP
    deserialization injection risk and is never used here.

    Raises NoFrontMatter if the file has no leading '---' (not a context doc).
    Raises ValueError if front-matter is present but malformed or lacks required
    fields.
    """
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        raise NoFrontMatter(f"{path}: no YAML front-matter block")

    rest = content[3:]
    end = rest.find("\n---")
    if end == -1:
        raise ValueError("malformed YAML front-matter: no closing '---' found")

    front_matter_text = rest[:end]
    try:
        # ALWAYS use safe_load — yaml.load() without a Loader is an OWASP
        # deserialization injection risk.
        data = yaml.safe_load(front_matter_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error in front-matter: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("front-matter did not parse as a mapping")

    for field in _REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"missing required front-matter field: {field}")
        if data[field] is None:
            raise ValueError(f"required front-matter field is null: {field}")

    return data


def _compute_source_hash(path: Path) -> str:
    """Compute sha256 hash of file bytes, prefixed with 'sha256:'."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_sidecar_provenance(md_path: Path) -> dict:
    """Load the canonical source_path from the .jsonld sidecar, if present.

    source_hash is intentionally NOT sourced from the sidecar: it is always
    recomputed from the current .md file bytes (see build_document_record) so
    published provenance reflects actual content even if the sidecar is stale.

    Returns a dict with key 'source_path' when available.
    Returns an empty dict if the sidecar is absent, unreadable, or has no path.
    """
    sidecar = md_path.with_suffix(".jsonld")
    if not sidecar.exists():
        return {}
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    result = {}
    if data.get("bsc:source_path"):
        result["source_path"] = data["bsc:source_path"]
    return result


def _source_path_str(md_path: Path, docs_dir: Path) -> str:
    """Return a repo-root-relative POSIX path for a markdown file.

    Attempts to compute a path relative to the parent of docs_dir (the repo root).
    Falls back to the absolute POSIX path if that fails.
    """
    try:
        return md_path.relative_to(docs_dir.parent).as_posix()
    except ValueError:
        return md_path.as_posix()


def _slug_from_source_path(source_path: str) -> str:
    """Extract slug: filename stem from source_path."""
    return Path(source_path).stem


# ---------------------------------------------------------------------------
# Document record builder
# ---------------------------------------------------------------------------


def build_document_record(md_path: Path, docs_dir: Path) -> dict:
    """Build a single document index record from a markdown file.

    Provenance (source_hash, source_path) is sourced from the .jsonld sidecar
    when present, or computed on the fly.  Both paths are preserved so API
    consumers can trace each record back to canonical markdown.
    """
    fm = parse_front_matter(md_path)

    # --- Provenance ---
    sidecar_prov = _load_sidecar_provenance(md_path)
    # Always recompute the hash from current file bytes — never trust a
    # sidecar-supplied hash, which may be stale relative to this content.
    source_hash = _compute_source_hash(md_path)
    # Prefer the canonicalized path from the sidecar (matches generate_jsonld.py contract).
    source_path = sidecar_prov.get("source_path") or _source_path_str(md_path, docs_dir)

    # --- Core fields ---
    domain = str(fm["domain"])
    slug = _slug_from_source_path(source_path)

    # Keywords: normalise to a sorted, deduplicated list of strings.
    keywords_raw = fm["keywords"]
    if isinstance(keywords_raw, str):
        keywords_raw = [keywords_raw]
    elif not isinstance(keywords_raw, list):
        raise ValueError(
            f"keywords must be a string or list, got {type(keywords_raw).__name__}"
        )
    keywords = sorted({str(k) for k in keywords_raw})

    # Only the exact "active" status counts toward the default retrieval set;
    # "draft" and "deprecated" (and any unrecognized value) are excluded.
    is_active = str(fm.get("status", "")).lower() == "active"

    # Document ID: source_path without the .md extension.
    doc_id = source_path.rsplit(".", 1)[0] if "." in source_path else source_path

    return {
        "id": doc_id,
        "domain": domain,
        "slug": slug,
        "source_path": source_path,
        "source_hash": source_hash,
        "title": str(fm["title"]),
        "description": str(fm["description"]),
        "keywords": keywords,
        "status": str(fm.get("status", "")),
        "active": is_active,
        "created": str(fm.get("created", "")),
        "updated": str(fm.get("updated", "")),
        "validated_by": str(fm.get("validated-by", "")),
    }


# ---------------------------------------------------------------------------
# YAML document record builder
# ---------------------------------------------------------------------------


def parse_yaml_document(path: Path) -> dict:
    """Parse a YAML context document (full-file YAML, no Markdown front-matter).

    A file is treated as a context document when it carries at least one of:
    ``concept-id``, ``scan-id``, or ``title``.  Files without any of these
    are silently skipped via NoFrontMatter so the index builder treats them
    the same way it treats non-context Markdown files.

    Uses yaml.safe_load exclusively — yaml.load() without a Loader is an OWASP
    deserialization injection risk and is never used here.

    Raises NoFrontMatter (silent skip) when the file is not a context document.
    Raises ValueError when the YAML is malformed.
    """
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error: {exc}") from exc

    if not isinstance(data, dict):
        raise NoFrontMatter(f"{path}: top-level YAML is not a mapping — not a context document")

    if not (data.get("concept-id") or data.get("scan-id") or data.get("title")):
        raise NoFrontMatter(
            f"{path}: no concept-id, scan-id, or title field — not a context document"
        )

    return data


def build_yaml_document_record(yaml_path: Path, docs_dir: Path) -> dict:
    """Build a single document index record from a YAML context document.

    YAML context documents use a flat-file schema rather than Markdown
    front-matter.  Available fields are mapped to the shared record schema;
    fields that have no YAML equivalent (created, updated, validated_by) are
    left as empty strings so API consumers receive a consistent record shape.

    Keyword derivation:
      - Each directory component of the domain path (e.g. 'member', 'enrollment')
      - Top-level YAML keys whose value is a non-empty list (rule sections such
        as 'required-data', 'eligibility-rules') — these are the most
        semantically meaningful keywords for retrieval.

    Domain derivation:
      The directory path of the YAML file relative to docs_dir, using POSIX
      separators (e.g. 'benefit/voluntaryDental').  Files at the root of
      docs_dir get domain 'root'.
    """
    data = parse_yaml_document(yaml_path)

    source_hash = _compute_source_hash(yaml_path)
    source_path = _source_path_str(yaml_path, docs_dir)

    # Domain: directory path relative to docs_dir, POSIX-style.
    try:
        rel = yaml_path.relative_to(docs_dir)
        domain = rel.parent.as_posix() if rel.parent.as_posix() != "." else "root"
    except ValueError:
        domain = "root"

    slug = _slug_from_source_path(source_path)

    # Title: explicit field, or title-case the concept/scan id, or the slug.
    raw_id = str(data.get("concept-id") or data.get("scan-id") or slug)
    title = str(data.get("title") or raw_id.replace("-", " ").title())

    # Description: scope field > scan-scope.codebase derivation > empty.
    description = ""
    if data.get("scope"):
        description = str(data["scope"])
    elif isinstance(data.get("scan-scope"), dict):
        codebase = data["scan-scope"].get("codebase", "")
        if codebase:
            description = f"Scan of {codebase} codebase"

    # Keywords: domain path components + non-empty top-level rule section names.
    domain_keywords: set[str] = set(domain.replace("/", " ").split())
    rule_section_keywords: set[str] = {
        k
        for k, v in data.items()
        if isinstance(v, list) and len(v) > 0 and k != "schema"
    }
    keywords = sorted(domain_keywords | rule_section_keywords)
    if not keywords:
        keywords = [slug]

    status = str(data.get("status", "draft")).lower()
    is_active = status == "active"
    doc_id = source_path.rsplit(".", 1)[0] if "." in source_path else source_path

    return {
        "id": doc_id,
        "domain": domain,
        "slug": slug,
        "source_path": source_path,
        "source_hash": source_hash,
        "title": title,
        "description": description,
        "keywords": keywords,
        "status": status,
        "active": is_active,
        "created": "",
        "updated": "",
        "validated_by": "",
    }


# ---------------------------------------------------------------------------
# Index builder
# ---------------------------------------------------------------------------


def build_index(
    docs_dir: Path,
    source_commit: str,
    *,
    _now_utc: datetime.datetime | None = None,
    _manifest_id: str | None = None,
) -> tuple[dict, dict]:
    """Scan docs_dir/**/*.md and build deterministic index + manifest data.

    Parameters
    ----------
    docs_dir:
        Root directory containing context documents (scanned recursively).
    source_commit:
        Git commit SHA to record in the build manifest.
    _now_utc:
        Override current UTC time (for deterministic tests). When None, uses
        ``datetime.datetime.now(datetime.timezone.utc)``.
    _manifest_id:
        Override the UUID4 build manifest ID (for deterministic tests). When
        None, a fresh UUID4 is generated.

    Returns
    -------
    (index_data, manifest_data) — two dicts ready for JSON serialisation.

    Raises ValueError if any document fails to parse.
    """
    build_manifest_id = _manifest_id if _manifest_id is not None else str(uuid.uuid4())
    now_utc = _now_utc if _now_utc is not None else datetime.datetime.now(datetime.timezone.utc)

    generated_at_utc = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    deadline_utc = now_utc + datetime.timedelta(minutes=FRESHNESS_SLA_MINUTES)
    freshness_deadline_utc = deadline_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- Parse all markdown documents ---
    # Exclude the _audit/ overlay path — conflict override records are not
    # indexable context documents.
    _audit_parts = {"_audit"}

    errors: list[str] = []
    raw_records: list[dict] = []

    for md_path in sorted(docs_dir.rglob("*.md")):
        # Skip files inside _audit/ subtrees.
        if _audit_parts.intersection(md_path.parts):
            continue
        try:
            record = build_document_record(md_path, docs_dir)
            raw_records.append(record)
        except NoFrontMatter:
            # Not a context document — skip silently.
            pass
        except (ValueError, OSError) as exc:
            errors.append(f"ERROR [{md_path}]: {exc}")

    # --- Parse YAML/YML context documents ---
    # Scanned after Markdown so any sidecar provenance written during the
    # sidecar-generation step is already on disk when the index builder runs.
    # YAML files lacking a recognisable identifier (concept-id / scan-id /
    # title) are silently skipped via the NoFrontMatter path, just like
    # Markdown files that have no front-matter block.
    for yaml_path in sorted([*docs_dir.rglob("*.yaml"), *docs_dir.rglob("*.yml")]):
        if _audit_parts.intersection(yaml_path.parts):
            continue
        try:
            record = build_yaml_document_record(yaml_path, docs_dir)
            raw_records.append(record)
        except NoFrontMatter:
            # Not a context document — skip silently.
            pass
        except (ValueError, OSError) as exc:
            errors.append(f"ERROR [{yaml_path}]: {exc}")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        raise ValueError(
            f"Index build failed: {len(errors)} document(s) could not be parsed"
        )

    # --- Deterministic sort: (domain, slug, source_path) ---
    raw_records.sort(key=lambda r: (r["domain"], r["slug"], r["source_path"]))

    # --- Build relationship maps (replace-by-snapshot, never append-log) ---
    # Each map is built fresh from the sorted record list; duplicate-free by
    # construction because we check membership before appending.
    domain_documents: dict[str, list[str]] = {}
    keyword_documents: dict[str, list[str]] = {}

    for rec in raw_records:
        domain = rec["domain"]
        doc_id = rec["id"]

        if domain not in domain_documents:
            domain_documents[domain] = []
        if doc_id not in domain_documents[domain]:
            domain_documents[domain].append(doc_id)

        for kw in rec["keywords"]:
            if kw not in keyword_documents:
                keyword_documents[kw] = []
            if doc_id not in keyword_documents[kw]:
                keyword_documents[kw].append(doc_id)

    # Sort relationship map values and keys for determinism.
    sorted_domain_documents = {
        k: sorted(v) for k, v in sorted(domain_documents.items())
    }
    sorted_keyword_documents = {
        k: sorted(v) for k, v in sorted(keyword_documents.items())
    }

    # Active document IDs list (default retrieval set; deprecated docs still in
    # full documents array with their status metadata preserved).
    active_ids = sorted(r["id"] for r in raw_records if r["active"])

    document_count = len(raw_records)
    keyword_count = len(keyword_documents)

    index_data: dict = {
        "build_manifest_id": build_manifest_id,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc,
        "freshness_deadline_utc": freshness_deadline_utc,
        "document_count": document_count,
        "keyword_count": keyword_count,
        "active_document_ids": active_ids,
        "documents": raw_records,
        "relationships": {
            "domain_documents": sorted_domain_documents,
            "keyword_documents": sorted_keyword_documents,
        },
    }

    manifest_data: dict = {
        "build_manifest_id": build_manifest_id,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc,
        "freshness_deadline_utc": freshness_deadline_utc,
        "source_commit": source_commit,
        "document_count": document_count,
        "keyword_count": keyword_count,
    }

    return index_data, manifest_data


# ---------------------------------------------------------------------------
# Artifact writer
# ---------------------------------------------------------------------------


def _atomic_write_json(path: Path, data: dict) -> None:
    """Write data as indented UTF-8 JSON to path atomically.

    Writes to a temporary sibling file first, then renames it into place via
    Path.replace() (os.replace() under the hood), which is atomic on both
    POSIX and Windows. This ensures a crash mid-write cannot leave a
    truncated or partially-written artifact at the final path.
    """
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


def write_artifacts(
    index_data: dict,
    manifest_data: dict,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Serialise index_data and manifest_data to output_dir as JSON files.

    Validates that both artifacts carry the same build_manifest_id before
    writing — raises ValueError if they differ (publication would be corrupt).

    Each file is written atomically (temp file + rename) so an interrupted
    run cannot leave a truncated or mismatched artifact on disk.

    Returns (index_path, manifest_path).
    """
    id_index = index_data.get("build_manifest_id")
    id_manifest = manifest_data.get("build_manifest_id")
    if id_index != id_manifest:
        raise ValueError(
            f"build_manifest_id mismatch between artifacts: "
            f"index={id_index!r}, manifest={id_manifest!r}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    index_path = output_dir / "index.json"
    manifest_path = output_dir / "build-manifest.json"

    # Use indent=2, UTF-8, trailing newline — consistent with generate_jsonld.py.
    _atomic_write_json(index_path, index_data)
    _atomic_write_json(manifest_path, manifest_data)

    return index_path, manifest_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point. Returns exit code (0 = success, 1 = failure)."""
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic full-snapshot index from docs/**/*.md "
            "and emit index.json + build-manifest.json."
        )
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Directory containing context documents (default: docs)",
    )
    parser.add_argument(
        "--output-dir",
        default="index",
        help="Output directory for index artifacts (default: index)",
    )
    parser.add_argument(
        "--source-commit",
        default="",
        help="Git commit SHA to record in build manifest (default: empty string)",
    )
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    output_dir = Path(args.output_dir)
    source_commit = args.source_commit

    if not docs_dir.is_dir():
        print(f"ERROR: docs-dir does not exist or is not a directory: {docs_dir}", file=sys.stderr)
        return 1

    try:
        index_data, manifest_data = build_index(docs_dir, source_commit)
        index_path, manifest_path = write_artifacts(index_data, manifest_data, output_dir)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Emit workflow summary (visible in GitHub Actions step summary via GITHUB_STEP_SUMMARY).
    summary_lines = [
        "=== Index Build Summary ===",
        f"Build manifest ID : {index_data['build_manifest_id']}",
        f"Published at (UTC): {index_data['generated_at_utc']}",
        f"Freshness deadline: {index_data['freshness_deadline_utc']}",
        f"Documents indexed : {index_data['document_count']}",
        f"Keywords indexed  : {index_data['keyword_count']}",
        f"Active documents  : {len(index_data['active_document_ids'])}",
        f"Index artifact    : {index_path}",
        f"Manifest artifact : {manifest_path}",
    ]
    print("\n".join(summary_lines))

    return 0


if __name__ == "__main__":
    sys.exit(main())
