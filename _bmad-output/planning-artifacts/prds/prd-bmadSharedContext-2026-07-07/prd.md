---
title: Shared Context System for Domain Knowledge and AI Agent Skills
status: final
created: 2026-07-07
updated: 2026-07-07
---

# PRD: Shared Context System for Domain Knowledge and AI Agent Skills

## 0. Document Purpose

This PRD defines Phase 1 (Pilot) of a GitHub-based shared context system that makes organizational domain knowledge accessible to both AI agents and humans. It is written for product, architecture, and engineering teams who will plan, build, and evaluate the pilot. The document constrains the pilot to a single domain — User Authentication — sufficient to prove the concept and measure the three acceptance tests defined during discovery. The system is designed to stay close to established open standards and common docs-as-code patterns, using a loose interpretation guided by markdown authoring and directory structure, and only embellishing where necessary. Specific technical selections and standards mappings are captured in `addendum.md`.

---

## 1. Vision

Organizations accumulate domain knowledge across SharePoint, Confluence, wikis, and individual experts' heads. AI agents — the primary consumers of this knowledge in automated workflows — have no reliable, structured way to query it. The result is agents that hallucinate, conflict with organizational standards, or require expensive prompt engineering per task.

The Shared Context System is a GitHub-native knowledge repository where domain knowledge is authored as structured markdown documents, automatically indexed into a graph database, and exposed via a lightweight containerized Go API. The pilot is intentionally local-first for ease of demo and early adoption: as much of the stack as possible should run on a developer machine while still preserving the repository and automation patterns needed for later GitHub-centered rollout. When an agent receives a task, it queries the API by keyword and receives back accurate, organization-vetted, conflict-checked context — grounded in the same vocabulary the business uses.

The pilot proves this loop on one well-understood domain (User Authentication): an agent is created and pointed at the shared context in under five minutes, it retrieves accurate context in under two seconds, and human contributors find the system valuable enough to add to it voluntarily.

---

## 2. Target Users

### 2.1 Jobs To Be Done

- **AI Agents**: retrieve domain-specific context by keyword to guide code generation, surface conflicts with proposed changes, or suggest implementation options — without requiring per-task prompt engineering.
- **Developers**: create agents connected to shared context without reading documentation; validate that agent behavior aligns with organizational standards.
- **Business / Domain Owners**: contribute, review, and validate domain knowledge without needing git expertise (Phase 2 priority; Phase 1 accepts git workflow).
- **Operations / Quality teams**: verify that stored context is accurate, identify conflicts between documents, and approve or reject PRs that introduce conflicting knowledge.
- **All disciplines (long-term)**: discover what the organization knows about a domain without opening five different tools.

### 2.2 Non-Users (v1 Pilot)

- External users outside the organization.
- Users seeking real-time collaborative editing (this is asynchronous, PR-driven).
- Teams outside the pilot domain (User Authentication) — they may observe but not contribute in Phase 1.

### 2.3 Key User Journeys

**UJ-1. Amelia creates an agent connected to shared context in under five minutes.**
- **Persona + context**: Amelia, a senior engineer, needs an agent to guide implementation of a new authentication feature against the org's standards.
- **Entry state**: authenticated to the org GitHub; has VS Code + GitHub Copilot.
- **Path**: Amelia runs the agent-creation script, answers 3–4 prompted questions (domain, task type, access level), receives a generated agent config with the shared context API endpoint pre-wired.
- **Climax**: Agent is created and successfully queries the shared context API, returning at least one relevant concept for the User Authentication domain within 5 minutes of starting the script.
- **Resolution**: Amelia uses the agent in her next implementation task; the agent's suggestions reference org-standard terminology.
- **Edge case**: If the shared context returns no results for the queried keyword, the agent surfaces a "no context found" message and offers to proceed without context rather than silently hallucinating.

**UJ-2. The GitHub Action catches a conflict before a PR is merged.**
- **Persona + context**: Aaron, a domain owner, submits a PR adding a new User Authentication document that contradicts an existing rule about session timeout values.
- **Entry state**: PR raised against `main` in the knowledge repository.
- **Path**: Pre-merge GitHub Action runs; semantic comparison detects conflicting statements between the new document and an existing `session-management.md`; PR check fails with a specific conflict report linking both documents and the contradicting claims.
- **Climax**: Aaron sees the conflict before it pollutes the graph database; he and the session management owner resolve it, update the PR, and the check passes.
- **Resolution**: Merged document is accurate and consistent; graph database is populated with clean data.
- **Edge case**: False positive conflict (similar vocabulary, different context); Aaron can override with a documented justification comment that is logged.

**UJ-3. A business analyst validates that stored rules are still correct.**
- **Persona + context**: Sarah, a business analyst, reviews the User Authentication domain documents monthly.
- **Entry state**: authenticated to the shared context UI (Phase 1: GitHub repo; Phase 2: web UI).
- **Path**: Sarah browses documents tagged with `domain:user-authentication`; for each one, sees the `validated-by` and `validated-on` metadata fields; clicks "validate" (Phase 1: edits front-matter; Phase 2: UI action); submits a PR.
- **Climax**: Document `validated-on` date is updated; confidence score for that context node increases in the graph.
- **Resolution**: Agents querying that node receive a freshness signal alongside the content.

---

## 3. Glossary

- **Domain** — A bounded area of organizational knowledge (e.g. "User Authentication," "Payment Processing"). A document belongs to exactly one Domain. Domains are defined by Domain Owners and represented in the knowledge model and metadata.
- **Context Document** — A markdown file in the knowledge repository representing one unit of domain knowledge. Contains structured front-matter metadata and a body in plain markdown. Identified by a stable slug.
- **Concept** — A term or phrase that represents a meaningful unit within a Domain. Stored in the graph and linked to Context Documents and other Concepts.
- **Keyword** — A normalized string extracted from a Context Document used to index it in the graph database and power retrieval.
- **Conflict** — Two or more Context Documents making logically contradictory claims about the same Concept. Detected at PR time by the Conflict Detection Action.
- **Knowledge Graph** — The Neo4j graph database containing Concept nodes, Context Document nodes, Domain nodes, and their relationships. The authoritative index for agent and human queries.
- **Agent Config** — A generated configuration file (YAML/JSON) that wires an AI agent to the shared context API, specifying domain scope, retrieval endpoint, and fallback behavior.
- **Domain Owner** — A named individual (business or IT) responsible for reviewing PRs, resolving Conflicts, and periodically validating Context Documents within their Domain.
- **Ingestion Pipeline** — The GitHub Actions workflow that runs on merge to `main`, extracts Keywords, builds JSON-LD metadata, and populates the Knowledge Graph.
- **Retrieval API** — The HTTP endpoint that accepts a keyword query and returns matching Context Documents and Concept nodes from the Knowledge Graph.
- **Validation** — The act of a Domain Owner or designated reviewer confirming that a Context Document is still accurate, updating the `validated-on` front-matter field.

---

## 4. Features

### 4.1 Knowledge Repository Structure

**Description:** The knowledge base lives as a GitHub repository. Context Documents are markdown files organized by Domain in folder paths (`/domains/{domain-slug}/{document-slug}.md`). Each file contains a structured YAML front-matter block and a plain-markdown body. This is the sole authoring interface in Phase 1. Realizes UJ-2, UJ-3.

**Functional Requirements:**

#### FR-1: Context Document front-matter schema

Each Context Document MUST include the following YAML front-matter fields:
- `title` (Dublin Core `dc:title`)
- `domain` (domain slug)
- `description` (Dublin Core `dc:description`)
- `keywords` (array)
- `created` (Dublin Core `dc:created`, ISO 8601)
- `updated` (Dublin Core `dc:modified`, ISO 8601)
- `validated-by` (Dublin Core `dc:contributor`)
- `validated-on` (ISO 8601; null if not yet validated)
- `status` (`draft` | `active` | `deprecated`)

**Consequences (testable):**
- A PR that introduces a Context Document missing any required field MUST fail the schema validation check.
- A document with `status: deprecated` MUST still be retrievable but MUST be flagged in API responses.

**Out of Scope:** Rich text formatting, embedded images, or binary attachments in Phase 1.

#### FR-2: JSON-LD sidecar generation

The Ingestion Pipeline MUST generate a machine-readable sidecar file for each Context Document on merge, serializing the document's metadata using the selected open knowledge representation defined in `addendum.md`.

**Consequences (testable):**
- Every merged Context Document MUST have a corresponding `.jsonld` file in the same directory within one pipeline run.
- The generated sidecar file MUST validate against the selected metadata representation without errors.

---

### 4.2 Ingestion Pipeline (GitHub-Compatible Automation)

**Description:** On merge to `main`, a GitHub-compatible automation workflow runs three steps in sequence: schema validation, conflict detection, and graph population. For the pilot, the workflow SHOULD be runnable locally or in a GitHub-compatible way to support demos and rapid iteration. Conflict detection is a blocking quality gate in the pilot. Realizes UJ-2.

**Functional Requirements:**

#### FR-3: Schema validation step

On every PR targeting `main`, a validation workflow MUST check all new or modified Context Documents against the front-matter schema (FR-1).

**Consequences (testable):**
- PRs with schema violations MUST fail with a check that names the offending field(s) and file(s).
- Valid PRs MUST pass this check without manual intervention.

#### FR-4: Conflict detection step

On every PR targeting `main`, a conflict detection workflow MUST compare incoming Context Documents against existing documents in the same Domain using an automated comparison approach suitable for domain-document conflicts.

**Consequences (testable):**
- A PR introducing a document with a claim that contradicts an existing document in the same Domain MUST fail with a conflict report naming both files and the conflicting statements.
- The conflict threshold MUST be configurable via a repository variable to allow tuning without code changes.
- The conflict check MUST block merge to `main` until the Conflict is resolved or explicitly overridden.
- A Domain Owner MUST be able to override a false-positive conflict by adding a `conflict-override: justified` field to the PR description; this override MUST be logged.

#### FR-5: Graph population step

On merge to `main`, a post-merge workflow MUST extract Keywords from each new/modified Context Document and upsert Concept nodes, Document nodes, and their relationships into the Knowledge Graph.

**Consequences (testable):**
- Within 5 minutes of a merge, querying the Retrieval API with a Keyword from the merged document MUST return that document.
- Re-running the pipeline on an unchanged document MUST be idempotent (no duplicate nodes).

---

### 4.3 Retrieval API

**Description:** A lightweight containerized Go API exposes keyword-based search over the Knowledge Graph. Phase 1 only needs to prove the retrieval loop works end-to-end; production hardening remains future scope. Realizes UJ-1.

**Functional Requirements:**

#### FR-6: Keyword query endpoint

The API MUST expose a `GET /context?keyword={term}&domain={domain-slug}` endpoint that queries the Knowledge Graph and returns matching Context Documents.

**Consequences (testable):**
- A query with a known Keyword MUST return at least the matching Context Document(s) within 2 seconds (p95).
- A query with no matching results MUST return an empty array and HTTP 200 (not 404).
- The response MUST include: document `slug`, `title`, `domain`, `status`, `validated-on`, and a `body_excerpt` (first 500 characters of the markdown body).
- [ASSUMPTION: Phase 1 API can run without end-user authentication if repository and container access are appropriately controlled for the pilot.]

#### FR-7: Conflict flag in API response

If a retrieved Context Document has an unresolved Conflict logged against it, the API response MUST include a `conflict_flag: true` field and a `conflict_summary` string.

**Consequences (testable):**
- Querying a document with an active unresolved Conflict MUST surface the conflict flag.
- Agents receiving a conflict-flagged response MUST be able to detect and surface it to the user.

---

### 4.4 Agent Creation Script

**Description:** A CLI script that asks a contributor 3–4 questions and outputs a ready-to-use Agent Config file wiring the agent to the Retrieval API for a chosen Domain. Designed for engineers who have never configured an agent. Realizes UJ-1.

**Functional Requirements:**

#### FR-8: Interactive agent creation

The script MUST prompt for:
1. Agent name (free text)
2. Domain to scope (select from list of active Domains)
3. Task type (`implementation-guidance` | `conflict-detection` | `validation-support`)
4. Output format (`github-copilot-agent` | `openai-assistants` | `generic-mcp`)

It MUST then generate an Agent Config file that includes the Retrieval API endpoint, domain scope, task instructions referencing the shared context, and fallback behavior for empty results.

**Consequences (testable):**
- A user running the script with no prior knowledge MUST be able to complete all prompts and have a working agent config within 5 minutes.
- The generated config MUST successfully query the Retrieval API in a smoke test run immediately after generation.

---

### 4.5 Manual Contribution Workflow (Phase 1)

**Description:** Contributors add or update Context Documents by forking the repo, editing or creating markdown files, and raising a PR. Domain Owners review and approve. A contribution guide (`CONTRIBUTING.md`) and a document template are provided. Realizes UJ-3.

**Functional Requirements:**

#### FR-9: Document template

The repository MUST include a `CONTRIBUTING.md` and a `/templates/context-document-template.md` with all required front-matter fields pre-populated with inline instructions.

**Consequences (testable):**
- A contributor using only the template and CONTRIBUTING.md MUST be able to author a valid Context Document that passes schema validation without additional help.

#### FR-10: Domain Owner assignment

Each Domain MUST have at least one named Domain Owner defined in a `CODEOWNERS` file scoped to the domain's folder path.

**Consequences (testable):**
- A PR to `/domains/user-authentication/` MUST automatically request review from the User Authentication Domain Owner.

---

## 5. Non-Goals (Explicit)

- **Real-time collaborative editing** — the system is PR-driven and asynchronous by design.
- **Replacing SharePoint or Confluence in Phase 1** — the pilot coexists alongside existing systems; migration tooling is Phase 2+.
- **Automated import of existing SharePoint/Confluence content in Phase 1** — identified as a high-leverage future step; manual seeding is acceptable for the pilot.
- **React UI** — Phase 3.
- **Multi-domain coverage** — Phase 1 is scoped to User Authentication only.
- **Vector/semantic search** — Phase 1 uses keyword-graph retrieval only; embedding-based semantic search is a Phase 2+ enhancement.
- **Role-based access control on the API** — Phase 2.
- **Agent marketplace or agent registry** — outside scope.

---

## 6. MVP Scope

### 6.1 In Scope (Phase 1 Pilot)

- GitHub repository with defined folder structure and document schema (FR-1).
- JSON-LD sidecar generation on merge (FR-2).
- GitHub-compatible automation for schema validation (FR-3), conflict detection (FR-4), and graph population (FR-5), with local-first pilot execution supported.
- Containerized graph database deployment as the Knowledge Graph.
- Containerized Go Retrieval API: keyword query endpoint (FR-6) and conflict flag (FR-7).
- Agent creation script (FR-8).
- Contribution guide + document template (FR-9).
- CODEOWNERS-based Domain Owner assignment (FR-10).
- Seed content: minimum 5 User Authentication Context Documents to make the pilot non-trivially demonstrable.
- Metrics collection: API request logging sufficient to track SM-1 through SM-4.

### 6.2 Out of Scope for MVP

- SharePoint/Confluence import tooling [deferred to a later phase — identified as high-leverage but not required to prove the concept].
- API authentication and rate limiting [Phase 2].
- Web-based contribution UI [Phase 3]. `[NOTE FOR PM]` — perceived-usability constraint identified in discovery; Phase 3 is emotionally load-bearing for non-developer adoption.
- Multi-domain expansion [Phase 2 — begin after pilot acceptance tests pass].
- React search UI [Phase 3].
- Automated conflict resolution suggestions [Phase 2+].
- Semantic/vector search [Phase 2+].
- SKOS taxonomy browser [Phase 2+].

---

## 7. Success Metrics

**Primary**

- **SM-1**: Agent creation time — a user with no prior knowledge completes the agent creation script and has a functioning agent within 5 minutes. Target: 100% of pilot users. Validates FR-8.
- **SM-2**: Retrieval speed — keyword query returns results in ≤ 2 seconds (p95). Target: maintained under normal pilot load. Validates FR-6.
- **SM-3**: User engagement — pilot users voluntarily browse and contribute Context Documents without being prompted. Target: ≥ 3 unsolicited contributions within the first 30 days. Validates FR-9, FR-10.

**Secondary**

- **SM-4**: Conflict detection precision — proportion of conflict flags that are genuine conflicts (not false positives), as reviewed by Domain Owners. Target: ≥ 70% precision in pilot. Validates FR-4.
- **SM-5**: Ingestion pipeline reliability — proportion of merges that complete the full ingestion pipeline (validation → conflict check → graph population) without manual intervention. Target: ≥ 95%. Validates FR-3, FR-4, FR-5.
- **SM-6**: Cross-functional discovery — at least one non-developer (business or ops role) queries the API or browses the repository for domain information within 30 days.

**Counter-metrics (do not optimize)**

- **SM-C1**: Conflict override rate — proportion of conflict flags overridden by Domain Owners. Should stay low (< 20%); high override rate signals the conflict threshold is too aggressive or the extracted keywords are poor quality. Counterbalances SM-4.
- **SM-C2**: Contribution friction — time for a non-developer to author and submit a valid Context Document. Should not increase as content grows; rising friction signals the template or process is too complex. Counterbalances SM-3.

---

## 8. Open Questions

1. Which GitHub-compatible execution path should be used in rollout: hosted GitHub Actions, self-hosted runners, or a hybrid model?
2. What parity checks will be required to prove local automation and rollout automation behave equivalently?

---

## 9. Assumptions Index

- **§4.3 / FR-6**: Phase 1 API can run without end-user authentication if repository and container access are appropriately controlled for the pilot.
- **§1 / Discovery**: The knowledge format should be a loose interpretation guided by markdown files and directory structure while staying close to open standards; exact metadata mapping lives in `addendum.md`.
- **§6.1**: Pilot domain is User Authentication only; multi-domain expansion begins after pilot acceptance tests pass.
- **§4.2 / FR-4**: The selected automated conflict detection approach is acceptable in GitHub-compatible automation and not blocked by org package or network restrictions (OQ-3).
- **§1**: GitHub is the fixed platform; no migration to other VCS.
- **§4.3 / §6.1**: Phase 1 Retrieval API is implemented in Go and deployed in containers.
- **§1 / §6.1**: The pilot should run as much as possible locally for demoability and ease of early adoption, while preserving GitHub integration patterns for later rollout.
- **§4.5 / FR-10**: Mindcraft acts as the effective pilot domain owner for User Authentication review and approval workflow.
- **§6.1 / §7**: The available GitHub plan is assumed sufficient for pilot-scale activity; limits are monitored and addressed before rollout.
- **§4.2 / §6.1**: NLP libraries used for keyword/conflict workflows are assumed acceptable in the pilot environment; formal governance validation is a rollout gate.
