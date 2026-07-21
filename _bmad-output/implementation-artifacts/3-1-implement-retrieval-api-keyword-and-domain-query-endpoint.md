---
baseline_commit: TBD (see Critical Blocker below)
---

# Story 3.1: Implement Retrieval API Keyword and Domain Query Endpoint

Status: ready-for-dev

## Story

As an AI agent,
I want to query shared context by keyword and domain,
So that I can retrieve relevant approved domain knowledge during task execution.

## Acceptance Criteria

1. **Given** a running retrieval API with access to the published index artifact
   **When** a client calls `GET /context?keyword={term}&domain={domain-slug}` with a known keyword
   **Then** the API returns HTTP 200 within p95 <= 2 seconds under normal pilot load
   **And** each result includes `slug`, `title`, `domain`, `status`, `validated-on`, and `body_excerpt`

2. **Given** a query with no matching results
   **When** the retrieval endpoint is called
   **Then** the API returns HTTP 200 with an empty results array (deferred to Story 3.5 for agent-level fallback messaging)

3. **Given** the API is queried with an unsupported `schema_version` in the published index
   **When** the API starts up and reads the index
   **Then** the API validates the index's `schema_version` against its supported version and rejects incompatible major versions with a clear startup error

## 🚨 CRITICAL BLOCKER — Epic 2 Publication Pipeline Not Validated End-to-End

**Discovery from Epic 2 retrospective (2026-07-16):**

> Epic 2's publication pipeline has been validated only by unit tests. The `index/index.json` and `index/build-manifest.json` artifacts have NEVER been produced by a real merge to `main`. The repository has no `index/` directory with committed artifacts.

**Impact on Story 3.1:**

- The retrieval API has **no artifact to read and test against**.
- All Story 3.1 implementation will be built against a **fictional/mocked index artifact**, not the real output from Story 2.4.
- Performance testing (AC p95 ≤ 2 seconds) cannot be validated without real artifact structure.
- Integration tests cannot verify the API against actual build-manifest format.

**Recommended action before dev begins:**

Either:
1. **Trigger the publication workflow on `main`** (run `build-index.yml` manually against the current state, or make a real merge to activate it), verify that `index/index.json` and `index/build-manifest.json` are committed and readable.
2. **OR create a representative test fixture** in `scripts/tests/fixtures/` that matches the schema from Story 2.4 and commit it to `index/` as a stable input for Story 3.1 development.
3. **Document the decision** in the story's Dev Notes before implementation begins.

**This story cannot claim AC compliance without resolving this first.**

---

## Tasks / Subtasks

### Task 1: Set Up Go Module and Directory Structure (AC: all)

- [ ] Initialize Go module at `cmd/retrieval-api/`
  - [ ] `go mod init github.com/<owner>/bmadSharedContext/cmd/retrieval-api`
  - [ ] Create `cmd/retrieval-api/main.go` with skeleton server startup
  - [ ] Document minimum supported Go version (suggest 1.22+; verify with architecture policy)
  
- [ ] Create internal packages
  - [ ] `internal/retrieval/` — query and filtering logic over index artifact
  - [ ] `internal/indexmodel/` — schema models and version compatibility checks
  - [ ] Establish naming and import boundaries per Architecture Spine (docs)

- [ ] Create test fixtures directory
  - [ ] `scripts/tests/fixtures/index-schema-1.0.json` — representative test index matching Story 2.4 schema
  - [ ] Document fixture provenance (e.g., "Matches `index/index.json` schema from build-index.py Story 2.4")

### Task 2: Define Index Schema Models and Validation (AC: 3)

- [ ] Model the expected `index/index.json` structure (from Story 2.4 output)
  - [ ] Go structs: `IndexArtifact`, `Document`, `BuildManifest`, `Relationships`
  - [ ] Enforce required fields: `build_manifest_id`, `schema_version`, `documents[]`, `relationships{}`
  - [ ] Use struct tags for JSON unmarshaling and field validation
  
- [ ] Implement schema version validation
  - [ ] Parse `schema_version` string from index (e.g., "1.0")
  - [ ] On startup: check major version against API's supported range (e.g., 1.x)
  - [ ] Reject unsupported major versions with error message including: expected version, received version, upgrade guidance
  
- [ ] Add consistency validation for atomic publication (AD-9)
  - [ ] Verify all artifact records share one `build_manifest_id` value
  - [ ] Fail fast with clear error if mismatched IDs detected

- [ ] Create unit tests for model unmarshaling and validation
  - [ ] Test valid index loads without error
  - [ ] Test unsupported schema_version rejection
  - [ ] Test missing required fields detection
  - [ ] Test build_manifest_id consistency checks

### Task 3: Implement Index Loading and In-Memory Indexing (AC: 1)

- [ ] Load index artifact on startup
  - [ ] Accept `--index-path` flag or `INDEX_PATH` env var pointing to `index/index.json`
  - [ ] Read and parse JSON into model structs
  - [ ] Validate schema version (Task 2)
  - [ ] Log load success with document count and keyword count
  
- [ ] Build in-memory indexes for fast query lookups
  - [ ] **Keyword → Documents**: map[keyword][]DocumentID for rapid lookup
  - [ ] **Domain → Documents**: map[domain][]DocumentID
  - [ ] **Document → Fields**: map[DocumentID]Document for result assembly
  - [ ] Pre-sort document results deterministically (by document_id, then source_path, then source_span — per Consistency Conventions, AD-7)
  
- [ ] Add index refresh/reload capability
  - [ ] Implement a reload handler for runtime index swaps (optional, defer if needed)
  - [ ] Document that in-memory indexes must be rebuilt on reload

### Task 4: Implement Query Endpoint Handler (AC: 1, 2)

- [ ] Create HTTP handler for `GET /context`
  - [ ] Parse query parameters: `keyword` (required), `domain` (optional)
  - [ ] Validate input: keyword must be non-empty; domain must match pattern if provided (suggest alphanumeric + hyphen)
  - [ ] Return HTTP 400 with clear error message for missing/invalid parameters
  
- [ ] Implement query logic
  - [ ] If `domain` is provided: filter to documents in that domain AND matching keyword
  - [ ] If `domain` is omitted: search across all domains matching keyword
  - [ ] Return documents with `status: active` by default; deferred to Story 3.2 whether to surface `status: draft`
  - [ ] Return empty array if no matches (AC 2)

- [ ] Build response envelope
  - [ ] Structure: `{ "request_id": "...", "schema_version": "1.0", "build_manifest_id": "...", "results": [...], "conflicts": [], "provenance": {...} }`
  - [ ] Set `request_id` to a unique ID (UUID4) for tracing
  - [ ] Include `schema_version` and `build_manifest_id` from loaded index
  - [ ] Include each result: `id`, `slug`, `title`, `domain`, `status`, `validated_on`, `body_excerpt` (first 200 chars of document body or empty if not available)
  - [ ] Keep `conflicts` and `provenance` placeholders for now (filled by Story 3.2 and future work)

- [ ] Implement result ordering
  - [ ] Sort results deterministically per Consistency Conventions: by `document_id`, then `source_path`, then `source_span`
  - [ ] Document ordering in response contract comment

- [ ] Add comprehensive tests
  - [ ] Test successful query with keyword in active documents
  - [ ] Test query with domain filter
  - [ ] Test query with no matches (empty array)
  - [ ] Test missing `keyword` parameter (HTTP 400)
  - [ ] Test invalid `domain` pattern (HTTP 400)
  - [ ] Test case-insensitive keyword matching (or define exact matching behavior)
  - [ ] Test response envelope structure and field presence

### Task 5: Performance and Error Handling (AC: 1, baseline)

- [ ] Implement startup and runtime error handling
  - [ ] Index load failures: log error, provide actionable message, fail startup (do not start server without valid index)
  - [ ] Query errors: log with request_id for tracing, return HTTP 500 with error message (no stack traces exposed)
  
- [ ] Add structured logging
  - [ ] Log on startup: Go version, index path, document count, keyword count, schema_version
  - [ ] Log on each query: request_id, keyword, domain, result count, latency
  - [ ] Use JSON or structured log format for machine readability
  
- [ ] Implement basic performance instrumentation
  - [ ] Measure query latency end-to-end (parse → lookup → build response)
  - [ ] Log histogram or percentile stats periodically (defer detailed perf testing to load test harness)
  - [ ] Ensure hot-path queries (index lookup, result filtering) are O(1) or O(log n) operations
  
- [ ] Document performance baseline
  - [ ] Add comment in code: "Expected p95 ≤ 2s under normal pilot load (verified by integration test, not unit test)"
  - [ ] Note assumption: in-memory index is fast; latency dominated by I/O on initial load

### Task 6: Documentation and Testing Harness (AC: all)

- [ ] Write API contract documentation
  - [ ] Document `GET /context` endpoint: parameters, response shape, status codes, error cases
  - [ ] Include example curl/JSON requests and responses
  - [ ] Document schema_version compatibility rules and startup failure modes
  
- [ ] Create smoke test helper script
  - [ ] `scripts/test_retrieval_api.sh` — starts the API, issues 3–5 representative queries, validates responses
  - [ ] Requires valid `index/index.json` to exist (deferred until Epic 2 blocker is resolved)
  - [ ] Exit 0 on success, non-zero on failure
  - [ ] Output human-readable pass/fail summary
  
- [ ] Create Go test suite
  - [ ] Run: `go test ./cmd/retrieval-api/...`
  - [ ] All tests must pass before code review
  - [ ] Target 80%+ coverage of query logic (exclude main() startup boilerplate)
  - [ ] Coverage report: `go test -cover ./...`

- [ ] Add integration test placeholder (deferred to Story 3.2/3.4)
  - [ ] Create `scripts/tests/test_retrieval_api_integration.py` stub
  - [ ] Document: "Story 3.2 will add conflict-signaling tests; Story 3.4 will add end-to-end flow tests"

---

## Dev Notes

### Story Intent

Story 3.1 is the first consumer of the index artifact published in Epic 2. It establishes the retrieval API contract and demonstrates that the publication pipeline's output is machine-readable and queryable. This story does **not** implement conflict signaling (3.2), agent CLI wiring (3.3), or explicit fallback messaging (3.5) — it is the foundational read path only.

### Architecture Constraints (Must Follow)

**AD-1 — Runtime boundary between write and read paths:**
- The API is read-only; it has zero write logic and makes zero modifications to the index artifact.
- The API never re-generates the index or modifies `docs/` or `index/` files.
- If the index needs updating, it comes from the CI publication pipeline, not the API.

**AD-2 — Index-as-artifact persistence model:**
- The API reads from a committed JSON file (`index/index.json`), not a database.
- No live graph database, no cache layer, no runtime state mutations.
- The API is stateless except for in-memory lookup indexes (rebuilt on each startup/reload).

**AD-4 — Document canonicality:**
- The API returns documents from the index as-is; it does NOT enforce business rules (e.g., filtering by status).
- Status filtering is deferred to Story 3.2/3.5 (where conflict and fallback logic lives).
- The API surface must remain agnostic to governance rules; those live in the write path (CI).

**AD-7 — Artifact schema as the only producer-consumer contract:**
- The API must validate that the index `schema_version` matches an expected range (e.g., 1.x).
- If the index has `schema_version: "2.0"` and the API only supports 1.x, startup fails with a clear error.
- This is the ONLY version checking mechanism; APIs and indices must negotiate by schema version, not by implicit assumption.

**AD-9 — Atomic artifact publication:**
- All documents and metadata in a published index share one `build_manifest_id` (generated by Story 2.4).
- The API must validate that all loaded records have the same `build_manifest_id`; if not, fail startup.
- This ensures the API is never reading a "mixed" snapshot from two different publication runs.

### Technical Requirements

**Language:** Go 1.22+ (per architecture additional requirement: "Use Go for retrieval API implementation in Phase 1")

**API Framework:** Standard library `net/http` is sufficient for MVP. If REST features grow later (pagination, filtering, caching headers), consider `gorilla/mux` or similar, but avoid over-engineering for the pilot scope.

**Serialization:** `encoding/json` for index loading and response marshaling.

**Startup Mode:** Command-line tool that reads index, builds in-memory lookup structures, and serves HTTP on a configurable port (default `:8080`; override with `--port` flag or `PORT` env var).

**Deployment Posture:** Container-first (Dockerfile for the API binary). Pilot deployment mode is "local-first" (NFR-9), so single-container deployment without orchestration is acceptable.

**Performance Target (NFR-1):** p95 latency ≤ 2 seconds under normal pilot load.
- "Normal pilot load" is undefined — suggest 10 QPS steady-state, 100 QPS burst.
- Actual load testing deferred to integration testing phase (Story 3.4), but implementation must not have obvious hot-path inefficiencies.
- In-memory lookup should be O(1) or O(log n) for any per-query operation.

**Error Handling:** 
- Startup errors (missing index, invalid schema_version, mismatched build_manifest_id) → fatal, exit code 1, clear error message on stderr.
- Query errors (malformed input, internal panic) → HTTP 500, JSON error response with request_id for tracing.
- No stack traces exposed in HTTP responses (only in logs).

### Index Artifact Contract (From Story 2.4)

The API expects to read `index/index.json` with this structure:

```json
{
  "build_manifest_id": "uuid-string",
  "schema_version": "1.0",
  "generated_at_utc": "2026-07-16T15:24:56Z",
  "freshness_deadline_utc": "2026-07-16T15:29:56Z",
  "document_count": 1,
  "keyword_count": 2,
  "active_document_ids": [],
  "documents": [
    {
      "id": "docs/user-authentication/concepts",
      "domain": "user-authentication",
      "slug": "concepts",
      "source_path": "docs/user-authentication/concepts.md",
      "source_hash": "sha256:...",
      "title": "User Authentication Concepts",
      "description": "...",
      "keywords": ["authentication", "concepts"],
      "status": "draft",
      "active": false,
      "created": "2026-07-09 00:00:00+00:00",
      "updated": "2026-07-09 00:00:00+00:00",
      "validated_by": "slf-aobrien"
    }
  ],
  "relationships": {
    "domain_documents": { "user-authentication": ["docs/user-authentication/concepts"] },
    "keyword_documents": { "authentication": [...], "concepts": [...] }
  }
}
```

**CRITICAL:** This structure is speculative based on Story 2.4 implementation notes. Until the epic 2 blocker is resolved (actual artifact produced), you are implementing against an educated guess, not a proven contract. Coordinate with the actual output from `build_index.py` as soon as it's available.

### File Structure

```
{project-root}/
  cmd/retrieval-api/
    main.go                    # Server startup, CLI flags, port binding
    go.mod, go.sum             # Dependency manifest
  internal/retrieval/
    query.go                   # Query execution, index lookup, result filtering
    model.go                   # Go structs for query results, response envelope
    handler.go                 # HTTP handler for GET /context
  internal/indexmodel/
    index.go                   # Index artifact model structs (unmarshal, validation)
    schema.go                  # Schema version validation, compatibility checks
  scripts/
    test_retrieval_api.sh      # Smoke test harness (bash)
    tests/
      test_retrieval_api_integration.py  # Integration tests (deferred to 3.2/3.4)
      fixtures/
        index-schema-1.0.json  # Test fixture matching Story 2.4 output schema
```

### Previous Story Intelligence (From Epic 2)

**Epic 2 Retrospective key findings:**

1. **Publication pipeline validated only by unit tests.** The `index/index.json` artifact has never been produced by a real merge. This directly impacts 3.1's ability to test against real data. Epic 2's success metrics are artificially inflated because integration was never proven.

2. **Deferred items accumulate without closing.** Epic 2 deferred ~27 items (mostly CI/infrastructure debt). The same issues were flagged in multiple stories as "pre-existing." No mechanism exists to retire deferred items — they become a permanent backlog. **For this story: do not defer CI/shell issues. Fix them in-story or document explicitly why they cannot be fixed.**

3. **Schema contract mismatches get deferred to "future consumers."** The `contentStatus` vs `schema:creativeWorkStatus` mismatch was flagged in Story 2.1 and explicitly deferred to "Story 2.4 + Epic 3 consumers." Story 2.4 passed without fixing it. You are now "future consumer." **Decision needed: should this story fix the field name before querying it, or accept the current schema and document the deviation?**

4. **Go code patterns NOT yet established.** Epic 2 was all Python (scripts, sidecar generation, conflict detection, index building). This is the first Go code in the project. No established conventions exist yet. You are setting the baseline for future Go work (stories 3.3, 3.4, and beyond). **Strong recommendation: document Go conventions in Dev Notes as you establish them (import organization, error handling style, logging patterns, test structure).**

### Code Review Discipline (From Epic 1 & 2)

**CI/Infrastructure issues** were the most-deferred category in both epics. Stories 1.3 and 1.4 shipped with shell/YAML quality gaps that will compound if left unfixed. This story's `cmd/retrieval-api/` and build setup (if included) should be reviewed with defensive rigor:

- Explicit `shell: bash` on multi-line workflow steps
- No silenced stderr/exit codes
- Timeout guards on long-running operations
- Explicit error handling (no assumptions about binaries existing in `$PATH`)

### Git Baseline

This story does not depend on a specific baseline commit (Story 2.4 is complete, so any current `main` is valid). However, **once the Epic 2 blocker is resolved** (index artifact committed), document that commit SHA here for reproducibility.

### Testing Standards

From Epic 1 & 2: All code shipped the first time must be covered by passing tests.

- Unit tests: `go test ./...` must pass; aim for 80%+ coverage of business logic.
- Integration smoke test: `scripts/test_retrieval_api.sh` must pass (after Epic 2 blocker resolved).
- No test deferred to code review; review receives code that already passes tests.

---

## Dev Agent Record

### Agent Model Used

[To be filled by dev agent on completion]

### Debug Log References

[To be filled by dev agent on completion]

### Completion Notes

- [ ] All tasks completed and tested
- [ ] All acceptance criteria verified
- [ ] Code review passed
- [ ] Integration with Epic 2 artifacts validated (once blocker resolved)

### File List

[To be filled by dev agent at completion]
