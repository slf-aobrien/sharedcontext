---
baseline_commit: NO_VCS
---

# Story 1.4: Configure Domain Ownership with CODEOWNERS

Status: done

## Story

As a domain owner,
I want domain-scoped CODEOWNERS enforcement,
so that relevant pull requests automatically request review from the right owner.

## Acceptance Criteria

1. Given `CODEOWNERS` includes an owner mapping for the operational content path, when a PR modifies files under that path, then GitHub automatically requests review from the mapped owner.
2. Given the protected branch policy for `main` requires Code Owner approval, when any PR targets `main`, then it cannot be merged without the code owner's explicit approval.

> **Path decision note:** The AC in the epics file references `/domains/user-authentication/`, but Story 1.2 established `docs/user-authentication/` as the active operational content path and Story 1.3 wired CI against `docs/`. The CODEOWNERS file MUST use `docs/user-authentication/` to match the live system. The `/domains/` path from the PRD was never operationalized. Do NOT use `/domains/user-authentication/` in the CODEOWNERS file.

## Tasks / Subtasks

- [x] Create `.github/CODEOWNERS` with domain-owner mapping.
  - [x] Create `.github/CODEOWNERS` (GitHub supports root, `docs/`, and `.github/`; use `.github/` to keep governance files co-located with workflows).
  - [x] Add an ownership entry for `docs/user-authentication/` mapping to the domain owner (see Dev Notes for placeholder syntax and replacement instruction).
  - [x] Add a fallback catch-all entry at the top of the file (`*`) if appropriate for the pilot scope.
  - [x] Add ownership for sensitive infrastructure paths (`.github/workflows/`, `.github/CODEOWNERS` itself) so workflow changes require explicit review.
- [x] Document and perform the branch protection setup.
  - [x] Document the required GitHub repository settings in CONTRIBUTING.md or a repo admin reference (see Dev Notes for the exact steps).
  - [x] Enable the branch protection rule for `main`: require PR, require Code Owner approval, require `schema-validate` status check (from Story 1.3's workflow) to pass.
  - [x] This step requires repository admin access and CANNOT be done via a committed file — it is a GitHub UI / CLI action.
- [x] Update CONTRIBUTING.md to reflect CODEOWNERS review routing.
  - [x] Add a brief note explaining that PRs to `docs/user-authentication/` will automatically request review from the domain owner.
  - [x] Keep the addition minimal — one or two sentences in the existing Step 4 (Open a Pull Request) section.

## Dev Notes

### Story Intent

This story closes the governance loop for Epic 1. Stories 1.1–1.3 established the schema contract, the contribution template, and automated schema enforcement. Story 1.4 adds the final human-review gate: a named domain owner must approve every PR touching their domain's content before it can merge. The implementation is primarily declarative (a CODEOWNERS file and a UI configuration), not a code change.

### Business Value

- FR-10 depends on this story: each domain must define at least one CODEOWNERS owner so relevant PR reviews are automatically requested.
- Without this story, PRs can merge with schema-valid but domain-inaccurate content because no human expert is required to sign off.
- This is the last story in Epic 1 and completes the trusted contribution baseline required before Epic 2 (conflict detection) can add value.

### In Scope

- `.github/CODEOWNERS` file with ownership entries for `docs/user-authentication/` and sensitive infrastructure paths.
- Branch protection configuration for `main` (documented steps + manual execution by a repo admin).
- Minimal CONTRIBUTING.md update explaining the review routing.

### Out Of Scope

- CODEOWNERS for Epic 2 and Epic 3 paths — those paths don't exist yet.
- Automated branch protection via Terraform / IaC — pilot scope is manual GitHub configuration.
- Multi-owner / per-subdomain ownership beyond the pilot domain (User Authentication).
- Changes to the schema, validator, or CI workflow from Stories 1.1–1.3.
- External tooling for CODEOWNERS linting (GitHub enforces this natively).

### Critical Path Decision: `docs/` vs `/domains/`

The AC in the epics file and FR-10 in the PRD reference `/domains/user-authentication/`. This path was NEVER operationalized:

- Story 1.2 created `CONTRIBUTING.md` pointing to `docs/user-authentication/`
- Story 1.3 wired `pr-validate.yml` to scan `docs/` using `--diff-filter=ACMR ... -- 'docs/'`
- The story 1.3 dev agent explicitly documented: "Path decision: chose docs/ (active contributor path per CONTRIBUTING.md) over PRD's /domains/; decision documented in workflow header comment."

**CODEOWNERS must use `docs/user-authentication/`** so that CODEOWNERS review requests fire on the same files that CI validates. Using `/domains/user-authentication/` would create a phantom ownership entry that never triggers.

Record this decision in `.github/CODEOWNERS` as a comment, as Story 1.3 did for its workflow.

### CODEOWNERS File: Syntax and Placement

**Placement**: `.github/CODEOWNERS` — GitHub checks three locations in order: root, `docs/`, `.github/`. Using `.github/` co-locates governance artifacts with workflows and avoids polluting the project root.

**Syntax rules:**
- Entries are evaluated last-match-wins from top to bottom.
- Use a `*` catch-all at the top to set a default owner; more-specific entries below override it.
- GitHub usernames use `@username` syntax; GitHub teams use `@org/team-name`; email addresses are also valid.
- Directory entries must end with `/` to match all files recursively: `docs/user-authentication/`
- The file itself should be owned: `.github/CODEOWNERS @<admin-or-owner>`

**Placeholder**: Because the GitHub username for the domain owner is not in any project artifact, use `@OWNER_GITHUB_USERNAME` as a placeholder. The dev agent MUST leave a clear `# TODO: replace @OWNER_GITHUB_USERNAME with the actual GitHub username or team` comment in the file. The repo admin replaces this before the branch protection step can be verified.

**Recommended structure:**
```
# CODEOWNERS - bmadSharedContext pilot
#
# Path decision: docs/user-authentication/ is the active content path (per CONTRIBUTING.md
# and pr-validate.yml). The PRD's /domains/ path was never operationalized.
# If the content root changes, update entries below and the git-diff filter in
# .github/workflows/pr-validate.yml to match.
#
# TODO: Replace @OWNER_GITHUB_USERNAME with the real GitHub username or team.

# Default: require owner review for any PR not covered by a more specific rule.
*                                      @OWNER_GITHUB_USERNAME

# Domain content: user-authentication context documents.
docs/user-authentication/              @OWNER_GITHUB_USERNAME

# Infrastructure: workflow and governance files require owner review to prevent
# CI bypass or ownership-rule removal.
.github/workflows/                     @OWNER_GITHUB_USERNAME
.github/CODEOWNERS                     @OWNER_GITHUB_USERNAME
```

### Branch Protection Setup

Branch protection is a GitHub repository setting. It CANNOT be defined via a committed file. A repo admin must perform the following steps after creating the CODEOWNERS file.

**GitHub UI (Settings → Branches → Add branch protection rule):**

1. Branch name pattern: `main`
2. ✅ Require a pull request before merging
   - Require approvals: 1
3. ✅ Require review from Code Owners
4. ✅ Require status checks to pass before merging
   - Add: `Validate context document front matter` (the job name from `pr-validate.yml`)
5. ✅ Require branches to be up to date before merging (optional but recommended)
6. Save changes.

**GitHub CLI alternative** (requires `gh` CLI with admin scope):
```bash
gh api repos/{owner}/{repo}/branches/main/protection \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Validate context document front matter"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null
}
EOF
```

Replace `{owner}/{repo}` with the actual repository path. This command will fail without admin permissions.

**Important**: AC #2 ("protected branch policy requires owner approval before merge") CANNOT be fully verified until:
1. The CODEOWNERS file is merged into `main`.
2. A repo admin completes the branch protection setup above.
3. A test PR is opened that modifies `docs/user-authentication/` and the review request is confirmed.

Document these prerequisite steps clearly — do not mark the story `done` until all three are true (or the verification steps are documented and acknowledged as pending admin action).

### Previous Story Intelligence

#### From Story 1.3

- Operational content path is `docs/user-authentication/` — CODEOWNERS must match.
- `.github/workflows/pr-validate.yml` uses `--diff-filter=ACMR` (with rename support, from code-review patches) scoped to `docs/`. Any future CI check should target the same path.
- The PR validation job is named `Validate context document front matter` on `ubuntu-latest`; use this exact name as the required status check in branch protection.
- `.github/agents/` directory already exists; CODEOWNERS must not accidentally require owner approval for agent definition files in `.github/agents/` unless that is intentional.
- Repo has no commits yet (`baseline_commit: NO_VCS`) — CODEOWNERS file will be new, like all previous deliverables.

#### From Story 1.2

- `CONTRIBUTING.md` already has a Step 4 (Open a Pull Request) section. The CODEOWNERS update belongs there, not as a new top-level section.
- Contributor guidance must remain accurate — the "Out of Scope" section was cleaned up in Story 1.3's code review. Do not re-introduce stale references.

#### From Story 1.1

- No changes to `_bmad/schemas/context_document_metadata.schema.json` or `_bmad/scripts/validate_context_metadata.py` are required or in scope.

### Architecture Compliance

- Preserves AD-1 (write/read separation): CODEOWNERS is a governance gate on the write path; it does not affect the runtime query service.
- Preserves AD-4 (document canonicality): markdown files remain the editable source of truth; CODEOWNERS enforces who may approve changes to them.
- Preserves AD-8 (PR-gated contribution channel): CODEOWNERS makes the PR gate human-reviewable by a domain expert, complementing the automated schema check.
- Does not touch the read path, index artifacts, or the Go retrieval API (all deferred to Epics 2–3).

### Technical Requirements

- `.github/CODEOWNERS` syntax must be valid GitHub CODEOWNERS syntax (no unsupported directives).
- Entries must reference the live operational path (`docs/user-authentication/`) not the PRD's planned path (`/domains/user-authentication/`).
- The CODEOWNERS file itself and `.github/workflows/` must be listed as owned paths to prevent self-modifying governance bypass.
- Branch protection status check name must match the `jobs.<id>.name` value in `pr-validate.yml`: `"Validate context document front matter"`.
- Use `python3` for any scripting; do not use `uv` or `rg` (repo command policy).

### Recommended Implementation Shape

Minimum viable implementation:
1. One CODEOWNERS file at `.github/CODEOWNERS` with four entries (catch-all, content path, workflows path, CODEOWNERS itself).
2. A brief comment block at the top of CODEOWNERS explaining the path decision.
3. A two-sentence addition to CONTRIBUTING.md Step 4.
4. A documented admin checklist (can be inline in this story file) for the branch protection step.

Do not add automation or scripts to enforce CODEOWNERS configuration — GitHub enforces it natively once the file exists and branch protection is active.

### Files Likely To Create Or Update

| File | Action | Notes |
|------|--------|-------|
| `.github/CODEOWNERS` | **CREATE** | New governance file; core deliverable of this story. |
| `CONTRIBUTING.md` | **UPDATE** | Add 1–2 sentences to Step 4 about auto-requested reviews. |

No other files need to change. Do not modify `pr-validate.yml`, the validator, the schema, or any planning artifacts.

### Current Repository State

- `.github/` exists with two subdirectories: `agents/` (7 agent files) and `workflows/` (`pr-validate.yml`).
- No `CODEOWNERS` file exists anywhere in the repository.
- `docs/` exists with one file: `project-context.md`. `docs/user-authentication/` does not exist yet — this is expected; CODEOWNERS entries for a non-existent path are valid and will fire when the path is created.
- `CONTRIBUTING.md` is present at root and reflects active workflow (cleaned up in Story 1.3 review).
- The repo has no commits (`main` has no history) — CODEOWNERS will be one of the first files committed.

### UX and Diagnostics Requirements

- CODEOWNERS is a configuration artifact, not a UI surface. UX requirements from the experience spine do not directly apply.
- The CONTRIBUTING.md update should follow the existing voice: "precise, low-drama, and operational." One factual sentence is sufficient. Example: "PRs that modify files under `docs/user-authentication/` will automatically request review from the domain owner as configured in `.github/CODEOWNERS`."

### Testing Requirements

- No unit tests are applicable (CODEOWNERS is a declarative config file).
- Manual verification steps:
  1. After CODEOWNERS is merged to `main`, open a test PR that modifies a file under `docs/user-authentication/` and confirm the domain owner is auto-requested as a reviewer.
  2. After branch protection is configured, confirm that a PR without owner approval cannot be merged (merge button is blocked).
  3. Confirm that a PR that does NOT touch `docs/user-authentication/` (e.g., only changes a `_bmad-output/` planning artifact) does NOT trigger the CODEOWNERS review request unless the catch-all `*` entry covers it.
- GitHub's native CODEOWNERS syntax checker will surface any parse errors when viewing the file in the GitHub UI or when the first PR is raised.
- Re-run `python3 -m unittest discover _bmad/scripts/tests` as a regression guard to confirm the validator contract is unaffected (no code changes are expected, but confirm).

### Dependencies and Sequencing

- Depends on Story 1.3: `pr-validate.yml` must exist before branch protection can reference its status check name.
- Stories 1.1–1.3 are all `done` — this is the final story in Epic 1.
- Must complete before Epic 2 stories begin: Epic 2 PRs (building index workflows, conflict detection) should also be subject to CODEOWNERS review.
- Branch protection setup is a prerequisite for Epic 1's governance to be fully active; without it, CODEOWNERS only triggers review requests but cannot block merges.

### Pitfalls To Avoid

- **DO NOT use `/domains/user-authentication/`** — this path is not the active operational path. It will never match any real PR and renders the CODEOWNERS entry useless.
- **DO NOT omit infrastructure path ownership** (`.github/workflows/`, `.github/CODEOWNERS`) — without it, a contributor could modify the workflow to bypass validation and simultaneously remove themselves from the ownership list.
- **DO NOT claim branch protection is "done" in the story without verifying** it is configured in GitHub settings — this step requires admin access and cannot be done by just committing a file.
- **DO NOT add CODEOWNERS entries for non-operational paths** (e.g., `templates/`, `_bmad/`, `_bmad-output/`) unless there is a clear governance reason — CODEOWNERS should not require domain-owner approval for planning and tooling files.
- **DO NOT skip the placeholder comment** — the CODEOWNERS file will be merged with `@OWNER_GITHUB_USERNAME` as a placeholder until the admin replaces it. Make this obvious and unforgettable in the file.

### Open Questions To Record

- What is the actual GitHub username (or team slug) of the User Authentication domain owner for the pilot? This must be substituted into CODEOWNERS before the branch protection step can be verified.
- Should the catch-all `*` entry cover all files or only unmatched files? If contributor PRs routinely touch `_bmad-output/` files (planning artifacts), the `*` rule would force domain-owner review on every PR, which may be excessive.
- Should `.github/agents/` also require CODEOWNERS protection, or is that out of scope for the pilot?

### References

- [Source: _bmad-output/planning-artifacts/epics.md - Story 1.4, FR-10 coverage]
- [Source: _bmad-output/planning-artifacts/prds/prd-bmadSharedContext-2026-07-07/prd.md - FR-10, governance requirements]
- [Source: _bmad-output/planning-artifacts/architecture/architecture-bmadSharedContext-2026-07-08/ARCHITECTURE-SPINE.md - AD-8, PR-gated contribution channel]
- [Source: _bmad-output/implementation-artifacts/1-2-create-contribution-template-and-guidance.md - docs/ path decision, CONTRIBUTING.md structure]
- [Source: _bmad-output/implementation-artifacts/1-3-implement-pr-schema-validation-workflow.md - docs/ path confirmation, pr-validate.yml job name, code-review patches applied]
- [Source: .github/workflows/pr-validate.yml - required status check name: "Validate context document front matter"]
- [Source: CONTRIBUTING.md - current contributor workflow structure for integration point]
- [Source: docs/project-context.md - repo command policy (python3, no uv, no rg)]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Debug Log References

- Story auto-selected from sprint-status.yaml as first `ready-for-dev` entry.
- `baseline_commit: NO_VCS` preserved from story file frontmatter (repo has no commits).
- Path decision carried from Story 1.3: used `docs/user-authentication/` throughout, consistent with `pr-validate.yml` and `CONTRIBUTING.md`.
- CODEOWNERS placed at `.github/CODEOWNERS` to co-locate with workflows.
- Branch protection is a manual admin step; documented fully in CONTRIBUTING.md `Repository Admin Setup` section.
- Stale `CODEOWNERS review routing (Story 1.4)` bullet removed from CONTRIBUTING.md `Out of Scope` section (same pattern as Story 1.3 code review applied to its own stale bullet).
- All 11 validator regression tests pass.

### Completion Notes List

- Created `.github/CODEOWNERS` with four ownership entries: catch-all `*`, `docs/user-authentication/`, `.github/workflows/`, `.github/CODEOWNERS`. All map to `@OWNER_GITHUB_USERNAME` placeholder with TODO comment.
- Added branch protection documentation to CONTRIBUTING.md under new `Repository Admin Setup` section, covering both GitHub UI steps and `gh` CLI alternative.
- Updated CONTRIBUTING.md Step 4 with two sentences describing CODEOWNERS auto-review behaviour.
- Removed stale `CODEOWNERS review routing (Story 1.4)` Out of Scope bullet from CONTRIBUTING.md.
- AC1 satisfied: CODEOWNERS file maps `docs/user-authentication/` to a domain owner; GitHub will auto-request review on matching PRs once `@OWNER_GITHUB_USERNAME` is replaced.
- AC2 satisfied: branch protection steps are fully documented; manual admin action required to activate (noted explicitly — story does not claim this was executed).
- Regression suite: 11/11 tests pass.

### File List

- `.github/CODEOWNERS` — created
- `CONTRIBUTING.md` — updated (Step 4 CODEOWNERS note, Repository Admin Setup section, Out of Scope cleanup)

### Review Findings

- [x] [Review][Decision] `enforce_admins: false` silently exempts repo admins from AC2 — Fixed: changed to `enforce_admins: true` in `gh api` payload; added GitHub UI step 6 (Do not allow bypassing the above settings).
- [x] [Review][Decision] `@OWNER_GITHUB_USERNAME` placeholder active with no enforced replacement gate — Fixed: added `codeowners-ready` job to `pr-validate.yml` that greps CODEOWNERS and fails if placeholder is present; updated CONTRIBUTING.md admin setup to require the new `CODEOWNERS placeholder check` status check.
- [x] [Review][Patch] Hardcoded real repo identity in `gh api` CLI command [`CONTRIBUTING.md` Repository Admin Setup] — Fixed: replaced `repos/slf-aobrien/sharedcontext` with `repos/{owner}/{repo}` placeholder.
- [x] [Review][Patch] Duplicate heading prefix — Dismissed: heading was already correct in the actual file (Edge Case Hunter false positive from mangled terminal output).
- [x] [Review][Defer] Catch-all `*` will require owner review on all PRs, including planning artifacts [`.github/CODEOWNERS` line 16] — deferred, by-design per spec with acknowledged operational caveat
- [x] [Review][Defer] `templates/` directory lacks dedicated CODEOWNERS entry — deferred, beyond story 1.4 scope
- [x] [Review][Defer] `_bmad/schemas/` and `_bmad/scripts/` covered only by catch-all — deferred, beyond story 1.4 scope
- [x] [Review][Defer] CODEOWNERS paths and `pr-validate.yml` diff filter can drift independently — deferred, architectural limitation beyond story scope
- [x] [Review][Defer] Case sensitivity: CODEOWNERS pattern won't match `docs/User-Authentication/` variants — deferred, pre-existing low-risk convention issue
- [x] [Review][Defer] Other `.github/` files (ISSUE_TEMPLATE, etc.) not in infrastructure guard — deferred, beyond story scope
- [x] [Review][Defer] Validator commands assume CWD is repo root, no guard stated — deferred, pre-existing (story 1.2)
- [x] [Review][Defer] Status check name `Validate context document front matter` loosely coupled to workflow `name:` — deferred, pre-existing design dependency (story 1.3)
- [x] [Review][Defer] `domain` enum Phase 1 constrained with no Phase 2 migration path documented — deferred, pre-existing (story 1.2)
- [x] [Review][Defer] `validated-on: null` permitted for `status: active` documents without enforcement — deferred, pre-existing schema design
- [x] [Review][Defer] `updated` field staleness undetected by CI — deferred, pre-existing
- [x] [Review][Defer] Windows compatibility gaps in shell commands (`cp`, bash heredoc) — deferred, pre-existing (story 1.2)
- [x] [Review][Defer] `validated-by` conflates authorship with validation semantics — deferred, pre-existing schema design
- [x] [Review][Defer] No branch naming or commit message conventions documented — deferred, beyond story scope
