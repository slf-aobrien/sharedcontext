---
baseline_commit: 125fd76
---

# Story 2.2: Implement Blocking Conflict Detection with Tunable Threshold

Status: done

## Story

As a domain owner,
I want conflicting claims detected during PR validation,
so that contradictory knowledge does not get merged unnoticed.

## Acceptance Criteria

1. Given a PR that introduces or changes context documents within a domain, when conflict detection executes against the full repository working tree, then any unresolved contradiction causes the PR check to fail and blocks merge.
2. Given conflict detection is configured, when maintainers adjust the configured threshold via repository variable, then the workflow behavior changes without code changes.
3. Given a conflict is detected, when the check fails, then the failure report names both source files and summarizes the contradictory claims.

## Tasks / Subtasks

- [x] Add conflict detection script and keep it docs-root scoped.
  - [x] Create `scripts/detect_conflicts.py` and keep it focused on changed docs under `docs/` plus same-domain comparison targets from the working tree.
  - [x] Accept changed markdown file paths as positional arguments; if none provided, print usage and exit non-zero.
  - [x] Parse YAML front-matter safely (`yaml.safe_load`), and read markdown body text for claim extraction.
  - [x] For each changed document, compare against other same-domain documents in the repository working tree (exclude self).
  - [x] Produce machine-readable output file for downstream workflow consumption (recommended: `conflict-report.json` in runner temp path) and a human-readable summary for job logs.
  - [x] Exit code contract: `0` for no unresolved conflicts, `1` for unresolved conflicts found, `2` for script/runtime/config errors.

- [x] Implement threshold tuning via repository variable.
  - [x] Read threshold from GitHub Actions `vars` context passed into script env (recommended variable name: `CONFLICT_THRESHOLD`).
  - [x] In workflow, set default when variable is unset (GitHub returns empty string for missing vars): use a safe default (recommended `0.70`) and validate numeric range `0.0 <= threshold <= 1.0`.
  - [x] Fail fast with explicit error if threshold is invalid (non-numeric or out of range) instead of silently coercing.

- [x] Integrate conflict detection as a blocking PR gate.
  - [x] Update `.github/workflows/pr-validate.yml` (do not create a separate workflow for this story).
  - [x] Keep existing schema validation behavior unchanged.
  - [x] Add/extend job step after changed-doc detection to run conflict detection only when `docs/*.md` changed.
  - [x] Ensure workflow fails when script reports unresolved conflicts; preserve PR-blocking semantics.
  - [x] Keep runtime shell blocks strict (`set -euo pipefail`) and explicit `shell: bash` for multi-line run blocks.

- [x] Add actionable failure reporting with both sources and claim summaries.
  - [x] Emit per-conflict entries containing: domain, left file path, right file path, similarity/score, and a concise contradiction summary.
  - [x] Print grouped report in logs by changed source file, then paired conflicting files.
  - [x] Ensure file paths are repo-relative and stable for deterministic output.

- [x] Add tests for detector behavior and threshold handling.
  - [x] Create `scripts/tests/test_detect_conflicts.py` with fixtures for: no-conflict pair, conflict pair, malformed front-matter, and cross-domain non-conflict.
  - [x] Test threshold behavior around boundary values (for example `0.69`, `0.70`, `0.71` for known fixtures).
  - [x] Test failure mode for invalid threshold input.
  - [x] Run `python3 -m unittest discover scripts/tests`.
  - [x] Re-run `python3 -m unittest discover _bmad/scripts/tests` as regression guard.

- [x] Capture pipeline safety and non-regression requirements.
  - [x] Do not modify `.github/workflows/build-index.yml` in this story except if absolutely required for shared helper reuse.
  - [x] Do not change sidecar schema contract fields from Story 2.1.
  - [x] Do not alter `_bmad/schemas/context_document_metadata.schema.json` for this story.

## Dev Notes

### Story Intent

Story 2.2 introduces the first contradiction-control gate in Epic 2 by making conflict detection a required pre-merge check in PR validation. The implementation must preserve Epic 1 schema validation behavior while adding a deterministic, tunable blocker for unresolved contradictions.

This story is foundational for:
- Story 2.3 (domain-owner override path and audit logging)
- Story 2.4 (deterministic publication with conflict-aware artifact state)
- Epic 3 conflict signaling requirements in retrieval responses

### Business and Architecture Context

- PRD FR-4 requires blocking conflict detection on PRs, threshold tuning without code changes, and source-specific reporting.
- AD-3 requires conflict detection against the full repository working tree in CI, not against stale derived artifacts.
- AD-4 and AD-5 require markdown documents to remain canonical source and derived outputs to be deterministic and provenance-aware.
- UX experience requirements demand explicit blocking language and plain-text actionable diagnostics, never silent failures.

### Existing Code to Update (Read Fully Before Editing)

- `.github/workflows/pr-validate.yml`
  - Current state: detects changed markdown files under `docs/`, runs schema validation, and includes CODEOWNERS placeholder check.
  - What this story changes: extend this workflow with a conflict-detection step/job that consumes changed docs and fails on unresolved conflicts.
  - Must preserve: existing schema validation semantics, docs-root scoping, and CODEOWNERS readiness check.

### Existing Code to Reuse (Do Not Reinvent)

- `_bmad/scripts/validate_context_metadata.py`
  - Reuse parsing/validation style patterns (safe YAML, file-level diagnostics).
- `scripts/generate_jsonld.py`
  - Reuse CLI behavior patterns: explicit usage on missing args, batch processing, explicit stderr errors, deterministic file/path handling.
- `scripts/tests/test_generate_jsonld.py`
  - Reuse unittest structure, fixture strategy, and edge-case coverage style.

### File Structure Requirements

- New production detector script under `scripts/`.
- New detector tests/fixtures under `scripts/tests/` and `scripts/tests/fixtures/`.
- Workflow update in-place at `.github/workflows/pr-validate.yml`.
- Keep all paths POSIX-style and repo-relative in emitted reports.

### Technical Requirements

- Use `python3`; do not introduce `uv`.
- Use safe parsing (`yaml.safe_load`) for all front-matter ingestion.
- Preserve deterministic behavior:
  - stable ordering of compared files and emitted conflicts
  - stable report formatting for predictable CI logs
- Use one threshold source of truth in workflow env and pass into script.
- Treat missing repository variable as empty string and apply explicit default in workflow expression or script parsing.

### Conflict Detection Behavior Guardrails

- Scope comparisons to same-domain documents only.
- Compare changed docs against full-tree same-domain docs to satisfy AD-3.
- Avoid false “self-conflicts” (same path on both sides).
- Handle malformed docs as actionable failures (do not silently skip).
- Include enough claim excerpt in summary for human triage, but keep summary concise and log-safe.

### Testing Requirements

- Unit tests must cover:
  - no conflict path (exit 0)
  - conflict path (exit 1)
  - malformed metadata path (error exit path)
  - threshold parsing and boundary behavior
  - deterministic output ordering
- CI command baseline:
  - `python3 -m unittest discover scripts/tests`
  - `python3 -m unittest discover _bmad/scripts/tests`

### Architecture Compliance Checklist

- AD-1: no runtime API coupling introduced in this story.
- AD-3: PR check compares against repository working tree, not derived index.
- AD-4: markdown remains canonical; no direct mutation of derived artifacts.
- AD-5: deterministic report outputs for reproducible CI behavior.

### Library and Framework Requirements

- Python standard library preferred.
- `pyyaml` is already used by repository tooling and accepted for front-matter parsing.
- Do not add heavyweight NLP dependencies in this story unless unavoidable; keep pilot implementation simple and testable.

### UX and Reporting Requirements

From UX requirements and experience spine:
- Blocking state must be explicit and understandable in plain text.
- Conflict callout must name both conflicting source files.
- Report must prioritize “revise source” path; override path belongs to Story 2.3.
- No-silent-failure: missing/invalid input must produce explicit actionable errors.

### Previous Story Intelligence (From Story 2.1)

- Keep shell scripts strict and explicit (`set -euo pipefail`, `shell: bash`) in workflow multi-line blocks.
- Use focused staging/changes in workflows; avoid touching unrelated files.
- Ensure generated/report paths are deterministic and relative.
- Preserve existing contracts (sidecar schema and workflow intent) to avoid downstream regressions.

### Git Intelligence Summary

Recent commits show story 2.1 validation and merge sequence already landed on mainline (`708312d`, `125fd76`). Use this as the baseline style:
- small, deterministic workflow edits
- explicit test coverage before completion
- fix-forward posture based on review findings

### Latest Technical Information

- GitHub Actions repository variables are exposed via `vars.*`; unset variable references resolve to empty string.
- Threshold wiring should therefore explicitly handle empty string defaults in workflow or script.
- PR workflows run on pull request merge branch by default; this is acceptable for repository-tree conflict checks but use explicit base/head SHAs already present in workflow for changed-file detection.

### Project Structure Notes

- Repo policy: use `python3`, `find`, and `grep`; do not use `uv` or `rg`.
- Story remains within Epic 2 pipeline safety scope and must not broaden to retrieval API/runtime changes.

### References

- `_bmad-output/planning-artifacts/epics.md` (Epic 2, Story 2.2)
- `_bmad-output/planning-artifacts/architecture/architecture-bmadSharedContext-2026-07-08/ARCHITECTURE-SPINE.md` (AD-1, AD-3, AD-4, AD-5)
- `_bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/prd.md` (FR-4)
- `_bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/addendum.md` (technical preferences)
- `_bmad-output/planning-artifacts/ux-designs/ux-bmadSharedContext-2026-07-07/EXPERIENCE.md` (blocking-state behavior)
- `_bmad-output/planning-artifacts/ux-designs/ux-bmadSharedContext-2026-07-07/DESIGN.md` (conflict callout behavior)
- `_bmad-output/implementation-artifacts/2-1-generate-json-ld-sidecars-on-merge.md` (implementation learnings)
- `https://docs.github.com/en/actions/learn-github-actions/variables`

## Dev Agent Record

### Agent Model Used

GPT-5.3-Codex

### Debug Log References

- `python3 -m unittest discover scripts/tests`
- `python3 -m unittest discover _bmad/scripts/tests`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story status set to ready-for-dev.
- Implemented `scripts/detect_conflicts.py` with deterministic same-domain comparison against repository working tree, safe front-matter parsing, and explicit exit-code contract (0/1/2).
- Added tunable threshold behavior (`CONFLICT_THRESHOLD`) with strict validation and explicit invalid-input failures.
- Integrated blocking conflict detection into PR validation workflow while preserving existing schema validation behavior.
- Added machine-readable report output and grouped human-readable logs with source file pairing and concise contradiction summary.
- Added detector tests and fixtures covering conflict/no-conflict, malformed front matter, cross-domain exclusion, threshold boundary behavior, invalid threshold handling, and deterministic ordering.
- Verified regression guard: existing `_bmad/scripts/tests` suite remains green.

### File List

- `_bmad-output/implementation-artifacts/2-2-implement-blocking-conflict-detection-with-tunable-threshold.md`
- `.github/workflows/pr-validate.yml`
- `scripts/detect_conflicts.py`
- `scripts/tests/test_detect_conflicts.py`
- `scripts/tests/fixtures/conflict-left.md`
- `scripts/tests/fixtures/conflict-right.md`
- `scripts/tests/fixtures/no-conflict.md`
- `scripts/tests/fixtures/cross-domain.md`
- `scripts/tests/fixtures/malformed-frontmatter.md`

### Change Log

- 2026-07-09: Implemented blocking conflict detection with tunable threshold, integrated PR gate wiring, and added deterministic reporting/test coverage.

### Review Findings

- [x] [Review][Patch] Hardcoded contradiction score — replace fixed `0.70` with computed Jaccard similarity (|shared| / |union| of meaningful tokens). Score will then be a real 0.0–1.0 value; update threshold boundary tests accordingly. [scripts/detect_conflicts.py:contradiction_score]
- [x] [Review][Patch] Negation heuristic fires on full-document presence, not same-sentence scope — add sentence-level scoping: split body on sentence boundaries (`re.split(r'[.!?]+')`), check negation mismatch only within sentences that share ≥3 meaningful (non-stop-word) tokens with a sentence in the other document. [scripts/detect_conflicts.py:contradiction_score]
- [x] [Review][Patch] Unit tests not enforced in CI — add a step to `pr-validate.yml` that runs `python3 -m unittest discover scripts/tests` and `python3 -m unittest discover _bmad/scripts/tests` on every PR (unconditional, not gated on docs-changed). [.github/workflows/pr-validate.yml]
- [x] [Review][Patch] Deprecated docs included in conflict comparisons — in `collect_same_domain_targets`, skip candidate documents whose front-matter `status` value is `deprecated` or `archived`; add a test fixture and test case to cover this exclusion. [scripts/detect_conflicts.py:collect_same_domain_targets]
- [x] [Review][Patch] `cat "${REPORT_PATH}"` blocked by set -euo pipefail — when Python exits 1 (conflicts found), bash exits immediately; the `echo "--- Conflict detection report ---"` and `cat "${REPORT_PATH}"` lines never run. JSON is not echoed to CI logs. Fix: capture exit code (`python3 … || CONFLICT_EXIT=$?`), then cat report, then `exit ${CONFLICT_EXIT}`. [.github/workflows/pr-validate.yml]
- [x] [Review][Patch] `CONFLICT_THRESHOLD_RAW` env var name mismatch — workflow injects `CONFLICT_THRESHOLD_RAW: ${{ vars.CONFLICT_THRESHOLD }}` but `scripts/detect_conflicts.py:main()` falls back to `os.getenv("CONFLICT_THRESHOLD")`. The env var names differ; the os.getenv path is dead code in CI (threshold IS passed correctly via `--threshold` arg, but the fallback is unreachable as intended). Fix: rename the workflow env key to `CONFLICT_THRESHOLD` to match the script's fallback, and remove the now-redundant `CONFLICT_THRESHOLD_RAW` indirection. [.github/workflows/pr-validate.yml + scripts/detect_conflicts.py]
- [x] [Review][Patch] `float("nan")` bypasses parse_threshold range validation — `NaN < 0.0` and `NaN > 1.0` are both `False` in Python, so `parse_threshold("nan")` returns `float("nan")`. Later, `0.70 < NaN` is `False` so no conflicts are ever suppressed — NaN silently acts as threshold 0.0 with no error. Fix: add `import math` and raise ValueError when `math.isnan(threshold)`. [scripts/detect_conflicts.py:parse_threshold]
- [x] [Review][Patch] `RUNNER_TEMP_DIR` empty string makes REPORT_PATH `/conflict-report.json` — if `runner.temp` resolves to `""` on a non-standard runner, `REPORT_PATH` becomes `/conflict-report.json` and the write attempt fails with permission denied. Fix: add `if [ -z "${RUNNER_TEMP_DIR}" ]; then RUNNER_TEMP_DIR="${TMPDIR:-/tmp}"; fi` guard before the REPORT_PATH assignment. [.github/workflows/pr-validate.yml]
- [x] [Review][Patch] `grouped_by_changed` incomplete when both conflicting docs are changed files — when two changed docs conflict with each other, `seen_pairs` causes the second iteration to skip the pair; the conflict appears only under the first doc in `grouped_by_changed`, not both. Fix: when both files are in `changed_docs`, append the conflict to both sides of `by_changed`. [scripts/detect_conflicts.py:detect_conflicts]
- [x] [Review][Defer] `/tmp` vs `$RUNNER_TEMP` inconsistency for changed-docs file list — `changed-context-docs.txt` uses hardcoded `/tmp/`; conflict output uses `$RUNNER_TEMP`. Pre-existing pattern established in story 2.1. [.github/workflows/pr-validate.yml] — deferred, pre-existing
- [x] [Review][Defer] `Path.cwd()` as repo root is invocation-directory-dependent — `detect_conflicts()` uses `Path.cwd()` as repo root; paths are wrong when script is not invoked from repo root. CI is always safe (runs from $GITHUB_WORKSPACE). Local dev caveat. [scripts/detect_conflicts.py:detect_conflicts] — deferred, pre-existing
- [x] [Review][Defer] Missing CODEOWNERS causes confusing grep error in CODEOWNERS check step — `grep -q '@OWNER_GITHUB_USERNAME' .github/CODEOWNERS` with `set -euo pipefail` gives "No such file" not an actionable message. Abnormal repo state; CODEOWNERS created in story 1.4. [.github/workflows/pr-validate.yml] — deferred, pre-existing
- [x] [Review][Defer] `--help` exits code 2 (non-standard POSIX) — standard convention is exit 0; this exits 2 like a usage error. No CI impact. [scripts/detect_conflicts.py:build_parser] — deferred, pre-existing
- [x] [Review][Defer] No `permissions:` block on workflow jobs — default repository permissions may be over-broad; all jobs should declare `contents: read`. Pre-existing pattern across all workflow jobs. [.github/workflows/pr-validate.yml] — deferred, pre-existing
