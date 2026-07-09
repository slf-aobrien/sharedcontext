---
baseline_commit: NO_VCS
---

# Story 1.2: Create Contribution Template and Guidance

Status: done

## Story

As a new contributor,
I want a clear template and instructions,
so that I can author valid context documents without external help.

## Acceptance Criteria

1. Given `/templates/context-document-template.md` and `CONTRIBUTING.md` are present in the repository, when a contributor follows only those documents to create a new context document, then the resulting document passes schema validation without requiring extra undocumented steps.
2. The template includes inline instructions and representative examples for each required front-matter field.

## Tasks / Subtasks

- [x] Create the contributor-facing authoring guide.
  - [x] Add `CONTRIBUTING.md` at the repository root with a short end-to-end contribution path for Phase 1.
  - [x] Explain where context documents live for the pilot and keep scope explicit to the User Authentication domain.
  - [x] Include copy-ready command examples that use the local-first validator entry point from Story 1.1.
  - [x] Explain how contributors should interpret blocking validation output and correct file-and-field issues.
- [x] Create the canonical context document template.
  - [x] Add `templates/context-document-template.md` with every required front-matter field pre-populated.
  - [x] Include inline instruction text and one representative example for each required metadata field.
  - [x] Keep `keywords` shown in block-list YAML style to match the schema authoring convention.
  - [x] Show `validated-on: null` for documents that have not yet been validated.
- [x] Keep template and guidance aligned to the canonical schema contract.
  - [x] Reuse Story 1.1 field names and semantics exactly; do not restate altered or simplified rules.
  - [x] Point contributors to the validator script and schema as the source of truth for enforcement.
  - [x] Make clear that markdown documents remain the only editable source of truth and derived artifacts are not authoring inputs.
- [x] Add local-first proof that the contribution flow works.
  - [x] Use the new template to create at least one sample-valid document fixture or equivalent proof artifact.
  - [x] Validate that proof artifact with `python3 _bmad/scripts/validate_context_metadata.py ...`.
  - [x] Add or update focused tests if documentation-coupled examples or helper behaviors need coverage.
- [x] Document story boundaries clearly for downstream work.
  - [x] Defer PR workflow wiring to Story 1.3.
  - [x] Defer CODEOWNERS enforcement to Story 1.4.
  - [x] Do not introduce JSON-LD, retrieval API, or conflict-detection behavior in this story.

### Review Findings

- [x] [Review][Patch] `cp` command missing `mkdir -p` — Step 1 fails on a fresh repo where `docs/user-authentication/` doesn't exist [CONTRIBUTING.md]
- [x] [Review][Patch] Template `created`/`updated` use hardcoded `2026-01-01T00:00:00Z` instead of `<placeholder>` style — passes validation silently [templates/context-document-template.md]
- [x] [Review][Patch] `validated-on` error row absent from error table — actual validator message is "must be null or RFC3339 UTC…" with no matching entry [CONTRIBUTING.md]
- [x] [Review][Patch] Overview says JSON-LD sidecars "are generated" (present tense) — contradicts Out of Scope section for Epic 2 [CONTRIBUTING.md]
- [x] [Review][Patch] Step 2 example `validated-by: your-name-or-email` uses no angle brackets — inconsistent with `<placeholder>` style used everywhere else [CONTRIBUTING.md]
- [x] [Review][Patch] "Delete all INSTRUCTIONS comments" instruction ambiguous — only one line labeled `# INSTRUCTIONS:`; per-field `# REQUIRED —` comment lines are unaddressed [templates/context-document-template.md]
- [x] [Review][Patch] Body placeholders (H1 `# <Your Document Title Here>`, HTML comment blocks) not covered by the deletion instruction [templates/context-document-template.md]
- [x] [Review][Defer] Unfilled `<…>` placeholder strings pass schema validation — validator cannot detect template tokens [templates/context-document-template.md] — deferred, pre-existing
- [x] [Review][Defer] Proof fixture `sample-valid-template-derived.md` not referenced in CONTRIBUTING.md [CONTRIBUTING.md] — deferred, pre-existing
- [x] [Review][Defer] No lifecycle guidance for `status` progression from `draft` to `active` [CONTRIBUTING.md] — deferred, pre-existing
- [x] [Review][Defer] `domain` value not enforced by validator — any string passes [templates/context-document-template.md] — deferred, pre-existing
- [x] [Review][Defer] `status: active` + `validated-on: null` cross-field inconsistency not enforced by schema — deferred, pre-existing
- [x] [Review][Defer] Empty/whitespace keyword item error messages absent from error table [CONTRIBUTING.md] — deferred, pre-existing
- [x] [Review][Defer] RFC3339 variant handling (fractional seconds, timezone offset) not specified [CONTRIBUTING.md] — deferred, pre-existing
- [x] [Review][Defer] `updated` before `created` passes validation — no temporal ordering constraint — deferred, pre-existing

## Dev Notes

### Story Intent

This story turns the schema contract from Story 1.1 into a usable contributor experience. The goal is not new validation rules; it is a self-sufficient contribution path that lets a first-time contributor produce a valid markdown context document with no hidden steps.

### Business Value

- FR-9 depends on this story: the pilot needs a contribution guide and template that make valid submissions possible without extra coaching.
- This is the usability bridge between the governance core in Story 1.1 and the PR automation in Story 1.3.
- If this story is weak, contributors will guess field semantics, drift from schema conventions, or rely on undocumented tribal knowledge.

### In Scope

- `CONTRIBUTING.md` authoring guidance for the Phase 1 repository workflow.
- `templates/context-document-template.md` with all required metadata fields.
- Inline instructions and examples for every required field.
- Local-first validation proof that the documented path is sufficient.

### Out Of Scope

- `.github/workflows/pr-validate.yml` and any CI wiring belong to Story 1.3.
- `CODEOWNERS` and protected-branch review routing belong to Story 1.4.
- JSON-LD sidecar generation belongs to Epic 2.
- Retrieval API, CLI, and runtime demo flows belong to Epic 3.

### Previous Story Learnings To Carry Forward

- The canonical metadata contract already exists at `_bmad/schemas/context_document_metadata.schema.json`; do not duplicate or reinterpret it in prose.
- The validator entry point already exists at `_bmad/scripts/validate_context_metadata.py`; guidance should route contributors through that local-first command instead of inventing a new validation path.
- `keywords` must be shown as block-list YAML, not flow-style YAML, or contributors will hit an avoidable authoring-convention error.
- `validated-on` may be `null` before review; the template should show that state explicitly so contributors do not invent placeholder timestamps.
- Unsupported YAML constructs now fail explicitly; documentation should steer contributors toward simple markdown front matter rather than advanced YAML features.

### Architecture Compliance

- Preserve document canonicality from AD-4: markdown files are the only editable source of truth.
- Preserve the write/read boundary from AD-1: this story concerns repository authoring guidance only, not retrieval runtime behavior.
- Keep schema guidance aligned to the producer-consumer contract from AD-7. The docs may explain the contract, but the schema remains normative.
- Keep the pilot local-first and GitHub-compatible. Commands and file paths should work on a developer machine without relying on hosted automation.

### UX And Documentation Requirements

- Follow the experience spine's plain-language operational tone. Blocking guidance should say exactly what to fix, not just that validation failed.
- Use the schema error list pattern conceptually: when showing examples of failures, group guidance by file then field.
- Use command block patterns with copyable commands and immediate explanation of any inline variables.
- Keep all required metadata visible in the template; do not hide instructions behind collapsible sections or secondary files.
- Ensure generated docs remain readable in markdown and narrow viewports; avoid wide tables when a flat list is clearer.
- Deprecated documents remain valid and visible; contributor guidance must not describe `deprecated` as invalid.

### Technical Requirements

- Required front-matter fields remain: `title`, `domain`, `description`, `keywords`, `created`, `updated`, `validated-by`, `validated-on`, `status`.
- Timestamps must match the Story 1.1 RFC3339 UTC rule: `YYYY-MM-DDTHH:MM:SSZ`.
- `status` values remain `draft`, `active`, or `deprecated` only.
- Guidance must explicitly point contributors at `_bmad/scripts/validate_context_metadata.py` for local verification.
- The template should stay consistent with the pilot domain posture: User Authentication is the only in-scope domain for Phase 1.
- The template and docs should avoid unsupported YAML features such as block scalars or inline mappings in front matter examples.

### Current Repository State

- `docs/project-context.md` exists and records the repo command policy: use `python3`, `find`, and `grep`; do not rely on `uv` or `rg`.
- `CONTRIBUTING.md` does not yet exist.
- `templates/` does not yet exist.
- `docs/` currently contains project context, but no authored domain content for contributors yet.
- `.github/` exists but no PR workflow files exist yet; do not reference workflow files as already present.

### Likely Files To Create Or Update

- `CONTRIBUTING.md`
- `templates/context-document-template.md`
- one small proof artifact or fixture demonstrating the template validates cleanly
- `_bmad/scripts/tests/test_validate_context_metadata.py` only if documentation-coupled validation behavior needs new coverage

### Testing Requirements

- Prove that a contributor following only `CONTRIBUTING.md` and the template can produce a document that passes validation.
- Prefer a local executable check using `python3 _bmad/scripts/validate_context_metadata.py` over a prose-only claim.
- If the story introduces any new example fixture or helper behavior, keep tests narrow and local-first.
- Re-run `python3 -m unittest discover _bmad/scripts/tests` if validator-facing tests are touched.

### Dependencies And Sequencing

- Depends on Story 1.1's schema and validator as the enforcement foundation.
- Must complete before Story 1.3 so the PR validation workflow can point contributors at an already-stable authoring path.
- Story 1.4 can assume this contributor path exists when CODEOWNERS begins routing reviews.

### Pitfalls To Avoid

- Do not redefine schema rules in prose that can drift from the canonical schema.
- Do not add hidden prerequisites outside the template and `CONTRIBUTING.md`.
- Do not document commands that violate repo policy (`uv`, `rg`).
- Do not imply multi-domain support in contributor examples; Phase 1 remains User Authentication only.
- Do not make the template so abstract that a first-time contributor still has to infer field meaning.

### References

- [Source: _bmad-output/planning-artifacts/epics.md - Story 1.2]
- [Source: _bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/prd.md - FR-1, FR-3, FR-9, MVP scope]
- [Source: _bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/addendum.md - standards posture, local-first pilot]
- [Source: _bmad-output/planning-artifacts/architecture/architecture-bmadSharedContext-2026-07-08/ARCHITECTURE-SPINE.md - AD-1, AD-4, AD-7]
- [Source: _bmad-output/planning-artifacts/ux-designs/ux-bmadSharedContext-2026-07-07/EXPERIENCE.md - command blocks, schema error list, plain-language blocking states]
- [Source: _bmad-output/implementation-artifacts/1-1-define-context-document-schema-and-front-matter-requirements.md - canonical field semantics, validator behavior, authoring-convention learnings]
- [Source: docs/project-context.md - repository command policy]

## Dev Agent Record

### Agent Model Used

GPT-5.4

### Debug Log References

- Story target auto-selected from `sprint-status.yaml` as the first backlog item after Story 1.1 completion.
- Previous story review learnings from Story 1.1 were carried forward to prevent schema drift and unsupported-YAML authoring guidance.
- No git history is available in this workspace, so `baseline_commit` remains `NO_VCS`.

### Completion Notes List

- Story file created with implementation guidance grounded in Story 1.1 schema/validator behavior.
- Story status set to `ready-for-dev` so implementation can begin without re-discovery.
- Implemented `CONTRIBUTING.md` at repo root with end-to-end Phase 1 contribution path, copyable validator commands, error interpretation table, and scope boundaries.
- Implemented `templates/context-document-template.md` with all required front-matter fields, inline instructions, and representative examples; keywords shown in block-list YAML; `validated-on: null` shown explicitly.
- Discovered and corrected schema alignment issue: `validated-by` requires `minLength: 1` (non-empty string); updated template, guide, and example block accordingly.
- Created proof fixture `_bmad/scripts/tests/fixtures/context_docs/sample-valid-template-derived.md`; validated `ok: true` against the schema.
- Full regression suite (11 tests) passes with no failures.

### File List

- _bmad-output/implementation-artifacts/1-2-create-contribution-template-and-guidance.md
- CONTRIBUTING.md
- templates/context-document-template.md
- _bmad/scripts/tests/fixtures/context_docs/sample-valid-template-derived.md

## Change Log

- 2026-07-08: Created Story 1.2 implementation context with contributor-guidance scope, schema-alignment guardrails, and local-first validation expectations.
- 2026-07-08: Implemented CONTRIBUTING.md, templates/context-document-template.md, and proof fixture; all tasks complete; 11/11 tests pass.