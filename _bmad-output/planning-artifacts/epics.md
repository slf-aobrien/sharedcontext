---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/prd.md
  - _bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-bmadSharedContext-2026-07-08/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/ux-designs/ux-bmadSharedContext-2026-07-07/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-bmadSharedContext-2026-07-07/EXPERIENCE.md
---

# bmadSharedContext - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for bmadSharedContext, decomposing the requirements from the PRD, UX design, and architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Context documents must include required front-matter fields (title, domain, description, keywords, created, updated, validated-by, validated-on, status) and fail validation if any are missing.

FR2: On merge, the ingestion workflow must generate a valid .jsonld sidecar for each context document.

FR3: On every PR to main, schema validation must check changed documents and return file-and-field specific diagnostics.

FR4: On every PR to main, conflict detection must compare incoming docs against same-domain docs, block merge on unresolved conflicts, allow threshold tuning via repo variable, and support logged domain-owner override with conflict-override: justified.

FR5: On merge to main, keyword extraction and graph/index population must upsert document/concept relationships, become queryable within five minutes, and remain idempotent on reruns.

FR6: Retrieval API must expose GET /context?keyword={term}&domain={domain-slug}, return HTTP 200 with empty array when no results, and include slug, title, domain, status, validated-on, and body_excerpt.

FR7: Retrieval API must expose conflict_flag and conflict_summary for unresolved-conflict documents.

FR8: Agent creation CLI must prompt for agent name, domain, task type, and output format, then generate working config with retrieval endpoint, scoped instructions, and empty-result fallback.

FR9: Repository must provide CONTRIBUTING guidance and a context document template that enables valid submissions without extra help.

FR10: Each domain must define at least one CODEOWNERS owner so relevant PR reviews are automatically requested.

### NonFunctional Requirements

NFR1: Retrieval performance must meet p95 <= 2 seconds under normal pilot load.

NFR2: Newly merged context must be retrievable within 5 minutes.

NFR3: Ingestion reliability target is >= 95% successful full runs without manual intervention.

NFR4: Conflict-detection precision target is >= 70% in pilot.

NFR5: New user must complete agent setup within 5 minutes without prior setup knowledge.

NFR6: Metadata approach must remain interoperable with markdown + YAML front-matter and JSON-LD/schema.org direction.

NFR7: Pipeline reruns on unchanged input must be idempotent (no duplicate derived state).

NFR8: Conflict overrides must be explicit, justified, and logged for auditability.

NFR9: Pilot execution should remain local-first while preserving GitHub-compatible behavior.

NFR10: Project-owned artifacts should remain readable and accessible (keyboard-first flows, explicit blocking states, plain-language error reporting).

### Additional Requirements

- Enforce write/read separation: CI build path produces derived artifacts, runtime API serves read-only retrieval from committed artifacts.
- Keep index-as-artifact as pilot persistence authority; live graph runtime is optional for demos and future evolution.
- Run conflict checks against full repository working tree in CI as a blocking gate.
- Preserve document canonicality: markdown source is editable truth, derived rules are read-only outputs.
- Require deterministic regeneration with provenance fields (source_path, source_span, source_hash) for derived rules.
- Allow agents to submit proposals only; only pipeline processing can promote proposals into derived rules.
- Treat schema version as producer-consumer contract; reject unsupported major versions.
- Require atomic artifact publication with shared build_manifest_id across related outputs.
- Require PR-gated agent-authored knowledge (same review and CI as human-authored changes).
- Pin workflow/runtime baselines for reproducible CI behavior.
- Keep GitHub as fixed platform and containers as default pilot runtime posture.
- Use Go for retrieval API implementation in Phase 1.

### UX Design Requirements

UX-DR1: Apply the DESIGN color token system consistently across project-owned artifacts and generated surfaces (status, warnings, errors, code blocks, cards).

UX-DR2: Apply typography roles (display, heading, body, label, mono) so technical docs and reports remain scannable and consistent.

UX-DR3: Implement compact status-badge patterns for draft/active/deprecated/validation states; deprecated content must stay visible and clearly flagged.

UX-DR4: Implement conflict callout pattern that names both conflicting sources and recommends revise-first before override.

UX-DR5: Implement schema error list pattern grouped by file then field, with explicit pointers to offending file/field pairs.

UX-DR6: Implement command block pattern with copyable commands and explicit inline-variable guidance.

UX-DR7: Implement agent config summary view after CLI generation showing selected domain, task type, format, endpoint, and fallback behavior.

UX-DR8: Implement freshness signaling tied to validated-on recency, including stale/missing metadata visibility.

UX-DR9: Enforce keyboard-first completion across contribution, review, and smoke-check flows.

UX-DR10: Ensure all blocking states are understandable in plain text/markdown without relying on color alone.

UX-DR11: Ensure responsive behavior for project-owned artifacts: single-column fallback and readable handling of wide tables/command blocks on narrow viewports.

UX-DR12: Enforce no-silent-failure behavior: empty retrieval returns explicit no-context messaging; conflict and validation failures remain explicit and actionable.

### FR Coverage Map

FR1: Epic 1 - Enforce required front-matter schema in contribution workflow  
FR2: Epic 2 - Generate valid JSON-LD sidecars during publication  
FR3: Epic 1 - Run PR schema checks with actionable diagnostics  
FR4: Epic 2 - Detect and gate conflicts with controlled override path  
FR5: Epic 2 - Build idempotent index/graph updates with freshness SLA  
FR6: Epic 3 - Serve keyword/domain retrieval API contract  
FR7: Epic 3 - Surface unresolved conflict flags in retrieval responses  
FR8: Epic 3 - Provide guided agent config generation and smoke-testable output  
FR9: Epic 1 - Provide contributor template and guidance for valid docs  
FR10: Epic 1 - Enforce domain-owner review routing via CODEOWNERS

## Epic List

### Epic 1: Trusted Knowledge Contribution and Governance

Contributors and domain owners can author, validate, and approve domain context safely through PRs, with clear ownership and contribution guidance.

**FRs covered:** FR1, FR3, FR9, FR10

### Epic 2: Conflict-Safe Publication Pipeline

Teams can merge new knowledge confidently because automation blocks conflicting or malformed content and publishes deterministic, auditable artifacts.

**FRs covered:** FR2, FR4, FR5

### Epic 3: Reliable Shared Context Consumption for Agents

Developers can create and run agents that retrieve accurate, conflict-aware domain context quickly, with explicit fallback behavior when context is missing.

**FRs covered:** FR6, FR7, FR8

## Epic 1: Trusted Knowledge Contribution and Governance

Contributors and domain owners can author, validate, and approve domain context safely through PRs, with clear ownership and contribution guidance.

### Story 1.1: Define Context Document Schema and Front-Matter Requirements

As a domain owner,
I want all context documents to have consistent, required metadata,
So that the system can validate completeness and enforce governance.

**Acceptance Criteria:**

**Given** a context document template with all required fields (title, domain, description, keywords, created, updated, validated-by, validated-on, status)
**When** a document is submitted without any required field
**Then** schema validation fails and reports which specific field is missing, by file name
**And** documents with `status: deprecated` remain retrievable while being explicitly flagged

### Story 1.2: Create Contribution Template and Guidance

As a new contributor,
I want a clear template and instructions,
So that I can author valid context documents without external help.

**Acceptance Criteria:**

**Given** `/templates/context-document-template.md` and `CONTRIBUTING.md` are present in the repository
**When** a contributor follows only those documents to create a new context document
**Then** the resulting document passes schema validation without requiring extra undocumented steps
**And** the template includes inline instructions and representative examples for each required front-matter field

### Story 1.3: Implement PR Schema Validation Workflow

As a domain owner reviewing a PR,
I want automated schema checks to catch incomplete or malformed documents before merge,
So that invalid knowledge artifacts never enter the main branch.

**Acceptance Criteria:**

**Given** a PR targeting `main` with new or modified context documents
**When** the schema validation workflow runs
**Then** all changed documents are validated against the required front-matter schema
**And** failures are grouped by file and field with actionable messages that block merge until corrected

### Story 1.4: Configure Domain Ownership with CODEOWNERS

As a domain owner,
I want domain-scoped CODEOWNERS enforcement,
So that relevant pull requests automatically request review from the right owner.

**Acceptance Criteria:**

**Given** `CODEOWNERS` includes an owner mapping for `/domains/user-authentication/`
**When** a PR modifies files under that path
**Then** GitHub automatically requests review from the mapped owner
**And** the protected branch policy requires owner approval before merge

## Epic 2: Conflict-Safe Publication Pipeline

Teams can merge new knowledge confidently because automation blocks conflicting or malformed content and publishes deterministic, auditable artifacts.

### Story 2.1: Generate JSON-LD Sidecars on Merge

As a platform engineer,
I want each merged context document to produce a valid JSON-LD sidecar,
So that document metadata is machine-readable and interoperable for downstream tooling.

**Acceptance Criteria:**

**Given** a merge to `main` that adds or updates one or more context documents
**When** the post-merge ingestion workflow runs
**Then** each changed document gets a corresponding `.jsonld` sidecar in the expected location
**And** generated sidecars validate against the selected metadata representation without schema errors

### Story 2.2: Implement Blocking Conflict Detection with Tunable Threshold

As a domain owner,
I want conflicting claims detected during PR validation,
So that contradictory knowledge does not get merged unnoticed.

**Acceptance Criteria:**

**Given** a PR that introduces or changes context documents within a domain
**When** conflict detection executes against the full repository working tree
**Then** any unresolved contradiction causes the PR check to fail and blocks merge
**And** the conflict threshold is configurable via repository variable without code changes
**And** the failure report names both source files and summarizes the contradictory claims

### Story 2.3: Add Domain-Owner Conflict Override with Audit Logging

As a domain owner,
I want to override false-positive conflicts with explicit justification,
So that teams can proceed when automated checks are over-sensitive while preserving accountability.

**Acceptance Criteria:**

**Given** a PR blocked by conflict detection
**When** a domain owner adds `conflict-override: justified` with rationale in the PR description
**Then** the workflow permits merge subject to standard approvals
**And** the override action is logged with PR reference, actor, timestamp, and reason for auditability

### Story 2.4: Build Deterministic Index/Graph Upsert Pipeline with Freshness SLA

As an AI agent consumer,
I want recently merged knowledge to become queryable quickly and consistently,
So that agent outputs reflect the latest approved domain context.

**Acceptance Criteria:**

**Given** a successful merge to `main`
**When** index/graph publication runs
**Then** document and concept relationships are upserted without duplicate derived state on reruns
**And** newly merged keywords are retrievable through the API within five minutes
**And** published artifacts carry consistent provenance and shared build manifest identity for the snapshot

## Epic 3: Reliable Shared Context Consumption for Agents

Developers can create and run agents that retrieve accurate, conflict-aware domain context quickly, with explicit fallback behavior when context is missing.

### Story 3.1: Implement Retrieval API Keyword and Domain Query Endpoint

As an AI agent,
I want to query shared context by keyword and domain,
So that I can retrieve relevant approved domain knowledge during task execution.

**Acceptance Criteria:**

**Given** a running retrieval API with access to the published index artifact
**When** a client calls `GET /context?keyword={term}&domain={domain-slug}` with a known keyword
**Then** the API returns HTTP 200 within p95 <= 2 seconds under normal pilot load
**And** each result includes `slug`, `title`, `domain`, `status`, `validated-on`, and `body_excerpt`

### Story 3.2: Add Conflict Signaling in Retrieval Responses

As an agent user,
I want retrieval results to indicate unresolved conflicts,
So that I can judge confidence and avoid using disputed guidance as settled truth.

**Acceptance Criteria:**

**Given** a context document with an unresolved logged conflict
**When** it is returned by the retrieval endpoint
**Then** the response includes `conflict_flag: true`
**And** the response includes a non-empty `conflict_summary` describing the active conflict

### Story 3.3: Build Interactive Agent Creation CLI

As a developer,
I want a guided CLI wizard for creating agent configs,
So that I can connect an agent to shared context without prior setup expertise.

**Acceptance Criteria:**

**Given** a developer runs the agent creation command
**When** prompted for agent name, domain, task type, and output format
**Then** the CLI validates input and generates a usable agent config file
**And** the generated config contains retrieval endpoint wiring, selected domain scope, task instructions, and empty-result fallback behavior

### Story 3.4: Add Agent Configuration Summary and Smoke-Test Flow

As a developer,
I want a post-generation summary and smoke test,
So that I can verify the new config works immediately.

**Acceptance Criteria:**

**Given** a config was generated by the CLI
**When** generation completes
**Then** the CLI displays a summary of domain, task type, output format, endpoint, and fallback behavior
**And** a smoke-check command validates retrieval connectivity and returns either at least one result or an explicit empty-result outcome
**And** the complete flow can be finished by a new user within 5 minutes

### Story 3.5: Implement Explicit Empty-Result Fallback Messaging

As an agent user,
I want explicit no-context messaging when retrieval has no matches,
So that workflows remain transparent and avoid fabricated context.

**Acceptance Criteria:**

**Given** no document matches the requested keyword and domain
**When** the retrieval endpoint is called
**Then** the API returns HTTP 200 with an empty array
**And** agent-facing behavior presents a clear no-context message and proceeds via configured fallback rather than inventing context
