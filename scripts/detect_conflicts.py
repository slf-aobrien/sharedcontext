#!/usr/bin/env python3
"""Detect contradictory claims between changed markdown docs and same-domain docs."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

import yaml

USAGE = (
    "Usage: python3 scripts/detect_conflicts.py <changed1.md> [<changed2.md> ...] "
    "[--docs-root <path>] [--threshold <0.0-1.0>] [--output <path>]"
)

NEGATION_TOKENS = {"not", "no", "never", "without"}

STOP_WORDS: frozenset = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "about",
    "it", "its", "this", "that", "these", "those", "and", "or", "but",
    "if", "then", "than", "so", "yet", "nor", "both", "either", "each",
    "all", "any", "few", "more", "most", "other", "some", "such", "own",
    "same", "very", "just", "my", "your", "our", "their",
    "he", "she", "we", "they", "you", "me", "him", "her", "us",
    "them", "who", "which", "there", "here", "when", "where", "why",
    "how", "what", "one", "two", "three", "first", "last", "also",
    "only", "up", "out", "after", "before", "while", "again",
})

OVERRIDE_MARKER_KEY = "conflict-override"
OVERRIDE_REASON_KEY = "override-reason"
OVERRIDE_REQUIRED_VALUE = "justified"


@dataclass(frozen=True)
class Document:
    path: Path
    relative_path: str
    domain: str
    body: str
    status: str = ""


class ConflictError(Exception):
    """Raised for script/runtime/configuration errors."""


def utc_now_rfc3339() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def evaluate_override_request(pr_body: str | None) -> dict:
    requested = False
    accepted = False
    reason = ""
    errors: list[str] = []

    if pr_body is None:
        return {"requested": False, "accepted": False, "reason": "", "errors": []}

    marker_values: list[str] = []
    reason_values: list[str] = []
    for line in pr_body.splitlines():
        if ":" not in line:
            continue
        key_raw, value_raw = line.split(":", 1)
        key = key_raw.strip().lower()
        value = value_raw.strip()
        if key == OVERRIDE_MARKER_KEY:
            marker_values.append(value.lower())
        elif key == OVERRIDE_REASON_KEY:
            reason_values.append(value)

    if not marker_values:
        return {"requested": False, "accepted": False, "reason": "", "errors": []}

    requested = True
    if any(value != OVERRIDE_REQUIRED_VALUE for value in marker_values):
        errors.append(
            "Malformed conflict-override marker. Expected 'conflict-override: justified'."
        )

    reason = reason_values[-1].strip() if reason_values else ""
    if reason == "":
        errors.append(
            "Override requires a non-empty override-reason field in PR description."
        )

    if not errors:
        accepted = True

    return {
        "requested": requested,
        "accepted": accepted,
        "reason": reason,
        "errors": errors,
    }


def load_codeowners_rules(codeowners_path: Path) -> list[tuple[str, list[str]]]:
    try:
        text = codeowners_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConflictError(f"Unable to read CODEOWNERS file {codeowners_path}: {exc}") from exc

    rules: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        row = line.split("#", 1)[0].strip()
        if not row:
            continue
        parts = row.split()
        if len(parts) < 2:
            continue
        pattern = parts[0]
        owners = [owner.lstrip("@").lower() for owner in parts[1:] if owner.startswith("@")]
        if owners:
            rules.append((pattern, owners))
    return rules


def codeowners_match(path: str, pattern: str) -> bool:
    if pattern == "*":
        return True
    if pattern.endswith("/"):
        return path.startswith(pattern)
    if any(ch in pattern for ch in ("*", "?", "[")):
        return fnmatch(path, pattern) or fnmatch(path, pattern.lstrip("/"))
    return path == pattern


def owners_for_path(path: str, rules: list[tuple[str, list[str]]]) -> list[str]:
    owners: list[str] = []
    for pattern, rule_owners in rules:
        if codeowners_match(path, pattern):
            owners = rule_owners
    return owners


def is_actor_authorized_for_domains(
    actor: str,
    domains: set[str],
    codeowners_path: Path,
) -> tuple[bool, dict[str, list[str]]]:
    rules = load_codeowners_rules(codeowners_path)
    normalized_actor = actor.lstrip("@").strip().lower()
    owner_details: dict[str, list[str]] = {}
    authorized_domains = 0

    for domain in sorted(domains):
        domain_path = f"docs/{domain}/"
        owners = owners_for_path(domain_path, rules)
        if not owners:
            owners = owners_for_path("*", rules)
        unique_owners = sorted(set(owners))
        owner_details[domain] = unique_owners
        if normalized_actor in unique_owners:
            authorized_domains += 1

    return authorized_domains > 0, owner_details


def build_override_audit_record(
    pr_number: str,
    repository: str,
    actor: str,
    affected_domains: list[str],
    affected_files: list[str],
    conflicts: list[dict],
    reason: str,
    timestamp_utc: str | None = None,
) -> dict:
    return {
        "pr_number": str(pr_number),
        "repository": repository,
        "actor": actor,
        "timestamp_utc": timestamp_utc or utc_now_rfc3339(),
        "affected_domains": sorted(set(affected_domains)),
        "affected_files": sorted(set(affected_files)),
        "conflict_summary": [c.get("summary", "") for c in conflicts],
        "reason": reason,
    }


def write_override_audit_record(
    audit_root: Path,
    record: dict,
    pr_number: str,
    run_id: str,
    run_attempt: str,
) -> Path:
    audit_root.mkdir(parents=True, exist_ok=True)
    filename = f"pr-{pr_number}-run-{run_id}-attempt-{run_attempt}.json"
    output_path = audit_root / filename
    with output_path.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)
        handle.write("\n")
    return output_path


def read_text_file(path: str | None) -> str | None:
    if not path:
        return None
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ConflictError(f"Unable to read text file {path}: {exc}") from exc


def split_front_matter(text: str) -> tuple[str | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text

    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[1:idx]), "\n".join(lines[idx + 1 :])

    return None, text


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def parse_threshold(raw: str | None) -> float:
    value = "0.50" if raw is None or raw.strip() == "" else raw.strip()
    try:
        threshold = float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid CONFLICT_THRESHOLD '{value}': must be numeric") from exc

    if math.isnan(threshold):
        raise ValueError(f"Invalid CONFLICT_THRESHOLD '{value}': must be a finite number")

    if threshold < 0.0 or threshold > 1.0:
        raise ValueError(
            f"Invalid CONFLICT_THRESHOLD '{value}': must satisfy 0.0 <= threshold <= 1.0"
        )
    return threshold


def rel_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def parse_document(path: Path, repo_root: Path) -> Document:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConflictError(f"Unable to read file {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ConflictError(f"File is not valid UTF-8: {path}") from exc

    fm_text, body = split_front_matter(text)
    if fm_text is None:
        raise ConflictError(f"Missing YAML front matter in {path}")

    try:
        metadata = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        raise ConflictError(f"Malformed YAML front matter in {path}: {exc}") from exc

    if not isinstance(metadata, dict):
        raise ConflictError(f"Front matter must be a mapping in {path}")

    domain = metadata.get("domain")
    if not isinstance(domain, str) or domain.strip() == "":
        raise ConflictError(f"Missing or invalid 'domain' in {path}")

    status_raw = metadata.get("status", "")
    status = status_raw.strip() if isinstance(status_raw, str) else ""

    return Document(
        path=path,
        relative_path=rel_path(path, repo_root),
        domain=domain.strip(),
        body=normalize_text(body),
        status=status,
    )


def tokenize_meaningful(text: str) -> set[str]:
    """Tokenize text, filtering stop words and single-character tokens."""
    return {
        t for t in re.findall(r"[a-z0-9]+", text.lower())
        if t not in STOP_WORDS and len(t) > 1
    }


def split_sentences(text: str) -> list[str]:
    """Split text into sentences on punctuation boundaries."""
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def contradiction_score(left: Document, right: Document) -> tuple[float, str] | None:
    """Return (Jaccard score, summary) for the best negation-contradicting sentence pair,
    or None if no qualifying pair exists."""
    left_sentences = split_sentences(left.body)
    right_sentences = split_sentences(right.body)

    best_score = 0.0
    best_shared: set[str] = set()

    for ls in left_sentences:
        ls_tokens = tokenize_meaningful(ls)
        ls_neg = any(token in ls_tokens for token in NEGATION_TOKENS)
        if not ls_tokens:
            continue
        for rs in right_sentences:
            rs_tokens = tokenize_meaningful(rs)
            rs_neg = any(token in rs_tokens for token in NEGATION_TOKENS)
            if not rs_tokens:
                continue

            # Only score sentence pairs where exactly one side carries negation
            if ls_neg == rs_neg:
                continue

            shared = ls_tokens.intersection(rs_tokens)
            if len(shared) < 3:
                continue

            union = ls_tokens.union(rs_tokens)
            score = len(shared) / len(union)
            if score > best_score:
                best_score = score
                best_shared = shared

    if best_score == 0.0:
        return None

    summary = (
        f"Potential contradiction: {left.relative_path} and {right.relative_path} "
        f"share key terms ({', '.join(sorted(best_shared))}) but differ by negation in related sentences."
    )
    return best_score, summary


def collect_same_domain_targets(changed_doc: Document, docs_root: Path, repo_root: Path) -> list[Document]:
    targets: list[Document] = []
    for path in sorted(docs_root.rglob("*.md")):
        if not path.is_file():
            continue
        if path.resolve() == changed_doc.path.resolve():
            continue

        try:
            candidate = parse_document(path, repo_root)
        except ConflictError:
            # Malformed comparison targets should not mask valid conflicts.
            continue
        if candidate.domain == changed_doc.domain:
            if candidate.status in ("deprecated", "archived"):
                continue
            targets.append(candidate)
    return targets


def detect_conflicts(changed_files: list[Path], docs_root: Path, threshold: float) -> dict:
    repo_root = Path.cwd()
    changed_docs: list[Document] = []
    errors: list[dict] = []

    for path in sorted(changed_files):
        try:
            changed_docs.append(parse_document(path, repo_root))
        except ConflictError as exc:
            errors.append({"file": rel_path(path, repo_root), "message": str(exc)})

    conflicts: list[dict] = []
    by_changed: dict[str, list[dict]] = {}
    seen_pairs: set[tuple[str, str]] = set()
    changed_paths = {doc.relative_path for doc in changed_docs}

    for changed_doc in changed_docs:
        targets = collect_same_domain_targets(changed_doc, docs_root, repo_root)

        for target in targets:
            left_file, right_file = sorted([changed_doc.relative_path, target.relative_path])
            pair_key = (left_file, right_file)
            if pair_key in seen_pairs:
                continue

            scored = contradiction_score(changed_doc, target)
            if scored is None:
                continue

            score, summary = scored
            if score < threshold:
                continue

            seen_pairs.add(pair_key)
            conflict = {
                "domain": changed_doc.domain,
                "left_file": left_file,
                "right_file": right_file,
                "score": round(score, 4),
                "summary": summary,
            }
            conflicts.append(conflict)
            by_changed.setdefault(changed_doc.relative_path, []).append(conflict)
            # Also group under the target when it is itself a changed file
            if target.relative_path in changed_paths:
                by_changed.setdefault(target.relative_path, []).append(conflict)

    conflicts.sort(key=lambda item: (item["left_file"], item["right_file"], item["score"]))
    for key in sorted(by_changed):
        by_changed[key] = sorted(
            by_changed[key],
            key=lambda item: (item["left_file"], item["right_file"], item["score"]),
        )

    return {
        "threshold": threshold,
        "changed_files": [doc.relative_path for doc in sorted(changed_docs, key=lambda d: d.relative_path)],
        "changed_domains": sorted({doc.domain for doc in changed_docs}),
        "conflicts": conflicts,
        "errors": errors,
        "grouped_by_changed": by_changed,
    }


def print_human_report(report: dict) -> None:
    if report["errors"]:
        print("Conflict detection errors:", file=sys.stderr)
        for error in report["errors"]:
            print(f"  - {error['file']}: {error['message']}", file=sys.stderr)

    if not report["conflicts"]:
        print("No unresolved conflicts detected.")
        return

    print("Unresolved conflicts detected:")
    for changed_file in sorted(report["grouped_by_changed"]):
        print(f"Changed source: {changed_file}")
        for conflict in report["grouped_by_changed"][changed_file]:
            print(
                "  -> "
                f"{conflict['left_file']} <-> {conflict['right_file']} "
                f"(domain={conflict['domain']}, score={conflict['score']:.2f})"
            )
            print(f"     summary: {conflict['summary']}")


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("changed_files", nargs="*")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--threshold", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--pr-body-file", default=None)
    parser.add_argument("--actor", default=None)
    parser.add_argument("--codeowners", default=".github/CODEOWNERS")
    parser.add_argument("--pr-number", default=None)
    parser.add_argument("--repository", default=None)
    parser.add_argument("--run-id", default="local")
    parser.add_argument("--run-attempt", default="1")
    parser.add_argument("--audit-root", default="docs/_audit/conflict-overrides")
    parser.add_argument("-h", "--help", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.help or not args.changed_files:
        print(USAGE, file=sys.stderr)
        return 2

    try:
        threshold = parse_threshold(args.threshold if args.threshold is not None else os.getenv("CONFLICT_THRESHOLD"))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    docs_root = Path(args.docs_root)
    if not docs_root.exists() or not docs_root.is_dir():
        print(f"Invalid docs root: {docs_root}", file=sys.stderr)
        return 2

    changed_files = [Path(item) for item in args.changed_files]
    report = detect_conflicts(changed_files=changed_files, docs_root=docs_root, threshold=threshold)

    try:
        pr_body = read_text_file(args.pr_body_file)
    except ConflictError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    override = evaluate_override_request(pr_body)

    output = (
        Path(args.output)
        if args.output
        else Path(os.getenv("CONFLICT_REPORT_PATH", "")).expanduser()
        if os.getenv("CONFLICT_REPORT_PATH")
        else Path(tempfile.gettempdir()) / "conflict-report.json"
    )

    try:
        write_report(output, report)
    except OSError as exc:
        print(f"Unable to write report file: {exc}", file=sys.stderr)
        return 2

    if override["requested"] and override["errors"]:
        print("Override validation failed:", file=sys.stderr)
        for message in override["errors"]:
            print(f"  - {message}", file=sys.stderr)
        print_human_report(report)
        print(f"Machine report written to: {output.as_posix()}")
        return 2

    if report["conflicts"] and override["requested"]:
        if report["errors"]:
            print(
                "Override rejected: unresolved document errors must be fixed before an override can be granted.",
                file=sys.stderr,
            )
            print_human_report(report)
            print(f"Machine report written to: {output.as_posix()}")
            return 2

        actor = (args.actor or "").strip()
        if actor == "":
            print("Override validation failed: actor is required for override authorization.", file=sys.stderr)
            print_human_report(report)
            print(f"Machine report written to: {output.as_posix()}")
            return 2

        try:
            authorized, owner_details = is_actor_authorized_for_domains(
                actor=actor,
                domains=set(report.get("changed_domains", [])),
                codeowners_path=Path(args.codeowners),
            )
        except ConflictError as exc:
            print(str(exc), file=sys.stderr)
            print_human_report(report)
            print(f"Machine report written to: {output.as_posix()}")
            return 2

        if not authorized:
            print(
                f"Override rejected: actor '{actor}' is not authorized for affected domains.",
                file=sys.stderr,
            )
            for domain in sorted(owner_details):
                owners = ", ".join(owner_details[domain]) if owner_details[domain] else "<none>"
                print(f"  - {domain}: allowed owners = {owners}", file=sys.stderr)
            print_human_report(report)
            print(f"Machine report written to: {output.as_posix()}")
            return 1

        pr_number = (args.pr_number or os.getenv("PR_NUMBER") or "unknown").strip()
        repository = (args.repository or os.getenv("GITHUB_REPOSITORY") or "unknown/unknown").strip()
        run_id = (args.run_id or os.getenv("GITHUB_RUN_ID") or "local").strip()
        run_attempt = (args.run_attempt or os.getenv("GITHUB_RUN_ATTEMPT") or "1").strip()

        audit_record = build_override_audit_record(
            pr_number=pr_number,
            repository=repository,
            actor=actor,
            affected_domains=report.get("changed_domains", []),
            affected_files=report.get("changed_files", []),
            conflicts=report["conflicts"],
            reason=override["reason"],
        )
        try:
            audit_file = write_override_audit_record(
                audit_root=Path(args.audit_root),
                record=audit_record,
                pr_number=pr_number,
                run_id=run_id,
                run_attempt=run_attempt,
            )
        except FileExistsError:
            print(
                "Override audit write blocked: audit record already exists for this PR/run metadata.",
                file=sys.stderr,
            )
            print_human_report(report)
            print(f"Machine report written to: {output.as_posix()}")
            return 2
        except OSError as exc:
            print(f"Unable to write override audit record: {exc}", file=sys.stderr)
            print_human_report(report)
            print(f"Machine report written to: {output.as_posix()}")
            return 2

        print("Override accepted: conflict block lifted for this PR.")
        print(f"Override audit record written to: {audit_file.as_posix()}")
        print(f"Machine report written to: {output.as_posix()}")
        return 0

    print_human_report(report)
    print(f"Machine report written to: {output.as_posix()}")

    if report["errors"]:
        return 2
    if report["conflicts"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
