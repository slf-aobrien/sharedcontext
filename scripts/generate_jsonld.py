#!/usr/bin/env python3
"""
Generate JSON-LD sidecars for context documents.

Usage: python3 scripts/generate_jsonld.py <file1.md> [<file2.md> ...]

For each .md file, writes a .jsonld sidecar alongside it using schema.org /
Dublin Core / bsc: namespace per the bmadSharedContext sidecar contract.

bsc: namespace URI (https://github.com/slf-aobrien/bmadSharedContext/vocab#) is
a pilot placeholder that does not resolve. This is intentional per the Phase 1
addendum's loose standards posture.

Exits 0 if all files succeed; exits 1 if any file fails (errors collected and
reported before exit so the full batch is attempted).
"""
import datetime
import hashlib
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

BSC_NAMESPACE = "https://github.com/slf-aobrien/bmadSharedContext/vocab#"
SCHEMA_VERSION = "1.0"
REQUIRED_FIELDS = [
    "title",
    "domain",
    "description",
    "keywords",
    "created",
    "updated",
    "validated-by",
    "status",
]


def parse_front_matter(path: Path) -> dict:
    """Parse YAML front-matter from a markdown file. Raises ValueError on failure."""
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        raise ValueError("missing YAML front-matter block (no leading '---')")

    # Find the closing ---
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

    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"missing required front-matter field: {field}")
        if data[field] is None and field != "validated-on":
            raise ValueError(f"required front-matter field is null: {field}")

    return data


def _to_rfc3339(value) -> str:
    """Convert a YAML-parsed datetime or string to an RFC 3339 string with Z suffix."""
    if isinstance(value, datetime.datetime):
        if value.tzinfo is not None:
            # Convert to UTC then format with Z.
            utc = value.astimezone(datetime.timezone.utc)
            return utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, datetime.date):
        return value.strftime("%Y-%m-%dT00:00:00Z")
    return str(value)


def build_jsonld(front_matter: dict, source_path: str, source_hash: str) -> dict:
    """Build a JSON-LD document from parsed front-matter and provenance fields."""
    source_path_no_ext = source_path.rsplit(".", 1)[0]

    # keywords must be a list; allow a bare string as a single-element list.
    keywords = front_matter["keywords"]
    if isinstance(keywords, str):
        keywords = [keywords]
    elif not isinstance(keywords, list):
        keywords = list(keywords)

    doc = {
        "@context": {
            "@vocab": "https://schema.org/",
            "dc": "http://purl.org/dc/terms/",
            "bsc": BSC_NAMESPACE,
        },
        "@type": "DigitalDocument",
        "@id": f"bsc:{source_path_no_ext}",
        "dc:title": front_matter["title"],
        "dc:description": front_matter["description"],
        "dc:subject": keywords,
        "dc:created": _to_rfc3339(front_matter["created"]),
        "dc:modified": _to_rfc3339(front_matter["updated"]),
        "dc:contributor": front_matter["validated-by"],
        "contentStatus": front_matter["status"],
        "bsc:domain": front_matter["domain"],
        "bsc:validated_on": _to_rfc3339(front_matter["validated-on"]) if front_matter.get("validated-on") is not None else None,
        "bsc:source_path": source_path,
        "bsc:source_hash": source_hash,
        "bsc:schema_version": SCHEMA_VERSION,
    }
    return doc


def _validate_sidecar(doc: dict) -> None:
    """Validate the generated JSON-LD document before writing. Raises ValueError on failure."""
    # Confirm it serialises cleanly as JSON.
    try:
        json.dumps(doc)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"generated sidecar is not serialisable as JSON: {exc}") from exc

    if "@context" not in doc:
        raise ValueError("generated sidecar missing '@context'")
    if doc.get("@type") != "DigitalDocument":
        raise ValueError("generated sidecar '@type' must be 'DigitalDocument'")

    required_json_fields = [
        "dc:title",
        "dc:description",
        "dc:subject",
        "dc:created",
        "dc:modified",
        "dc:contributor",
        "contentStatus",
        "bsc:domain",
        "bsc:source_path",
        "bsc:source_hash",
    ]
    for field in required_json_fields:
        if field not in doc:
            raise ValueError(f"generated sidecar missing required field: {field}")
        if doc[field] is None:
            raise ValueError(f"generated sidecar has null value for required field: {field}")


def generate_sidecar(md_path: Path) -> Path:
    """Generate a .jsonld sidecar for a single .md file. Returns the sidecar path."""
    raw_bytes = md_path.read_bytes()
    source_hash = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()

    # Normalise source_path to a repo-root-relative POSIX path.
    # Use removeprefix (not lstrip) — lstrip("./") strips a character SET, not a
    # prefix string; it would silently corrupt paths like "../sibling/doc.md".
    # In production (build-index.yml), the workflow always passes repo-root-relative
    # paths (e.g. "docs/foo.md"). Absolute paths are the caller's responsibility.
    posix = Path(md_path).as_posix()
    source_path = posix.removeprefix("./")

    front_matter = parse_front_matter(md_path)
    doc = build_jsonld(front_matter, source_path, source_hash)
    _validate_sidecar(doc)

    sidecar_path = md_path.with_suffix(".jsonld")
    sidecar_path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return sidecar_path


def main() -> int:
    """Entry point. Returns exit code."""
    if len(sys.argv) < 2:
        print(
            "Usage: python3 scripts/generate_jsonld.py <file1.md> [<file2.md> ...]",
            file=sys.stderr,
        )
        return 1

    errors = []
    for arg in sys.argv[1:]:
        try:
            out = generate_sidecar(Path(arg))
            print(f"Generated: {out}")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR [{arg}]: {exc}", file=sys.stderr)
            errors.append(arg)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
