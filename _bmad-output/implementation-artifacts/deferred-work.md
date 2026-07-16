# Deferred Work

## Deferred from: code review of 2-4-build-deterministic-index-graph-upsert-pipeline-with-freshness-sla (2026-07-14)

- Freshness deadline stamped before push/rebase completes — `freshness_deadline_utc` is computed inside `build_index.py` at generation time, before the workflow's `git pull --rebase` + `git push` steps run; the manifest can't fully prove SLA compliance for commit/push latency. Inherent tension in any git-commit-as-publish-mechanism; no clean fix without restructuring the publish flow.
- `_source_path_str`'s absolute-path fallback would break determinism — if `md_path.relative_to(docs_dir.parent)` ever fails, it falls back to an absolute POSIX path, but this is unreachable with the current fixed workflow invocation (`--docs-dir docs` from repo root). Latent risk if invocation args change.
- `--source-commit` silently accepts and persists an empty string with no validation — only reachable via non-standard manual invocation; the production workflow always passes `${{ github.sha }}`.
- `index` output directory hardcoded independently in two places — `build_index.py --output-dir index` in the build step and `git add index/index.json index/build-manifest.json` in the commit step, with no shared source of truth.
- `_audit` exclusion matches any path segment literally named `_audit` anywhere under `docs/`, not scoped to the documented `docs/_audit/conflict-overrides/` location.
- No duplicate-`id` detection across parsed documents — currently unreachable since `id` derives from each file's unique path, but no defensive check exists if that assumption breaks.

## Deferred from: code review of 2-3-add-domain-owner-conflict-override-with-audit-logging (2026-07-14)

- No `actions/setup-python`/PyYAML install step in CI — `detect_conflicts.py` imports `yaml`, but the workflow's `unit-tests` job has no `actions/setup-python` or `pip install` step; relies on the runner image having PyYAML preinstalled. Predates this story — introduced in Story 2.2.
- `CONFLICT_REPORT_PATH` env var branch in `main()`'s output-path resolution is dead code — the workflow never sets this variable, so the branch is unreachable and untested. Predates this story (Story 2.2).
- Threshold default `"0.50"` duplicated independently in the workflow bash fallback and `parse_threshold()` — the two defaults can drift out of sync if only one is updated. Predates this story (Story 2.2).
- No `permissions:` block on workflow jobs — already identified and deferred as pre-existing in Story 2.2's review.
- `/tmp` vs `$RUNNER_TEMP_DIR` inconsistency for the changed-docs file list — already identified and deferred as pre-existing in Story 2.2's review.
- `cat "${REPORT_PATH}"` can mask the real exit code if the report write itself fails before reaching that line — same script/workflow pattern established in Story 2.2.

## Deferred from: code review of 2-2-implement-blocking-conflict-detection-with-tunable-threshold (2026-07-10)

- `/tmp` vs `$RUNNER_TEMP` inconsistency for changed-docs file list — `changed-context-docs.txt` uses hardcoded `/tmp/`; conflict output uses `$RUNNER_TEMP`. Pre-existing pattern from story 2.1; fix if self-hosted concurrent runners are added.
- `Path.cwd()` as repo root is invocation-directory-dependent — `detect_conflicts()` uses `Path.cwd()` for repo root; paths are wrong if invoked from a subdirectory. CI is always safe. Add `--repo-root` flag as a future cleanup.
- Missing CODEOWNERS produces confusing grep error — `grep -q '@OWNER_GITHUB_USERNAME' .github/CODEOWNERS` with `set -euo pipefail` gives a cryptic "No such file" error; add a file-existence guard when hardening the workflow.
- `--help` exits code 2 instead of 0 — non-standard POSIX behavior; no CI impact, cosmetic fix for future CLI polish.
- No `permissions:` block on workflow jobs — all jobs should declare `contents: read` for least-privilege posture; pre-existing pattern to address in a workflow hardening pass.

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
