---
baseline_commit: 125fd76
---

# Story 2.4: Build Deterministic Index/Graph Upsert Pipeline with Freshness SLA

Status: done

## Story

As an AI agent consumer,
I want recently merged knowledge to become queryable quickly and consistently,
so that agent outputs reflect the latest approved domain context.

## Acceptance Criteria

1. Given a successful merge to `main`, when index/graph publication runs, then document and concept relationships are upserted without duplicate derived state on reruns.
2. Given newly merged keywords, when publication completes, then they are retrievable through the API within five minutes.
3. Given a published snapshot, when artifacts are inspected, then they carry consistent provenance and shared build manifest identity for the snapshot.

## Tasks / Subtasks

- [x] Implement deterministic index artifact generation for full-snapshot publication.
  - [x] Create `scripts/build_index.py` to build a full `index/index.json` snapshot from `docs/**/*.md` and `docs/**/*.jsonld`.
  - [x] Parse markdown front-matter safely with `yaml.safe_load`; include only active, non-deprecated documents for default retrieval set while preserving explicit status metadata in output.
  - [x] Generate deterministic entity IDs and ordering (stable sort by `domain`, then `slug`, then `source_path`) to ensure reruns produce byte-identical output for unchanged inputs.
  - [x] Emit relationship records linking `document -> domain`, `document -> keywords`, and keyword back-references needed for retrieval filtering.
  - [x] Ensure rerunning on unchanged input yields no duplicate relationships and no non-deterministic ordering drift.

- [x] Add build-manifest and provenance contract outputs.
  - [x] Create `index/build-manifest.json` containing at least: `build_manifest_id`, `schema_version`, `generated_at_utc`, `source_commit`, `document_count`, and `keyword_count`.
  - [x] Stamp `build_manifest_id` into `index/index.json` and any other derived publication artifact produced in this story.
  - [x] Preserve provenance fields (`source_path`, `source_hash`) from sidecars when building index records so API consumers can trace each record back to canonical markdown.
  - [x] Fail publication if derived artifacts do not share one `build_manifest_id` value for the same run.

- [x] Extend merge-time publication workflow for sidecars + index + manifest.
  - [x] Update `.github/workflows/build-index.yml` (do not create a second post-merge pipeline).
  - [x] Keep existing sidecar generation behavior intact; run `scripts/generate_jsonld.py` first, then run `scripts/build_index.py`.
  - [x] Stage and commit both sidecars and index artifacts (`docs/**/*.jsonld`, `index/index.json`, `index/build-manifest.json`) in one commit per run when changes exist.
  - [x] Preserve deterministic publication semantics under concurrency (`cancel-in-progress: false`) and avoid partial publication.
  - [x] Ensure strict shell safety (`set -euo pipefail`) and explicit `shell: bash` for multi-line steps.

- [x] Implement freshness SLA signaling and verification hooks.
  - [x] Add `freshness_deadline_utc` or equivalent SLA marker to build manifest based on publish time + 5 minutes.
  - [x] Add workflow summary output showing publish time, freshness deadline, and published artifact counts.
  - [x] Add a lightweight verification script or test helper (for example `scripts/tests/test_build_index.py`) that validates freshness metadata format and manifest/index consistency.
  - [x] Prepare API-consumption contract fields now so Epic 3 retrieval endpoint can expose freshness without reworking publication schema.

- [x] Add unit and integration-style tests for deterministic publication.
  - [x] Create `scripts/tests/test_build_index.py` with fixture-driven tests.
  - [x] Add tests that verify deterministic ordering and byte-stable output across two consecutive runs on unchanged fixtures.
  - [x] Add tests that verify idempotent upsert semantics (no duplicate keyword/document relationships).
  - [x] Add tests that verify `build_manifest_id` consistency across all emitted artifacts.
  - [x] Add tests that verify provenance fields are present and correctly mapped from sidecars.
  - [x] Run `python3 -m unittest discover scripts/tests`.
  - [x] Re-run `python3 -m unittest discover _bmad/scripts/tests` as regression guard.

- [x] Keep architecture boundaries and non-goals intact.
  - [x] Do not implement or modify retrieval API endpoints in this story; produce publication artifacts and contracts only.
  - [x] Do not bypass PR conflict gates or schema gates established in stories 2.2 and 2.3.
  - [x] Do not introduce live graph database runtime dependency for Phase 1 correctness (index-as-artifact remains the acceptance authority).

### Review Findings

- [x] [Review][Patch] Deletion-only merges never trigger index rebuild, leaving stale/orphaned entries [.github/workflows/build-index.yml:60]
- [x] [Review][Patch] `status: draft` documents miscategorized as `active` in `active_document_ids` [scripts/build_index.py:184]
- [x] [Review][Patch] `parse_front_matter` doesn't reject null required fields, unlike `generate_jsonld.py` (AD-7 contract mismatch) [scripts/build_index.py:72]
- [x] [Review][Patch] Malformed `keywords` front-matter raises uncaught `TypeError` instead of documented per-document error handling [scripts/build_index.py:181]
- [x] [Review][Patch] Sidecar-sourced provenance (`source_hash`/`source_path`) trusted without verifying it matches current `.md` bytes [scripts/build_index.py:114]
- [x] [Review][Patch] "Publish build summary" step can block the atomic commit step on failure; also makes 5 redundant subprocess calls for one JSON file [.github/workflows/build-index.yml:104,130]
- [x] [Review][Patch] `write_artifacts()` writes `index.json` and `build-manifest.json` non-atomically; an interrupted run can leave mismatched artifacts on disk [scripts/build_index.py:372,376]
- [x] [Review][Defer] Freshness deadline stamped before push/rebase completes; SLA clock doesn't account for git-publish latency [scripts/build_index.py:222] — deferred, pre-existing architectural tension with git-commit-as-publish-mechanism
- [x] [Review][Defer] `_source_path_str` absolute-path fallback would break determinism, but unreachable with current fixed CLI invocation [scripts/build_index.py:135] — deferred, pre-existing latent risk
- [x] [Review][Defer] `--source-commit` silently accepts and persists empty string with no validation [scripts/build_index.py CLI] — deferred, only reachable via non-standard manual invocation
- [x] [Review][Defer] `index` output directory hardcoded independently in build-step arg and git-add step, no shared source of truth [.github/workflows/build-index.yml:96,140] — deferred, pre-existing
- [x] [Review][Defer] `_audit` exclusion matches any path segment literally named `_audit` anywhere under `docs/`, not scoped to documented location [scripts/build_index.py:225] — deferred, pre-existing
- [x] [Review][Defer] No duplicate-`id` detection across parsed documents [scripts/build_index.py:211] — deferred, currently unreachable since IDs derive from unique file paths

## Dev Notes

### Story Intent

Story 2.4 closes Epic 2 by moving from sidecar-only publication to a deterministic, snapshot-based index publication contract that Epic 3 consumers can query. This story must preserve governance gates built in 2.2 and 2.3 while introducing a build manifest and full-snapshot index output that remain stable on reruns.

### Business and Architecture Context

- FR-5 requires idempotent document/concept upsert behavior and freshness within five minutes.
- AD-2 makes index-as-artifact the pilot persistence authority.
- AD-5 requires deterministic regeneration with provenance (`source_path`, `source_hash`).
- AD-7 requires schema/version contract discipline between producer and consumers.
- AD-9 requires atomic publication under one shared `build_manifest_id`.

### Existing Code to Update (Read Fully Before Editing)

- `.github/workflows/build-index.yml`
  - Current state: post-merge sidecar generation + auto-commit.
  - Story change: extend same workflow to produce `index/index.json` + `index/build-manifest.json` in the same publication run.
  - Must preserve: sidecar generation ordering, strict shell blocks, and non-canceling concurrency semantics.

- `scripts/generate_jsonld.py`
  - Current state: deterministic sidecar generation with provenance/hash fields.
  - Story change: no contract break; only reuse outputs as index input.
  - Must preserve: field names, hash behavior, and existing test expectations.

- `scripts/tests/test_generate_jsonld.py`
  - Current state: validates sidecar contract and deterministic hash/path behavior.
  - Story change: keep these tests green while adding index-level tests.

### New Files Expected

- `scripts/build_index.py`
- `scripts/tests/test_build_index.py`
- `scripts/tests/fixtures/` additions for index generation scenarios
- `index/index.json` (generated artifact)
- `index/build-manifest.json` (generated artifact)

### Determinism and Idempotence Guardrails

- Build index from a full repository snapshot of `docs/**/*.md` and sidecars, not only changed files, to prevent stale/orphaned derived relationships.
- Sort all emitted arrays and maps deterministically before serialization.
- Use one JSON serializer strategy (`indent=2`, UTF-8, trailing newline) across all emitted artifacts.
- Repeated publication on unchanged inputs must produce no git diff.
- Never append duplicate relationship entries; treat publication as replace-by-snapshot, not append-log.

### Freshness SLA Guardrails

- Manifest must include machine-readable UTC timestamps in RFC3339.
- Freshness metadata must be explicit and portable (no runner-local assumptions).
- Publication output must expose enough metadata for Epic 3 retrieval to prove whether data is within SLA.

### Integration and Regression Guardrails

- Keep `pr-validate.yml` unchanged for this story unless a strictly necessary compatibility fix is discovered.
- Keep conflict override audit path intact (`docs/_audit/conflict-overrides/`) and excluded from indexing unless explicitly required.
- Preserve contributor-facing markdown canonicality: never mutate document body content during publication.

### Testing Requirements

- Unit tests for index builder parsing, ordering, dedupe, and manifest stamping.
- Determinism test: run index builder twice in temp workspace and assert byte-equal outputs.
- Contract test: validate that all artifacts in one run share same `build_manifest_id`.
- Regression tests: existing sidecar and schema suites remain green.

### Previous Story Intelligence (2.3)

- Override gating now includes strict authorization and append-only audit logs; do not weaken or bypass this in publication flow.
- CI commit behavior for generated artifacts is already in use; continue bot-identity commit style and avoid touching unrelated files.
- Existing review fixes emphasize deterministic behavior and explicit error handling; keep the same implementation posture.

### Git Intelligence Summary

Recent merges show repository pattern is incremental workflow hardening with deterministic scripts and unittest coverage (`scripts/`, `scripts/tests/`, workflow updates). Follow that same pattern: small, auditable changes with tests first-class.

### Latest Technical Information

- GitHub Actions concurrency supports workflow-level groups; maintain one publication run per ref to avoid mixed snapshots.
- GitHub environment/output files (`GITHUB_ENV`, `GITHUB_OUTPUT`, `GITHUB_STEP_SUMMARY`) are the preferred way to pass metadata between steps and publish run summaries.
- Go 1.22 keeps compatibility promises and includes HTTP routing improvements in `net/http`; keep publication contracts clean so upcoming Go retrieval implementation can consume index schema without migration churn.

### Project Context Reference

- Repository command policy applies: use `python3`; avoid `uv` and `rg` in tooling/scripts.
- Story remains in Epic 2 write path only; read path API behavior is consumed in Epic 3.

### References

- `_bmad-output/planning-artifacts/epics.md` (Epic 2, Story 2.4)
- `_bmad-output/planning-artifacts/architecture/architecture-bmadSharedContext-2026-07-08/ARCHITECTURE-SPINE.md` (AD-2, AD-5, AD-7, AD-9)
- `_bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/prd.md` (FR-5, NFR2, NFR7)
- `_bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/addendum.md` (index-as-artifact acceptance authority)
- `_bmad-output/planning-artifacts/ux-designs/ux-bmadSharedContext-2026-07-07/EXPERIENCE.md` (no-silent-failure and explicit state communication)
- `.github/workflows/build-index.yml`
- `scripts/generate_jsonld.py`
- `scripts/tests/test_generate_jsonld.py`
- `https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency`
- `https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#environment-files`
- `https://go.dev/doc/go1.22`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Debug Log References

- `python3 -m unittest discover scripts/tests` → 71 tests, OK
- `python3 -m unittest discover _bmad/scripts/tests` → 11 tests, OK
- `python3 scripts/build_index.py --docs-dir docs --output-dir /tmp/bmad-index-test --source-commit 125fd76` → smoke test passed, 1 document indexed, build_manifest_id consistent across both artifacts

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story status set to ready-for-dev.
- **2026-07-14**: Implemented `scripts/build_index.py` — full-snapshot index builder with deterministic sorting (domain, slug, source_path), idempotent relationship maps, provenance sourced from JSON-LD sidecars or computed on-the-fly, and `NoFrontMatter` exception to skip non-context markdown files (index.md, project-context.md) silently.
- **2026-07-14**: Implemented freshness SLA: `freshness_deadline_utc = generated_at_utc + 5 minutes` stamped in both `index/index.json` and `index/build-manifest.json`; both artifacts carry identical `build_manifest_id`; `write_artifacts()` raises ValueError on mismatch before writing.
- **2026-07-14**: Extended `.github/workflows/build-index.yml`: sidecar generation runs first (Step 1), then deterministic index build (Step 2), then atomic single-commit of all derived artifacts (`docs/**/*.jsonld`, `index/index.json`, `index/build-manifest.json`). Added GitHub Actions step summary reporting publish time, freshness deadline, and artifact counts.
- **2026-07-14**: Created `scripts/tests/test_build_index.py` with 22 tests covering: fixture-driven parsing, deprecated/active filtering, provenance sidecar loading, byte-stable determinism (two consecutive runs with fixed UUID/timestamp produce identical JSON), no-duplicate relationship maps, RFC3339 freshness format, `build_manifest_id` consistency on disk, manifest field completeness, and `_audit/` exclusion.
- **2026-07-14**: Added 3 fixture files (`scripts/tests/fixtures/index-active-a.md`, `index-active-b.md`, `index-deprecated.md`) for index builder test scenarios.
- **2026-07-14**: No retrieval API endpoints implemented; no live graph database dependency introduced; conflict gates from 2.2/2.3 remain intact.
- All 71 `scripts/tests` tests pass; all 11 `_bmad/scripts/tests` regression tests pass.

### File List

- `_bmad-output/implementation-artifacts/2-4-build-deterministic-index-graph-upsert-pipeline-with-freshness-sla.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `scripts/build_index.py` (new)
- `scripts/tests/test_build_index.py` (new)
- `scripts/tests/fixtures/index-active-a.md` (new)
- `scripts/tests/fixtures/index-active-b.md` (new)
- `scripts/tests/fixtures/index-deprecated.md` (new)
- `.github/workflows/build-index.yml` (modified — added build-index step, summary step, atomic commit for index artifacts)

### Change Log

- 2026-07-14: Created `scripts/build_index.py` — deterministic full-snapshot index builder producing `index/index.json` and `index/build-manifest.json` with freshness SLA, provenance, and relationship maps.
- 2026-07-14: Created `scripts/tests/test_build_index.py` — 22 unit/integration tests covering determinism, idempotence, manifest consistency, provenance, freshness format, and _audit exclusion.
- 2026-07-14: Added 3 index builder test fixtures (`index-active-a.md`, `index-active-b.md`, `index-deprecated.md`).
- 2026-07-14: Extended `.github/workflows/build-index.yml` to run `build_index.py` after sidecar generation and commit all derived artifacts atomically in one publication run.
