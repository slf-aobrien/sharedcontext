# Addendum: Technical Direction

## Purpose

This addendum captures technical direction, standards choices, and implementation-oriented detail that informs architecture and delivery but does not belong in the PRD's main product narrative.

## Standards Posture

- The system should stay close to established open standards and common docs-as-code conventions.
- The intended interpretation of "Google's Open Knowledge Format" is loose rather than rigid: the repository structure and markdown documents are the primary authoring model, with machine-readable metadata layered on top.
- Preferred standards direction:
  - Markdown files as the source authoring format.
  - YAML front-matter as the native metadata envelope.
  - Dublin Core field naming for document metadata where it improves interoperability.
  - schema.org / JSON-LD for machine-readable structured metadata and export.
  - SKOS for keyword, taxonomy, and concept relationships when taxonomy depth is needed.

## Technical Preferences Confirmed

- GitHub is the fixed platform for authoring, review, and automation.
- The pilot should run as much as possible locally for demoability before broader rollout.
- The pilot should use containers from day one.
- The Retrieval API should be implemented in Go from day one.
- The pilot domain is User Authentication.
- Conflict detection should be a blocking PR check.

## Candidate Runtime Topology

- GitHub repository stores markdown knowledge documents.
- Local containers run the graph database and Go API for demo and pilot usage.
- GitHub-compatible automation validates schema, detects conflicts, extracts keywords, and updates the graph store.
- A containerized graph database stores document, concept, and relationship nodes.
- A containerized Go API serves keyword-based retrieval for agents and future UI consumers.

## Phase 1 Runtime Authority

- Phase 1 acceptance authority is the index-as-artifact model consumed by the Go Retrieval API.
- A live Neo4j runtime is an optional implementation path for pilot demos and future evolution, not a correctness requirement for Phase 1 acceptance.
- If runtime choices diverge across artifacts, the architecture spine acceptance model governs pilot pass/fail criteria.

## Local-First Pilot Posture

- Preferred pilot setup is a developer-runnable environment using containers and local configuration.
- GitHub remains the source of truth for documents, review, and merge control.
- Where direct GitHub-hosted execution is awkward for demos, local-compatible execution is acceptable as long as behavior matches the rollout path closely enough to avoid rework.
- The main product risk in local-first execution is drift between demo-time local automation and later GitHub-hosted automation; parity checks should be part of rollout readiness.

## Graph Database Direction

- Neo4j Community Edition is the current preferred implementation because it is mature, well understood, and fits entity/relationship traversal well.
- This remains an architecture preference rather than a product requirement; another graph database is acceptable if it preserves the same product behavior.

## Keyword / Conflict Detection Direction

- Candidate approaches discussed: YAKE or KeyBERT in GitHub Actions.
- Exact algorithm choice is an implementation decision.
- Product requirement is outcome-based: conflicts must be detected early enough to block inaccurate merges with usable diagnostics.

## Known Container Risks For The Pilot

- Persistence risk: container-local storage can lose graph data unless backed by a volume or external disk.
- Backup risk: pilot data still needs a simple backup/export plan.
- Resource contention: graph database and API performance may degrade on undersized hosts.
- Networking/secrets risk: GitHub Actions must be able to reach the running graph database securely.
- Upgrade drift: container image versions must be pinned to avoid unexpected behavior changes.

## Current Ownership Signal

- Mindcraft is the currently identified development owner for the pilot domain and delivery workflow.