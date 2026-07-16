---
baseline_commit: 125fd76
---

# Story 2.3: Add Domain-Owner Conflict Override with Audit Logging

Status: done

## Story

As a domain owner,
I want to override false-positive conflicts with explicit justification,
so that teams can proceed when automated checks are over-sensitive while preserving accountability.

## Acceptance Criteria

1. Given a PR blocked by conflict detection, when a domain owner adds `conflict-override: justified` with rationale in the PR description, then the workflow permits merge subject to standard approvals.
2. Given an override is used, when the workflow processes the PR, then the override action is logged with PR reference, actor, timestamp, and reason for auditability.

## Tasks / Subtasks

- [x] Add override metadata parsing and validation.
  - [x] Extend conflict-check execution path to read PR body text and detect `conflict-override: justified` marker.
  - [x] Require a non-empty rationale field in the PR description when override is present.
  - [x] Treat malformed override payload as a blocking failure with actionable error output.

- [x] Enforce domain-owner authorization for override usage.
  - [x] Resolve changed domains from changed `docs/**/*.md` files in the PR.
  - [x] Validate that the override actor is an allowed owner for at least one affected domain from `CODEOWNERS` mappings.
  - [x] Block and report unauthorized override attempts with actor and affected domain information.

- [x] Integrate override behavior into PR validation workflow.
  - [x] Update `.github/workflows/pr-validate.yml` so unresolved conflicts still fail by default.
  - [x] Permit pass-through only when all override conditions are met (marker + rationale + authorized owner).
  - [x] Preserve existing schema validation and conflict detection behavior when no override is present.

- [x] Implement audit logging for approved overrides.
  - [x] Emit a deterministic audit record for each accepted override with: PR number, repo, actor, UTC timestamp, affected domains/files, conflict summary, and rationale.
  - [x] Persist logs under a committed audit path (recommended: `docs/_audit/conflict-overrides/`) with stable file naming keyed by PR and run metadata.
  - [x] Ensure log output is append-only and does not rewrite existing historical records.

- [x] Add tests for override and authorization paths.
  - [x] Add unit tests for override parsing and validation edge cases.
  - [x] Add tests for authorized and unauthorized owner scenarios using CODEOWNERS-like fixtures.
  - [x] Add tests confirming standard blocking behavior remains unchanged without override.
  - [x] Run `python3 -m unittest discover scripts/tests`.
  - [x] Re-run `python3 -m unittest discover _bmad/scripts/tests` as regression guard.

## Dev Notes

### Story Intent

Story 2.3 introduces a controlled exception path for false-positive conflicts while preserving governance guarantees. This is not a global bypass: merge remains blocked unless override intent is explicit, justified, and executed by an authorized domain owner.

### Business and Architecture Context

- FR4 requires both conflict blocking and a logged domain-owner override path.
- NFR8 requires overrides to be explicit, justified, and auditable.
- AD-3 and AD-4 constraints still apply: conflict checks execute against repository content, and markdown remains canonical source.
- UX constraints require plain-text, actionable blocking messages and no silent failures.

### Existing Code to Update (Read Fully Before Editing)

- `.github/workflows/pr-validate.yml`
  - Current state: blocks unresolved conflicts and reports contradiction context.
  - Story change: add override gating path and audit log publication while keeping default block semantics.

- `scripts/detect_conflicts.py`
  - Current state: computes conflicts and returns deterministic report/exit code.
  - Story change: support override decision input and expose override-aware outcome data to workflow logging.

### Design Guardrails

- Override must be explicit and scoped to the current PR only.
- Rationale must be captured verbatim and stored for later audit.
- Authorization should be derived from repository-owned ownership rules (CODEOWNERS), not ad-hoc allowlists.
- If any validation step fails (missing rationale, unauthorized actor, malformed marker), workflow remains blocking.

### Suggested Override Payload Format

Use a PR-description block in a deterministic form. Example:

```text
conflict-override: justified
override-reason: <plain-language rationale>
```

Both lines are required for override acceptance.

### Determinism and Logging Requirements

- Use stable field ordering and consistent timestamp format (UTC, RFC3339).
- Use repo-relative paths for all files listed in the audit record.
- Keep one record per accepted override decision event; no in-place mutation of existing records.

### Testing Requirements

- Validate successful override by authorized owner with complete rationale.
- Validate reject path for missing rationale.
- Validate reject path for unauthorized owner.
- Validate reject path for malformed override marker.
- Validate no-override path remains unchanged and blocking on conflicts.

### References

- `_bmad-output/planning-artifacts/epics.md` (Epic 2, Story 2.3)
- `_bmad-output/planning-artifacts/architecture/architecture-bmadSharedContext-2026-07-08/ARCHITECTURE-SPINE.md`
- `_bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/prd.md`
- `_bmad-output/implementation-artifacts/2-2-implement-blocking-conflict-detection-with-tunable-threshold.md`

## Dev Agent Record

### Agent Model Used

GPT-5.3-Codex

### Completion Notes List

- Story 2.3 artifact created and set to ready-for-dev.
- Acceptance criteria and task plan aligned with Epic 2 FR4/NFR8 requirements.
- Added override parsing and validation in `scripts/detect_conflicts.py` via `evaluate_override_request`, requiring explicit `conflict-override: justified` plus non-empty `override-reason`.
- Added CODEOWNERS-based domain-owner authorization (`is_actor_authorized_for_domains`) and blocking unauthorized override reporting with per-domain allowed-owner details.
- Added deterministic append-only override audit record creation under `docs/_audit/conflict-overrides/` using PR/run keyed filenames.
- Updated `.github/workflows/pr-validate.yml` to pass PR body, actor, PR/run metadata, and CODEOWNERS path to conflict detection while preserving default blocking behavior when no valid override is present.
- Added and passed unit tests for parsing, authorization, and append-only audit logging.
- Validation executed successfully:
  - `python3 -m unittest discover scripts/tests` (pass)
  - `python3 -m unittest discover _bmad/scripts/tests` (pass)

### File List

- `_bmad-output/implementation-artifacts/2-3-add-domain-owner-conflict-override-with-audit-logging.md`
- `scripts/detect_conflicts.py`
- `scripts/tests/test_detect_conflicts.py`
- `.github/workflows/pr-validate.yml`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `CONTRIBUTING.md`
- `_bmad-output/implementation-artifacts/deferred-work.md`

### Change Log

- 2026-07-14: Created story artifact for implementation kickoff.
- 2026-07-14: Implemented conflict override validation, CODEOWNERS authorization, workflow integration, append-only audit logging, and corresponding unit/regression tests; moved story to review.
- 2026-07-14: Applied code review patches — audit-record commit-and-push, errors-bypass fix in override acceptance, unconditional override syntax validation, CODEOWNERS glob matching, CLI-level override flow tests, and contributor documentation.

### Review Findings

- [x] [Review][Patch] Audit records are never persisted beyond the ephemeral CI runner — `write_override_audit_record()` writes to `docs/_audit/conflict-overrides/` on the GitHub Actions runner filesystem, but no step in `pr-validate.yml` commits, pushes, or uploads that file as an artifact. **Fixed:** added a "Commit override audit record" step that commits and pushes any new audit file back to the PR head branch using the `github-actions[bot]` identity, with `permissions: contents: write` added to the job and checkout pinned to the PR head SHA. [.github/workflows/pr-validate.yml, scripts/detect_conflicts.py:write_override_audit_record]
- [x] [Review][Patch] Accepted-override branch in `main()` never checks `report["errors"]` before granting pass-through. **Fixed:** the override-accepted branch now checks `report["errors"]` first and blocks (exit 2) if unresolved document errors remain, even with a valid authorized override. Covered by `test_cli_override_accepted_but_document_errors_present_still_blocks`. [scripts/detect_conflicts.py:main]
- [x] [Review][Patch] No test exercises the full override flow through `detect_conflicts.main()`. **Fixed:** added `TestOverrideCliFlow` with CLI-level tests for accepted (exit 0 + audit file written), unauthorized (exit 1), malformed-marker-without-conflicts (exit 2), and accepted-override-with-document-errors (exit 2) scenarios. [scripts/tests/test_detect_conflicts.py]
- [x] [Review][Patch] `codeowners_match()` only supports exact-path or trailing-slash-prefix matching (plus a bare `*`) — no glob/wildcard support. **Fixed:** added `fnmatch`-based glob matching for patterns containing wildcard characters (`*`, `?`, `[`), preserving existing exact/prefix behavior otherwise. [scripts/detect_conflicts.py:codeowners_match]
- [x] [Review][Patch] No contributor-facing documentation of the `conflict-override: justified` / `override-reason:` PR-description contract. **Fixed:** added an "Overriding a False-Positive Conflict (Domain Owners Only)" section to CONTRIBUTING.md documenting the required lines, authorization rule, and audit-logging behavior. [CONTRIBUTING.md]
- [x] [Review][Patch] Malformed/unauthorized override syntax is silently ignored when the PR has zero detected conflicts. **Fixed:** override syntax validation (`override["errors"]`) now runs unconditionally whenever the marker is present, regardless of whether conflicts exist. Covered by `test_cli_malformed_override_blocks_even_without_conflicts`. [scripts/detect_conflicts.py:main]
- [x] [Review][Defer] No `actions/setup-python`/PyYAML install step in CI — `detect_conflicts.py` imports `yaml`, but the workflow's `unit-tests` job has no `actions/setup-python` or `pip install` step; relies on the runner image having PyYAML preinstalled. Predates this story — the script and unit-tests job were introduced in Story 2.2. [.github/workflows/pr-validate.yml] — deferred, pre-existing
- [x] [Review][Defer] `CONFLICT_REPORT_PATH` env var branch in `main()`'s output-path resolution is dead code — the workflow never sets this variable, so the branch is unreachable and untested. Predates this story (introduced in Story 2.2). [scripts/detect_conflicts.py:main] — deferred, pre-existing
- [x] [Review][Defer] Threshold default `"0.50"` duplicated independently in the workflow bash fallback and `parse_threshold()` — the two defaults can drift out of sync if only one is updated. Predates this story (Story 2.2). [.github/workflows/pr-validate.yml, scripts/detect_conflicts.py:parse_threshold] — deferred, pre-existing
- [x] [Review][Defer] No `permissions:` block on workflow jobs — already identified and deferred as pre-existing in Story 2.2's review. [.github/workflows/pr-validate.yml] — deferred, pre-existing
- [x] [Review][Defer] `/tmp` vs `$RUNNER_TEMP_DIR` inconsistency for the changed-docs file list — already identified and deferred as pre-existing in Story 2.2's review. [.github/workflows/pr-validate.yml] — deferred, pre-existing
- [x] [Review][Defer] `cat "${REPORT_PATH}"` can mask the real exit code if the report write itself fails before reaching that line — same script/workflow pattern established in Story 2.2. [.github/workflows/pr-validate.yml] — deferred, pre-existing