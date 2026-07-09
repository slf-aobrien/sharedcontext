---
id: SPEC-bmadSharedContext
companions:
  - ../planning-artifacts/ux-designs/ux-bmadSharedContext-2026-07-07/DESIGN.md
  - ../planning-artifacts/ux-designs/ux-bmadSharedContext-2026-07-07/EXPERIENCE.md
  - ../planning-artifacts/architecture/architecture-bmadSharedContext-2026-07-08/ARCHITECTURE-SPINE.md
sources:
  - ../planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/prd.md
  - ../planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/addendum.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability only — consult them only if you need narrative rationale this contract intentionally omits.

# Shared Context System Pilot for Domain Knowledge and Agent Skills

## Why

The pilot exists to prove that organization-vetted domain knowledge can be reliably consumed by AI agents and humans from a GitHub-native workflow, specifically for User Authentication. This work matters now because agents without grounded context can produce conflicting or non-compliant guidance, while teams currently lose accuracy and time across fragmented knowledge sources.

## Capabilities

- **CAP-1**
  - **intent:** Contributors can author and review domain context documents in GitHub using a required metadata schema and owner-based review.
  - **success:** PRs with missing required metadata fail with file and field diagnostics; schema-valid PRs pass and can merge.

- **CAP-2**
  - **intent:** The system can detect contradictory domain claims before merge.
  - **success:** PRs with unresolved conflicts are blocked and report both source files and conflicting statements until resolved or explicitly justified override is recorded.

- **CAP-3**
  - **intent:** Newly merged context can be retrieved quickly by keyword and domain.
  - **success:** A known keyword query returns matching document payload (including status and validation freshness fields) in under 2 seconds p95, and within 5 minutes of merge.

- **CAP-4**
  - **intent:** Engineers can create a context-aware agent without manual endpoint wiring.
  - **success:** The agent creation script generates a working config and passes an immediate retrieval smoke check in under 5 minutes.

- **CAP-5**
  - **intent:** Domain owners can maintain trust freshness of context artifacts.
  - **success:** Validation metadata updates through standard PR flow and retrieval responses expose stale or fresh validation status.

## Constraints

- Phase 1 scope is strictly the User Authentication domain.
- Authored source of truth is markdown in a GitHub repository, governed by PR review and CODEOWNERS.
- Phase 1 acceptance model is index-as-artifact persistence consumed by the Go retrieval API; a live Neo4j runtime is optional and deferred for correctness-critical scope.
- Retrieval runtime is a containerized Go API with explicit empty-result behavior.
- Conflict detection is a blocking, configurable, and auditable PR quality gate.
- Each merged context document must produce machine-readable JSON-LD sidecar metadata.

## Non-goals

- Real-time collaborative editing and standalone web authoring UI in MVP.
- Multi-domain rollout, semantic vector retrieval, and production RBAC in Phase 1.
- Automated SharePoint/Confluence import during the pilot.

## Success signal

A full pilot cycle demonstrates all of the following: an engineer creates a working context-aware agent in under 5 minutes, retrieval returns known keyword context in under 2 seconds p95, conflicts are intercepted before merge, and contributors voluntarily continue adding validated User Authentication knowledge.

## Assumptions

- Phase 1 retrieval access can remain controlled through repository and container boundary controls without introducing end-user authentication.
