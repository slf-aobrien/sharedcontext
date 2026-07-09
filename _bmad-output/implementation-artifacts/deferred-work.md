# Deferred Work

## Deferred from: code review of 2-1-generate-json-ld-sidecars-on-merge (2026-07-09)

- Multi-commit push (≥2 commits) triggers `find docs` fallback which processes `docs/user-authentication/index.md` (no front-matter); generator exits 1, CI step fails. Resolves when `index.md` is updated with valid front-matter.
- `/tmp/changed-docs.txt` not run-scoped; concurrent jobs on self-hosted runners can race and corrupt the file list. Hosted runners get fresh containers so this is low priority; fix with `$RUNNER_TEMP` or a per-run unique name if self-hosted runners are added.
- `actions/checkout@v4` pinned to a floating tag, not a commit SHA — supply-chain risk. SHA-pin before production hardening.
- Non-atomic sidecar write: `write_text()` is not atomic; SIGKILL mid-write leaves partial `.jsonld`. Fix with temp file + `os.replace()` when write reliability becomes a requirement.
- `contentStatus` is not a schema.org vocabulary term; the correct schema.org property is `schema:creativeWorkStatus`. Changing this breaks the AD-7 sidecar contract; requires coordinated update with Story 2.4 index builder and Epic 3 Go retrieval API.

## Deferred from: code review of 1-4-configure-domain-ownership-with-codeowners (2026-07-09)

- Catch-all `*` will require owner review on all PRs including planning artifacts — by-design per spec with acknowledged operational caveat in CODEOWNERS comment; narrow if review noise becomes a problem.
- `templates/` directory lacks dedicated CODEOWNERS entry — a PR modifying the canonical contribution template triggers only the catch-all, not a domain-specific review path; mitigated by catch-all but worth a dedicated entry when governance matures.
- `_bmad/schemas/` and `_bmad/scripts/` covered only by catch-all — the authoritative schema and validator can be weakened without governance-specific review; covered by catch-all for now.
- CODEOWNERS paths and `pr-validate.yml` diff filter can drift independently — comment warns about this invariant but no CI check enforces it; mitigate when adding new domains.
- Case sensitivity: CODEOWNERS pattern `docs/user-authentication/` won't match case variants on GitHub's Linux runtime — low risk as path convention is documented.
- Other `.github/` files (ISSUE_TEMPLATE, pull_request_template, etc.) not in infrastructure guard — covered by catch-all but not domain-explicitly owned.
- Validator commands in CONTRIBUTING.md assume CWD is repo root with no explicit guard — pre-existing from story 1.2; add a note when updating CONTRIBUTING.md.
- Status check name `Validate context document front matter` loosely coupled to the workflow job's `name:` field — pre-existing design dependency from story 1.3; renaming the job will break or freeze branch protection.
- `domain` enum Phase 1 constrained with no Phase 2 migration path documented — pre-existing from story 1.2; needs a schema migration plan before adding new domains.
- `validated-on: null` permitted for `status: active` documents without cross-field enforcement — pre-existing schema design gap.
- `updated` field staleness undetected by CI — pre-existing; validator could check that `updated` changed on each PR.
- Windows compatibility gaps in shell commands (`cp`, bash heredoc in gh api step) — pre-existing from story 1.2.
- `validated-by` conflates authorship with validation semantics — pre-existing schema design; revisit field semantics when formal validation workflow is defined.
- No branch naming or commit message conventions documented — governance gap for future contributor guidance.

## Deferred from: code review of 1-3-implement-pr-schema-validation-workflow (2026-07-08)

- No enforcement for PR description validator output — CONTRIBUTING.md instructs contributors to include validator output in their PR description, but there is no automated check, PR template, or enforcement mechanism; will be ignored over time.
- Fallback branch validates all `docs/*.md` when BASE_SHA is unreachable — intentional documented behavior, but could surprise contributors whose PRs are blocked by pre-existing broken docs they didn't author.
- No workflow concurrency control (`concurrency:` key absent) — multiple simultaneous PRs each trigger independent runs; benign for current traffic but an unaddressed operational pattern.
- `fetch-depth: 0` full-history fetch — technically correct for ensuring BASE_SHA reachability, but expensive as repo grows; a targeted fetch strategy is a future optimization.

## Deferred from: code review of 1-2-create-contribution-template-and-guidance (2026-07-08)

- Unfilled `<…>` placeholder strings pass schema validation — the validator cannot detect unfilled template tokens; would require a validator enhancement to check for `<...>` pattern in field values.
- Proof fixture `sample-valid-template-derived.md` not referenced in CONTRIBUTING.md — low value addition; fixture serves as proof, not a contributor reference.
- No lifecycle guidance for `status` progression from `draft` to `active` — governance workflow (who can promote, when to set `validated-on`) is out of Story 1.2 scope.
- `domain` value not enforced by validator — any string passes; schema constraint on allowed domain values is a validator/schema enhancement for a future story.
- `status: active` + `validated-on: null` cross-field inconsistency not enforced — schema cross-field constraint out of Story 1.2 scope.
- Empty/whitespace keyword item error messages absent from error table — obscure edge case; validator messages `"must be a non-empty list of strings"` / `"must contain only non-empty strings"` have no matching rows in the CONTRIBUTING.md error table.
- RFC3339 variant handling (fractional seconds, timezone offset) not specified — edge case for contributors who know RFC3339 variants; existing guidance (`YYYY-MM-DDTHH:MM:SSZ`) is unambiguous for normal use.
- `updated` before `created` passes validation — temporal ordering cross-field constraint is a schema enhancement out of Story 1.2 scope.
