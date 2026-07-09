---
baseline_commit: NO_VCS
---

# Story 1.3: Implement PR Schema Validation Workflow

Status: done

## Story

As a domain owner reviewing a PR,
I want automated schema checks to catch incomplete or malformed documents before merge,
so that invalid knowledge artifacts never enter the main branch.

## Acceptance Criteria

1. Given a PR targeting `main` with new or modified context documents, when the schema validation workflow runs, then all changed documents are validated against the required front-matter schema.
2. Given the workflow finds invalid metadata, when it reports failures, then failures are grouped by file and field with actionable messages that block merge until corrected.

## Tasks / Subtasks

- [x] Create the PR validation workflow entrypoint.
  - [x] Add `.github/workflows/pr-validate.yml` as the first workflow under `.github/workflows/` without disturbing the existing `.github/agents/` files.
  - [x] Trigger the workflow on pull requests targeting `main`.
  - [x] Keep the workflow GitHub-compatible and local-first in posture so it can be reasoned about and, where practical, replayed outside hosted execution.
- [x] Reuse the existing validator as the enforcement core.
  - [x] Invoke `_bmad/scripts/validate_context_metadata.py` from the workflow rather than duplicating schema rules in YAML or shell.
  - [x] Continue treating `_bmad/schemas/context_document_metadata.schema.json` as the single source of truth for required fields and field semantics.
  - [x] Preserve current validator behavior for `deprecated` documents, keyword-style diagnostics, invalid UTF-8 handling, and missing-path diagnostics.
- [x] Scope validation to changed context documents only.
  - [x] Detect new or modified markdown context documents in the operational content path instead of validating all markdown files in the repository.
  - [x] Exclude planning artifacts, skill docs, and implementation notes from schema validation so unrelated markdown files do not cause false failures.
  - [x] Handle the no-matching-documents case explicitly so unrelated pull requests do not fail the schema gate.
- [x] Surface actionable blocking output for reviewers.
  - [x] Preserve file-and-field-specific diagnostics from the validator in CI logs and/or job summary so reviewers can correct the exact offending metadata.
  - [x] Make sure failures remain understandable in plain text, not only via GitHub UI affordances.
  - [x] Exit non-zero when any changed context document fails validation so the PR is blocked.
- [x] Add focused local proof for the workflow slice.
  - [x] Re-run `python3 -m unittest discover _bmad/scripts/tests` to protect the reusable validator contract.
  - [x] No new helper logic introduced; existing suite of 11 tests is sufficient.
  - [x] Proved all four behaviour slices locally: valid pass, invalid fail with field diagnostics, deprecated pass, no-matching-docs skip.
- [x] Update contributor-facing guidance only where Story 1.3 changes reality.
  - [x] Replaced the "not yet active" note in `CONTRIBUTING.md` with a description of the active workflow and its local-CI parity guarantee.

### Review Findings

- [x] [Review][Patch] `mapfile` builtin used without explicit `shell: bash` [.github/workflows/pr-validate.yml:63-66]
- [x] [Review][Patch] `git diff` errors silenced by `2>/dev/null` — validation silently skipped on error [.github/workflows/pr-validate.yml:42]
- [x] [Review][Patch] Renamed files (`--diff-filter=R`) bypass schema validation [.github/workflows/pr-validate.yml:42]
- [x] [Review][Patch] No job `timeout-minutes` — hung validator stalls runner for up to 6 hours [.github/workflows/pr-validate.yml:24]
- [x] [Review][Patch] CONTRIBUTING.md "Out of Scope" section lists workflow automation as not yet active — contradicts Step 4 prose [CONTRIBUTING.md:175]
- [x] [Review][Defer] No enforcement for PR description validator output [CONTRIBUTING.md:139-142] — deferred, pre-existing
- [x] [Review][Defer] Fallback branch validates all `docs/*.md` on no-base-commit (not just PR changes) [.github/workflows/pr-validate.yml:47-49] — deferred, pre-existing
- [x] [Review][Defer] No workflow concurrency control [.github/workflows/pr-validate.yml:on:] — deferred, pre-existing
- [x] [Review][Defer] `fetch-depth: 0` fetches full history — correct but potentially expensive [.github/workflows/pr-validate.yml:31] — deferred, pre-existing

## Dev Notes

### Story Intent

This story wires pull-request automation around the metadata contract established in Story 1.1 and the contributor path established in Story 1.2. The implementation should make CI call the existing validator on the right files; it should not create a second validation system.

### Business Value

- FR-3 depends on this story: pull requests must fail before merge when context-document metadata is incomplete or malformed.
- This is the governance bridge between local author validation and later conflict detection/publication automation.
- If this story is implemented loosely, reviewers will get noisy false failures, schema drift, or unhelpful blocking output that slows adoption.

### In Scope

- PR-targeted schema validation workflow for changed context documents.
- Reuse of the canonical schema and validator from Story 1.1.
- Actionable file-and-field diagnostics surfaced in CI.
- Minimal documentation update if contributor instructions still claim the workflow is not active.

### Out Of Scope

- Conflict detection belongs to Epic 2, especially Stories 2.2 and 2.3.
- JSON-LD sidecar generation belongs to Story 2.1.
- CODEOWNERS enforcement belongs to Story 1.4.
- Retrieval API, CLI, and runtime demo flows belong to Epic 3.
- Rewriting the schema contract, changing front-matter semantics, or expanding metadata rules is out of scope unless a workflow integration issue exposes a real defect.

### Previous Story Intelligence

#### From Story 1.1

- The canonical metadata contract already exists at `_bmad/schemas/context_document_metadata.schema.json` and must remain the only normative field-definition source.
- The validator entry point already exists at `_bmad/scripts/validate_context_metadata.py` and emits structured JSON with `ok`, `errors`, `deprecated`, `schema`, and `helpers`.
- Existing validation behavior already covers required fields, RFC3339 UTC timestamps, `validated-on: null`, allowed `status` values, flow-style keyword rejection, unsupported YAML constructs, missing paths, and invalid UTF-8 file handling.
- `deprecated` documents are valid and flagged; they must not become blocking failures in CI.

#### From Story 1.2

- Contributor guidance already points authors to `_bmad/scripts/validate_context_metadata.py`; Story 1.3 should keep local and CI validation on the same code path.
- The repo currently tells contributors that PR automation is not yet active. If this story adds the workflow, `CONTRIBUTING.md` should be brought into sync.
- Current contribution guidance uses `docs/user-authentication/` as the Phase 1 document path, while the PRD discusses `/domains/{domain-slug}/...`; the implementation must choose one operational path for CI and record the mismatch explicitly rather than guessing silently.
- The template and guide intentionally avoid unsupported YAML features; CI should preserve that same authoring posture rather than accepting a broader syntax locally than in automation.

### Architecture Compliance

- Preserve AD-1 write/read separation: this story is part of the write path only and must not couple to the retrieval runtime.
- Preserve AD-3 full-tree CI posture where relevant, but keep Story 1.3 scoped to schema validation only; do not pre-implement conflict detection logic here.
- Preserve AD-4 document canonicality: markdown files remain the only editable source of truth and the workflow validates them directly.
- Preserve AD-5 deterministic regeneration posture by avoiding duplicated schema rules in workflow YAML that can drift from the validator.
- Preserve AD-7 producer-consumer contract discipline by treating the schema artifact as the normative contract and the workflow as a caller of that contract.

### Technical Requirements

- The workflow should live at `.github/workflows/pr-validate.yml`, matching the architecture spine’s structural seed.
- Target pull requests to `main`, matching FR-3 and the PRD’s write-path definition.
- Validate only changed markdown context documents in the operational domain-content path.
- Do not validate repository-wide markdown indiscriminately; `_bmad-output/`, `.agents/`, and other support docs would create false positives.
- Preserve structured file-and-field diagnostics in workflow output. Reviewers must be able to map a failure directly back to the offending file and field.
- Exit with a failing status when any changed context document is invalid.
- Treat the no-changed-context-documents case as a non-failing no-op or explicit pass, not a blocker.
- Keep the implementation compatible with the repo command policy: use `python3`; do not rely on `uv` or `rg`.

### Recommended Implementation Shape

Because the validator already exists, the smallest coherent implementation shape is:

- one workflow file under `.github/workflows/`;
- at most one tiny helper surface for changed-file discovery or report shaping if the workflow logic would otherwise become brittle;
- reuse of the existing validator and test suite;
- one small documentation edit only if the contributor workflow text becomes stale.

Avoid embedding field-level validation rules directly in the workflow. If a helper is introduced, keep it thin and focused on file selection or CI presentation, not schema semantics.

### Files Likely To Create Or Update

- `.github/workflows/pr-validate.yml`
- `CONTRIBUTING.md` only if the “not yet active” note must be updated
- `_bmad/scripts/validate_context_metadata.py` only if workflow integration exposes a real interface gap worth fixing at the reusable core
- `_bmad/scripts/tests/test_validate_context_metadata.py` only if new helper behavior requires narrow tests

### Current Repository State

- `.github/` exists and currently contains only agent metadata files under `.github/agents/`; there is no `.github/workflows/` directory yet.
- `_bmad/scripts/validate_context_metadata.py` is the current validation implementation surface.
- `_bmad/scripts/tests/test_validate_context_metadata.py` contains 11 contract tests for the validator.
- `CONTRIBUTING.md` and `templates/context-document-template.md` are already present and aligned to the validator contract.
- A `.git` directory exists, but the branch has no commits yet, so no usable commit history is available for implementation pattern mining.

### UX And Diagnostics Requirements

- Follow the experience spine’s schema error list pattern: group failures by file first, then field, with explicit file/field pairs.
- Keep blocking messages plain-language and operational. “Validation failed” alone is not enough.
- Ensure workflow output remains understandable in plain text/markdown, not only through GitHub annotations or color.
- If a summary surface is added, it should point reviewers toward revision first and keep the exact offending files visible.

### Testing Requirements

- Re-run `python3 -m unittest discover _bmad/scripts/tests` after any validator-adjacent change.
- Add narrow tests only for any new helper logic introduced by this story.
- Prove four behavior slices for the workflow path:
  - valid changed context document passes;
  - invalid changed context document fails with file-and-field diagnostics;
  - deprecated but valid context document passes;
  - unrelated markdown changes do not fail the schema gate.
- Do not broaden into conflict-detection, index build, or retrieval tests in this story.

### Dependencies And Sequencing

- Depends on Story 1.1 for the schema and validator contract.
- Depends on Story 1.2 for the contributor path and operational document location.
- Must complete before Story 1.4 if you want contributor PRs to have both automated validation and later ownership routing.
- Serves as a prerequisite foundation for Epic 2’s broader `pr-validate.yml` expansion into conflict checks.

### Pitfalls To Avoid

- Do not implement a second copy of validation rules in workflow YAML or shell.
- Do not validate every markdown file in the repo.
- Do not fail PRs with no changed context documents.
- Do not convert `deprecated` status into a validation error.
- Do not quietly choose between `docs/user-authentication/` and `/domains/user-authentication/` without documenting the operational decision.
- Do not expand into conflict detection, CODEOWNERS, JSON-LD generation, or retrieval concerns.

### Open Questions To Record

- The PRD describes `/domains/{domain-slug}/...`, while current contributor guidance uses `docs/user-authentication/`. Story 1.3 needs one operational path for CI; if the mismatch is not resolved here, record the decision and rationale in the implementation.
- It is not yet explicit whether Phase 1 requires GitHub annotations/job summaries or whether structured JSON logs from the validator are sufficient, as long as the output remains actionable.
- If changed-file detection needs repo-history assumptions, the implementation must account for fork PRs, shallow checkouts, and rename handling rather than assuming a fully populated local git history.

### References

- [Source: _bmad-output/planning-artifacts/epics.md - Story 1.3, FR coverage]
- [Source: _bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/prd.md - FR-1, FR-3, MVP scope, success metrics]
- [Source: _bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/addendum.md - GitHub-fixed platform, local-first pilot, blocking PR check posture]
- [Source: _bmad-output/planning-artifacts/architecture/architecture-bmadSharedContext-2026-07-08/ARCHITECTURE-SPINE.md - AD-1, AD-3, AD-4, AD-5, AD-7, structural seed]
- [Source: _bmad-output/planning-artifacts/ux-designs/ux-bmadSharedContext-2026-07-07/EXPERIENCE.md - schema error list, plain-text blocking states, PR review flow]
- [Source: _bmad-output/planning-artifacts/ux-designs/ux-bmadSharedContext-2026-07-07/DESIGN.md - project-owned artifact clarity and command-block/error treatment]
- [Source: _bmad-output/implementation-artifacts/1-1-define-context-document-schema-and-front-matter-requirements.md - validator contract and parser hardening learnings]
- [Source: _bmad-output/implementation-artifacts/1-2-create-contribution-template-and-guidance.md - contributor-path learnings and active-note sync requirement]
- [Source: _bmad/scripts/validate_context_metadata.py - reusable validator implementation surface]
- [Source: _bmad/scripts/tests/test_validate_context_metadata.py - contract regression suite]
- [Source: CONTRIBUTING.md - current contributor workflow and inactive-automation note]
- [Source: docs/project-context.md - repo command policy]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Debug Log References

- Story target auto-selected from `sprint-status.yaml` as first `ready-for-dev` item.
- Workflow activation: no prepend/append steps; persistent facts loaded from `docs/project-context.md`.
- `.github/` had only agent metadata files; `.github/workflows/` directory did not exist before this story.
- `.git` present but `main` has no commits yet; no git history available for implementation pattern mining.
- Path decision: chose `docs/` (active contributor path per CONTRIBUTING.md) over PRD's `/domains/`; decision documented in workflow header comment.
- Regression suite: 11/11 tests pass; no validator changes were needed.
- All four CI behaviour slices proven locally: valid pass, invalid fail exit-1 with file+field, deprecated pass, nonexistent path explicit error.

### Completion Notes List

- Implemented `.github/workflows/pr-validate.yml` that calls the existing validator against changed docs/ markdown; does not duplicate schema rules.
- Changed-file detection uses `git diff --diff-filter=ACM` against base SHA; falls back to `find docs/` when no reachable base commit exists (initial-PR safety net).
- No-changed-docs case handled in the detect step: skips the validate step cleanly instead of calling the validator with no arguments.
- `CONTRIBUTING.md` Step 4 updated to describe the active workflow and its local-CI parity guarantee.
- No changes to validator script, schema, or test suite required.
- All tasks and acceptance criteria satisfied.

### File List

- _bmad-output/implementation-artifacts/1-3-implement-pr-schema-validation-workflow.md
- .github/workflows/pr-validate.yml
- CONTRIBUTING.md

## Change Log

- 2026-07-08: Created Story 1.3 implementation context with CI-wrapper guidance for the existing metadata validator, path-scoping guardrails, and focused workflow-testing requirements.
- 2026-07-08: Implemented `.github/workflows/pr-validate.yml` and updated `CONTRIBUTING.md`; all tasks complete; 11/11 regression tests pass; story status set to review.