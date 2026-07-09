---
baseline_commit: NO_VCS
---

# Story 1.1: Define Context Document Schema and Front-Matter Requirements

Status: done

## Story

As a domain owner,
I want all context documents to have consistent, required metadata,
so that the system can validate completeness and enforce governance.

## Acceptance Criteria

1. Given a context document template with all required fields (`title`, `domain`, `description`, `keywords`, `created`, `updated`, `validated-by`, `validated-on`, `status`), when a document is submitted without any required field, then schema validation fails and reports which specific field is missing, by file name.
2. Documents with `status: deprecated` remain valid and retrievable while being explicitly flagged rather than rejected.

## Tasks / Subtasks

- [x] Define the canonical context-document metadata contract.
  - [x] Fix the required field list and required/optional semantics for every field named in FR1.
  - [x] Constrain `status` to `draft`, `active`, or `deprecated`.
  - [x] Resolve timestamp semantics consistently for this repo by documenting and enforcing RFC3339 UTC-compatible values for `created`, `updated`, and `validated-on`.
  - [x] Decide and document how `validated-on` behaves when a document has not yet been validated.
- [x] Add one machine-readable schema artifact that later workflows and runtime consumers can share.
  - [x] Prefer a single canonical schema definition rather than duplicating rules across prose and code.
  - [x] Keep the schema reusable by later PR validation work in Story 1.3.
- [x] Add a local-first validation entry point that enforces the schema contract against markdown context documents.
  - [x] Validate YAML front matter presence and required fields.
  - [x] Emit file-and-field-specific diagnostics rather than generic pass/fail output.
  - [x] Treat `deprecated` as a valid status and surface it as a flagged state, not a validation error.
- [x] Add focused fixtures/tests for the schema contract.
  - [x] One passing document containing every required field.
  - [x] Negative cases for missing required fields.
  - [x] Negative cases for malformed timestamps or invalid `status` values.
  - [x] A passing `deprecated` document proving it validates successfully.
- [x] Document developer-facing constraints for downstream stories.
  - [x] Make clear which pieces are intentionally deferred to Story 1.2 and Story 1.3.
  - [x] Preserve a single source of truth for schema rules so contributor docs and CI checks do not drift later.

## Dev Notes

### Story Intent

This story establishes the canonical metadata contract for context documents and the core validation behavior the rest of Epic 1 depends on. It is not the contribution experience story and it is not the PR workflow story.

### Business Value

- This is the governance foundation for the pilot. Without a stable metadata contract, later PR checks, retrieval freshness signals, and JSON-LD export behavior will drift.
- CAP-1 in the spec depends on this story: invalid metadata must fail with file-and-field diagnostics, while valid documents can proceed through the GitHub review path.

### In Scope

- Required metadata field definitions.
- Allowed values and date semantics.
- Machine-readable schema contract.
- Local validation behavior that proves the contract.
- Contract-level handling for deprecated documents.

### Out Of Scope

- `CONTRIBUTING.md` and contributor instructions belong to Story 1.2.
- `templates/context-document-template.md` belongs to Story 1.2.
- PR-triggered workflow wiring under `.github/workflows/` belongs to Story 1.3.
- `CODEOWNERS` work belongs to Story 1.4.
- JSON-LD sidecar generation belongs to Epic 2, not this story.

### Architecture Compliance

- Follow the write/read split from the architecture spine: this story defines a schema contract and local validation core for the write path; it must not couple implementation to the retrieval API runtime.
- Treat the schema as a producer-consumer contract, not a loose documentation note. Later CI and downstream consumers should be able to reuse the same contract without reinterpretation.
- Preserve markdown documents as the only editable source of truth. Derived validation artifacts are supportive, not an alternative authoring surface.
- Keep the implementation local-first and reusable in GitHub-compatible automation later.

### Technical Requirements

- Required front-matter fields: `title`, `domain`, `description`, `keywords`, `created`, `updated`, `validated-by`, `validated-on`, `status`.
- `status` must accept `draft`, `active`, `deprecated` only.
- Missing required fields must produce diagnostics that identify both the file and the specific field.
- `deprecated` must validate successfully and remain eligible for downstream retrieval, where later stories can flag it explicitly.
- Date handling must be unambiguous. The PRD says ISO 8601; the architecture conventions tighten timestamps to RFC3339 UTC. Implement one consistent rule and document it so later stories do not fork behavior.
- Keep metadata naming aligned with the standards direction in the addendum: markdown + YAML front matter, Dublin Core naming where applicable, JSON-LD/schema.org compatibility later.

### Recommended Implementation Shape

Because the repo has no existing implementation surface for schema validation yet, prefer the smallest coherent foundation that later stories can reuse:

- one canonical machine-readable schema artifact;
- one local validation command or script that checks markdown files against that schema;
- one focused test/fixture area covering valid, invalid, and deprecated cases.

Avoid scattering the rules across multiple partially overlapping files.

### Likely Files To Create

The exact paths are not fixed yet in the repo, but the implementation should stay minimal and reusable. Favor a shape similar to this:

- a dedicated schema artifact in a small top-level validation or schema location;
- a local validation helper in an existing script/tooling area such as `_bmad/scripts/` if reuse is straightforward;
- fixtures/tests in a dedicated validation test area;
- only minimal sample markdown content needed to prove validation behavior.

Do not create `.github/workflows/pr-validate.yml`, `CONTRIBUTING.md`, `templates/context-document-template.md`, or `CODEOWNERS` in this story unless the implementation absolutely requires a placeholder for test fixtures. If a placeholder is necessary, keep it isolated from the production path and document why.

### Current Repository State

- `docs/` exists but is empty.
- `.github/` exists but only contains `agents/`; no workflow files exist yet.
- No `CONTRIBUTING.md` file exists.
- No `templates/context-document-template.md` exists.
- No `CODEOWNERS` file exists.
- No git repository metadata is available in this workspace, so do not rely on recent commit history.

### UX And Diagnostics Requirements

- Validation output must be actionable, grouped by file and then field when multiple failures exist.
- Blocking messages must remain understandable in plain markdown/plain text, not only through color or UI treatment.
- Deprecated content is visible and valid. Do not encode deprecated as equivalent to invalid.
- Keep diagnostics low-drama and operational in tone.

### Testing Requirements

- Add at least one passing fixture with all required fields populated.
- Add a failing fixture for each missing required field, or an equivalent coverage pattern that still proves field-specific diagnostics.
- Add coverage for malformed date values and invalid status values.
- Add explicit proof that a `deprecated` document passes validation.
- Keep tests local and contract-focused. End-to-end PR workflow tests are for Story 1.3.

### Dependencies And Sequencing

- Story 1.2 depends on this story's schema contract to build a valid template and contributor guidance.
- Story 1.3 depends on this story's validation core to wire the PR check without duplicating rules.
- If you need to choose between speed and reuse, optimize for a single validation contract that Stories 1.2 and 1.3 can both consume.

### Pitfalls To Avoid

- Do not bundle contributor guidance and template authoring into this story.
- Do not jump ahead to full GitHub Actions workflow wiring.
- Do not reject `deprecated` documents.
- Do not leave timestamp rules vague.
- Do not implement schema rules only in prose; keep a machine-usable contract.
- Do not hard-code assumptions for multiple domains; Phase 1 scope is User Authentication only.
- Do not produce generic validation failures when the requirement is file-and-field-specific diagnostics.

### Project Structure Notes

- Align any new validation surface with the architecture spine's index-as-artifact and source-canonicality rules.
- Prefer the smallest new directory footprint needed to establish a reusable contract.
- If you introduce a new schema directory, keep naming deterministic and future-friendly so later runtime and CI consumers can reuse it without migration churn.

### References

- [Source: _bmad-output/planning-artifacts/epics.md - Story 1.1 and Story 1.3]
- [Source: _bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/prd.md - FR-1, FR-3, FR-9]
- [Source: _bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/addendum.md - standards posture and local-first pilot]
- [Source: _bmad-output/planning-artifacts/architecture/architecture-bmadSharedContext-2026-07-08/ARCHITECTURE-SPINE.md - AD-1, AD-4, AD-7, consistency conventions]
- [Source: _bmad-output/planning-artifacts/ux-designs/ux-bmadSharedContext-2026-07-07/EXPERIENCE.md - schema error list, conflict/deprecated state treatment, keyboard-first behavior]
- [Source: _bmad-output/specs/spec-bmadSharedContext/SPEC.md - CAP-1, constraints, User Authentication scope]

## Dev Agent Record

### Agent Model Used

GPT-5.3-Codex

### Debug Log References

- No prior implementation story exists for this epic.
- No git history is available in this workspace.
- Baseline capture attempted with `git rev-parse HEAD`; repository has no available `HEAD`, so `baseline_commit` set to `NO_VCS`.
- Local validation suite run via `python3 -m unittest discover _bmad/scripts/tests` (11 tests passing after closeout hardening).
- Post-review hardening applied: explicit invalid-path diagnostics and actionable keyword-style consistency diagnostics.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- This story is the first story in Epic 1, so the epic should move to `in-progress` in sprint tracking.
- No `project-context.md` file was present in the workspace during story creation.
- Implemented canonical schema at `_bmad/schemas/context_document_metadata.schema.json` with required fields, `status` enum, and RFC3339 UTC timestamp constraints.
- Implemented local-first validation entry point `_bmad/scripts/validate_context_metadata.py` with file-and-field diagnostics for missing/invalid metadata and explicit deprecated-document flagging.
- Added fixtures for valid, missing-field, invalid-status, malformed-timestamp, validated-on-null, and deprecated-valid cases.
- Added contract tests in `_bmad/scripts/tests/test_validate_context_metadata.py`; all six tests pass.
- Added follow-up contract coverage for flow-style keyword diagnostics and explicit missing-path input diagnostics; suite now has eight passing tests.
- Carried the YAML consistency convention into the canonical schema using explicit authoring-convention metadata while keeping extension flexibility (`additionalProperties: true`).
- Added validator helper hints: when `keywords` style fails, output now points directly to schema `x-bmad-authoring-conventions` keys for fast correction.
- Hardened the dependency-free front-matter parser to report unsupported YAML constructs explicitly instead of silently mis-parsing them.
- Added file-level diagnostics for unreadable or non-UTF-8 markdown inputs so validation failures remain structured and actionable.
- Expanded regression coverage for multiline YAML block scalars, flow-style keyword authoring violations, and invalid UTF-8 inputs; suite now has 11 passing tests.

### File List

- _bmad-output/implementation-artifacts/1-1-define-context-document-schema-and-front-matter-requirements.md
- _bmad/schemas/context_document_metadata.schema.json
- _bmad/scripts/validate_context_metadata.py
- _bmad/scripts/tests/test_validate_context_metadata.py
- _bmad/scripts/tests/fixtures/context_docs/valid.md
- _bmad/scripts/tests/fixtures/context_docs/missing-title.md
- _bmad/scripts/tests/fixtures/context_docs/invalid-status.md
- _bmad/scripts/tests/fixtures/context_docs/invalid-created-timestamp.md
- _bmad/scripts/tests/fixtures/context_docs/validated-on-null.md
- _bmad/scripts/tests/fixtures/context_docs/deprecated-valid.md
- _bmad/scripts/tests/fixtures/context_docs/flow-style-keywords.md

## Change Log

- 2026-07-08: Added canonical metadata schema, local validation CLI, and focused contract fixtures/tests for required fields, timestamp rules, and deprecated status handling.
- 2026-07-08: Addressed code-review findings by improving input-path failure messages and enforcing consistent `keywords` block-list YAML style with actionable diagnostics.
- 2026-07-08: Added schema-level authoring convention metadata to carry forward the `keywords` block-list YAML rule for downstream consumers and documentation.
- 2026-07-08: Added targeted validator helper output linking `keywords` style failures to schema convention metadata (`x-bmad-authoring-conventions`).
- 2026-07-08: Hardened parser/runtime error handling to avoid silent YAML misparses and to report unreadable or invalid-UTF-8 markdown files as structured diagnostics.
