---
baseline_commit: 74de78c
---

# Story 2.1: Generate JSON-LD Sidecars on Merge

Status: done

## Story

As a platform engineer,
I want each merged context document to produce a valid JSON-LD sidecar,
so that document metadata is machine-readable and interoperable for downstream tooling.

## Acceptance Criteria

1. Given a merge to `main` that adds or updates one or more context documents, when the post-merge ingestion workflow runs, then each changed document gets a corresponding `.jsonld` sidecar in the same directory as the source file.
2. Given a generated sidecar, when it is inspected, then it is well-formed JSON, contains `@context` and `@type`, includes all required metadata fields (`dc:title`, `dc:description`, `dc:subject`, `dc:created`, `dc:modified`, `dc:contributor`, `contentStatus`, `bsc:domain`, `bsc:validated_on`, `bsc:source_path`, `bsc:source_hash`), and was produced by the pipeline step with a zero exit code.
3. Given a document with missing or malformed front-matter fields, when the generator runs, then it exits non-zero, names the file and the specific cause in stderr, and does not produce a partial sidecar.

## Tasks / Subtasks

- [x] Create the sidecar generator script.
  - [x] Add `scripts/generate_jsonld.py` as the production pipeline script. Do NOT place it under `_bmad/` — that directory holds bmad infrastructure tools; this script is part of the publication pipeline.
  - [x] Accept one or more `.md` file paths as positional command-line arguments.
  - [x] For each file: parse YAML front-matter with `yaml.safe_load()`, compute SHA-256 `source_hash` over the full file bytes, build the JSON-LD document per the schema in Dev Notes, write the `.jsonld` sidecar alongside the `.md` file (same directory, same basename, extension replaced).
  - [x] Validate each generated sidecar before writing: confirm it is well-formed JSON, `@context` is present, `@type` is `DigitalDocument`, all required fields are non-null (except `bsc:validated_on` which is nullable).
  - [x] Wrap each file's processing in a try/except so a single bad file does not abort the batch. Collect all errors, continue to the next file, and exit 1 at the end if any file failed.
  - [x] Print `"Generated: <path>"` to stdout for each successful sidecar. Print errors to stderr.
  - [x] If invoked with no arguments, print usage and exit 1.

- [x] Create the post-merge ingestion workflow.
  - [x] Add `.github/workflows/build-index.yml`. This is the architecture spine's index-build workflow. This story creates it scoped to sidecar generation only; Stories 2.2–2.4 will extend it with conflict detection and index population.
  - [x] Trigger on `push: branches: [main]`.
  - [x] Add `concurrency:` block (do not repeat the omission from `pr-validate.yml`). Set `cancel-in-progress: false` — see Dev Notes for rationale.
  - [x] Add `permissions: contents: write` to allow committing generated sidecars back to main.
  - [x] Job `generate-sidecars` with `timeout-minutes: 10`.
  - [x] Step: `actions/checkout@v4` with `fetch-depth: 2` and `token: ${{ secrets.GITHUB_TOKEN }}`.
  - [x] Step: detect changed context documents in `docs/` using `git diff --name-only --diff-filter=ACMR` against the previous commit. Include a fallback to `find docs -type f -name '*.md'` if no reachable previous commit exists.
  - [x] Step: run `python3 scripts/generate_jsonld.py "${FILES[@]}"` for all detected changed docs.
  - [x] Step: configure `github-actions[bot]` git identity, stage all new/updated `.jsonld` files under `docs/`, and commit+push only if staged changes exist. Include `[skip ci]` in the commit message.
  - [x] Use explicit `shell: bash` on every multi-line `run:` step. Use `set -euo pipefail` inside non-trivial shell blocks.

- [x] Add unit tests for the generator.
  - [x] Add `scripts/tests/test_generate_jsonld.py` following the pattern in `_bmad/scripts/tests/`.
  - [x] Add fixture `scripts/tests/fixtures/valid-concepts.md` with a complete, valid front-matter block.
  - [x] Add fixture `scripts/tests/fixtures/missing-title.md` with the `title` field removed.
  - [x] Test: valid document produces a `.jsonld` with all required fields at correct types and values.
  - [x] Test: `bsc:source_hash` matches `"sha256:" + sha256(file_bytes).hexdigest()`.
  - [x] Test: `bsc:source_path` is the relative path from the repo root (not an absolute path).
  - [x] Test: document with missing required field raises an error and produces no sidecar.
  - [x] Run with `python3 -m unittest discover scripts/tests`.
  - [x] Re-run `python3 -m unittest discover _bmad/scripts/tests` as a regression guard — this story does not touch the validator, but confirm the 11 existing tests still pass.

### Review Findings

- [x] [Review][Decision→Patch] `pip install pyyaml` step missing from workflow — resolved: added explicit `pip install pyyaml --quiet` step before detect step. [`build-index.yml`]
- [x] [Review][Patch] `bsc:validated_on` date value not RFC3339-converted — fixed: `_to_rfc3339()` now applied to `validated-on` when non-null. [`scripts/generate_jsonld.py:113`]
- [x] [Review][Patch] `git add docs/**/*.jsonld` missing `shopt -s globstar` — fixed: `shopt -s globstar` added before `git add`. [`.github/workflows/build-index.yml`]
- [x] [Review][Patch] Push race: no `git pull --rebase` before `git push` — fixed: `git pull --rebase origin main` added before push. [`.github/workflows/build-index.yml`]
- [x] [Review][Patch] `lstrip("./")` strips character set, dead absolute-path guard — fixed: replaced with `posix.removeprefix("./")`. [`scripts/generate_jsonld.py`]
- [x] [Review][Patch] Tests create temp files in `dir=FIXTURES` — fixed: removed `dir=FIXTURES` from both NamedTemporaryFile calls. [`scripts/tests/test_generate_jsonld.py`]
- [x] [Review][Patch] Dead code: `field != "validated-on"` guard unreachable — fixed: condition removed. [`scripts/generate_jsonld.py`]
- [x] [Review][Defer] Multi-commit push fallback scans all docs including `index.md` without front-matter, causing CI exit 1 [`build-index.yml` detect+generate steps] — deferred, pre-existing (`index.md` known bad state per story notes; resolves when `index.md` gets valid front-matter)
- [x] [Review][Defer] `/tmp/changed-docs.txt` not run-scoped; concurrent jobs on self-hosted runners can race [`build-index.yml:55`] — deferred, pre-existing (hosted runners get fresh containers; self-hosted runner concern only)
- [x] [Review][Defer] `actions/checkout@v4` floating tag, not SHA-pinned [`build-index.yml:32`] — deferred, pre-existing (Phase 1 acceptable; security hardening deferred)
- [x] [Review][Defer] Non-atomic sidecar write — SIGKILL mid-write leaves partial `.jsonld` [`scripts/generate_jsonld.py:162`] — deferred, pre-existing (Phase 1 acceptable; atomic write via temp file + os.replace() deferred)
- [x] [Review][Defer] `contentStatus` is not a schema.org vocabulary term; correct term is `schema:creativeWorkStatus` — deferred, pre-existing (pre-existing spec design decision in AD-7 sidecar contract; change would require Story 2.4 + Epic 3 consumer updates)

## Dev Notes

### Story Intent

Story 2.1 opens Epic 2 by establishing the post-merge publication pipeline's first step. Epic 1 built the governance gate (schema validation before merge). This story builds what happens after merge: each context document gets a machine-readable JSON-LD sidecar committed alongside it.

Downstream stories are blocked on this foundation:
- **Story 2.2**: conflict detection logic reads document metadata from source files — having sidecars pre-generated also seeds future conflict metadata.
- **Story 2.4**: index builder aggregates per-document sidecars into `index/index.json` for retrieval.
- **Epic 3**: the Go retrieval API serves metadata from the index derived from sidecars.

The sidecar format established here is the producer-consumer contract per AD-7. Build it correctly now — changing it later breaks Story 2.4 and the Go API.

### Business Value

- FR-2 depends on this story: "The Ingestion Pipeline MUST generate a machine-readable sidecar file for each Context Document on merge."
- Without sidecars, no downstream indexing or retrieval can function (Stories 2.4 and 3.1 are blocked).
- Sidecars make document metadata queryable without parsing markdown — essential for the Go API in Epic 3.

### In Scope

- `scripts/generate_jsonld.py` — the sidecar generation script.
- `.github/workflows/build-index.yml` — post-merge ingestion workflow (sidecar step only).
- `scripts/tests/test_generate_jsonld.py` and fixtures.
- Sidecar format: JSON-LD using schema.org + Dublin Core + `bsc:` project namespace.
- Auto-commit of generated sidecars back to `main` via the workflow.

### Out Of Scope

- Conflict detection (Story 2.2).
- Domain-owner conflict override (Story 2.3).
- `index/index.json` and `index/build-manifest.json` production (Story 2.4).
- Go retrieval API (Epic 3).
- Validation against an external JSON-LD registry or schema.org validator — in-process Python validation is sufficient for Phase 1.
- Concept/keyword graph extraction — deferred to Story 2.4.
- Any changes to `_bmad/schemas/context_document_metadata.schema.json` or `_bmad/scripts/validate_context_metadata.py`.
- Changes to `pr-validate.yml`, `CODEOWNERS`, or `CONTRIBUTING.md` (unless absolutely necessary).

### JSON-LD Sidecar Format

The sidecar format uses schema.org as the base vocabulary, Dublin Core for document metadata, and a project-scoped `bsc:` namespace for provenance and pilot-specific fields.

**Canonical example** (for `docs/user-authentication/concepts.md`):
```json
{
  "@context": {
    "@vocab": "https://schema.org/",
    "dc": "http://purl.org/dc/terms/",
    "bsc": "https://github.com/slf-aobrien/bmadSharedContext/vocab#"
  },
  "@type": "DigitalDocument",
  "@id": "bsc:docs/user-authentication/concepts",
  "dc:title": "User Authentication Concepts",
  "dc:description": "Overview of core concepts and terminology used within the user authentication domain.",
  "dc:subject": ["authentication", "concepts"],
  "dc:created": "2026-07-09T00:00:00Z",
  "dc:modified": "2026-07-09T00:00:00Z",
  "dc:contributor": "slf-aobrien",
  "contentStatus": "draft",
  "bsc:domain": "user-authentication",
  "bsc:validated_on": null,
  "bsc:source_path": "docs/user-authentication/concepts.md",
  "bsc:source_hash": "sha256:<hex-digest-of-full-file-bytes>",
  "bsc:schema_version": "1.0"
}
```

**Field mapping from front-matter → JSON-LD:**

| Front-matter field | JSON-LD key | Type | Notes |
|---|---|---|---|
| `title` | `dc:title` | string | Required |
| `domain` | `bsc:domain` | string | Required; also used to derive `@id` |
| `description` | `dc:description` | string | Required |
| `keywords` | `dc:subject` | array of strings | Required |
| `created` | `dc:created` | string (RFC3339) | Required |
| `updated` | `dc:modified` | string (RFC3339) | Required |
| `validated-by` | `dc:contributor` | string | Required |
| `validated-on` | `bsc:validated_on` | string or null | Nullable; front-matter `null` → JSON `null` |
| `status` | `contentStatus` | string | Required (`draft`/`active`/`deprecated`) |

**Provenance fields (added by generator, not from front-matter):**
- `bsc:source_path`: normalized relative path from repo root (e.g., `"docs/user-authentication/concepts.md"`)
- `bsc:source_hash`: `"sha256:<hex>"` — SHA-256 of the full source file bytes (not just front-matter)
- `bsc:schema_version`: `"1.0"` — hardcoded for Phase 1; this is the contract version per AD-7
- `@id`: derived as `"bsc:<source_path_without_extension>"` (e.g., `"bsc:docs/user-authentication/concepts"`)

**`bsc:` namespace note:** The URI `https://github.com/slf-aobrien/bmadSharedContext/vocab#` is a pilot placeholder. It does not resolve to a live schema. This is acceptable per the addendum's "loose rather than rigid" standards posture. Document this explicitly in the script's module docstring so future maintainers know it is intentional.

**DO NOT add `build_manifest_id` to the sidecar** — that field belongs to Story 2.4's `build-manifest.json`. Adding it now creates a partially implemented invariant with no producer.

### Sidecar File Location

Per FR-2 ("a corresponding `.jsonld` file in the same directory"):
- `docs/user-authentication/concepts.md` → `docs/user-authentication/concepts.jsonld`
- `docs/user-authentication/index.md` → `docs/user-authentication/index.jsonld`

The `.jsonld` extension replaces `.md` in the same directory. Sidecars are derived read-only artifacts (AD-4). Consider adding a one-line header comment (not valid JSON; use a note in CONTRIBUTING.md instead) or a `README` in `docs/` noting that `.jsonld` files are auto-generated and must not be manually edited.

### Script Design: `scripts/generate_jsonld.py`

**New directory structure this story creates:**
```
scripts/
  generate_jsonld.py                  # Pipeline script invoked by build-index.yml
  tests/
    __init__.py                       # Empty — makes scripts/tests a package
    test_generate_jsonld.py           # Unit tests
    fixtures/
      valid-concepts.md               # Fixture: complete, valid front-matter
      missing-title.md                # Fixture: title field removed
```

**Script skeleton (implement this structure):**
```python
#!/usr/bin/env python3
"""
Generate JSON-LD sidecars for context documents.

Usage: python3 scripts/generate_jsonld.py <file1.md> [<file2.md> ...]

For each .md file, writes a .jsonld sidecar alongside it using schema.org /
Dublin Core / bsc: namespace per the bmadSharedContext sidecar contract.

bsc: namespace URI (https://github.com/slf-aobrien/bmadSharedContext/vocab#) is
a pilot placeholder that does not resolve. This is intentional per the Phase 1
addendum's loose standards posture.

Exits 0 if all files succeed; exits 1 if any file fails (errors collected and
reported before exit so the full batch is attempted).
"""
import hashlib
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

BSC_NAMESPACE = "https://github.com/slf-aobrien/bmadSharedContext/vocab#"
SCHEMA_VERSION = "1.0"
REQUIRED_FIELDS = [
    "title", "domain", "description", "keywords",
    "created", "updated", "validated-by", "status",
]

def parse_front_matter(path: Path) -> dict:
    """Parse YAML front-matter from a markdown file. Raises ValueError on failure."""
    ...

def build_jsonld(front_matter: dict, source_path: str, source_hash: str) -> dict:
    """Build a JSON-LD document from parsed front-matter and provenance fields."""
    ...

def generate_sidecar(md_path: Path) -> Path:
    """Generate a .jsonld sidecar for a single .md file. Returns the sidecar path."""
    ...

def main() -> int:
    """Entry point. Returns exit code."""
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/generate_jsonld.py <file1.md> [...]", file=sys.stderr)
        return 1
    errors = []
    for arg in sys.argv[1:]:
        try:
            out = generate_sidecar(Path(arg))
            print(f"Generated: {out}")
        except Exception as exc:
            print(f"ERROR [{arg}]: {exc}", file=sys.stderr)
            errors.append(arg)
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
```

**Critical implementation notes:**
- **ALWAYS use `yaml.safe_load()`** — never `yaml.load()` without a Loader. `yaml.load()` can execute arbitrary Python via the YAML `!!python/object` tag. This is an OWASP deserialization injection risk. The existing validator (`_bmad/scripts/validate_context_metadata.py`) uses `safe_load()` — follow its example.
- **Hash the full file bytes before parsing:** `hashlib.sha256(path.read_bytes()).hexdigest()`. Do not hash only the front-matter block — the hash covers the canonical source including the body.
- **Normalize `source_path`:** Use `Path(md_path).as_posix()` after stripping any leading `./`. The path must be relative from the repo root (matching the CWD of the CI workflow).
- **Write sidecars with `json.dumps(doc, indent=2, ensure_ascii=False)` + newline** — human-readable, UTF-8 safe.
- **Do not silently skip files** — one bad file should not silently produce no sidecar. Every failure must be named.

### Workflow Design: `.github/workflows/build-index.yml`

```yaml
# Post-Merge Index Build Workflow
#
# Triggered after each merge to main. Currently produces only JSON-LD sidecars.
# Stories 2.2–2.4 extend this workflow with conflict detection and index.json population.
#
# Concurrency: one run at a time. cancel-in-progress: false because cancelling a partial
# run could commit sidecars for some docs but not others, corrupting the next diff.
#
# [skip ci] in the auto-commit message prevents the commit from re-triggering this workflow.

name: Build Index

on:
  push:
    branches:
      - main

concurrency:
  group: build-index-${{ github.ref }}
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate-sidecars:
    name: Generate JSON-LD sidecars
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          # fetch-depth: 2 — only current + previous commit needed for push-event diff.
          # (pr-validate.yml uses fetch-depth: 0 for PR base SHA; not needed here.)
          fetch-depth: 2
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Detect changed context documents
        id: detect
        shell: bash
        run: |
          PREV_SHA="${{ github.event.before }}"
          CURR_SHA="${{ github.sha }}"

          if [ -n "$PREV_SHA" ] && git cat-file -e "$PREV_SHA" 2>/dev/null; then
            CHANGED=$(git diff --name-only --diff-filter=ACMR "$PREV_SHA" "$CURR_SHA" -- 'docs/' \
              | grep '\.md$' || true)
          else
            # First push or unreachable base: process all docs so nothing is missed.
            CHANGED=$(find docs -type f -name '*.md' 2>/dev/null || true)
          fi

          if [ -z "$CHANGED" ]; then
            echo "changed=false" >> "$GITHUB_OUTPUT"
            echo "No context documents changed — sidecar generation skipped."
          else
            echo "changed=true" >> "$GITHUB_OUTPUT"
            printf '%s\n' "$CHANGED" > /tmp/changed-docs.txt
            echo "Context documents to process:"
            printf '  %s\n' "$CHANGED"
          fi

      - name: Generate JSON-LD sidecars
        if: steps.detect.outputs.changed == 'true'
        shell: bash
        run: |
          set -euo pipefail
          mapfile -t FILES < /tmp/changed-docs.txt
          echo "--- Generating sidecars for ${#FILES[@]} document(s) ---"
          python3 scripts/generate_jsonld.py "${FILES[@]}"
          echo "--- Sidecar generation complete ---"

      - name: Commit and push generated sidecars
        if: steps.detect.outputs.changed == 'true'
        shell: bash
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add docs/**/*.jsonld
          if git diff --cached --quiet; then
            echo "No sidecar changes to commit — all up to date."
          else
            git commit -m "ci: regenerate JSON-LD sidecars [skip ci]"
            git push
          fi
```

**Workflow design rationale:**
- `fetch-depth: 2`: push events only need current and previous commit for accurate diff. Using `fetch-depth: 0` (full history like pr-validate.yml) is unnecessarily expensive here.
- `cancel-in-progress: false`: a cancelled mid-run could commit sidecars for some files but not others, causing the next diff to miss regenerating the skipped files.
- `[skip ci]`: prevents the auto-commit from re-triggering `build-index.yml` in a loop.
- `GITHUB_TOKEN` with `contents: write`: standard GitHub auto-commit pattern. The token expires at workflow end; it only has repository-scoped write access.
- `git add docs/**/*.jsonld`: stages only sidecars, not any other changed files.

### Architecture Compliance

- **AD-1** (write/read separation): `build-index.yml` is exclusively the write path — it produces derived artifacts. The future read path (Go API, Epic 3) is unaffected.
- **AD-4** (document canonicality): Markdown files remain the editable source of truth. `.jsonld` sidecars are derived and must never be directly edited.
- **AD-5** (deterministic regeneration with provenance): Each sidecar carries `bsc:source_path` and `bsc:source_hash`. Running the generator twice on unchanged input produces bit-for-bit identical output. CI can detect and recommit if a sidecar is stale.
- **AD-7** (artifact schema as producer-consumer contract): `bsc:schema_version: "1.0"` establishes the version. Story 2.4 (index builder) and Epic 3 (Go API) must consume sidecars at this version. Do not change the sidecar format mid-epic without versioning it.
- **AD-9** (atomic artifact publication): Not fully applicable to Story 2.1 in isolation. The `build_manifest_id` that binds related artifacts into a single snapshot is Story 2.4's concern. This story produces only per-document sidecars; the manifest is added later.

### Technical Requirements

- Python 3 for the generator script (consistent with existing validator).
- `pyyaml` for YAML parsing — already present in the dev environment (used by `validate_context_metadata.py`). No new pip dependencies needed.
- Standard library only beyond `pyyaml`: `json`, `hashlib`, `sys`, `pathlib`.
- Do not use `uv` or `rg` (repo command policy from `AGENTS.md` and `docs/project-context.md`).
- Explicit `shell: bash` on all multi-line `run:` steps in the workflow.
- `set -euo pipefail` at the top of non-trivial shell blocks.
- `timeout-minutes: 10` on the workflow job.
- `concurrency:` block present with `cancel-in-progress: false`.

### Files To Create

| File | Action | Notes |
|------|--------|-------|
| `scripts/generate_jsonld.py` | **CREATE** | Sidecar generator; core pipeline deliverable. |
| `scripts/tests/__init__.py` | **CREATE** | Empty init to make the directory a Python package. |
| `scripts/tests/test_generate_jsonld.py` | **CREATE** | Unit tests for the generator. |
| `scripts/tests/fixtures/valid-concepts.md` | **CREATE** | Test fixture with complete valid front-matter. |
| `scripts/tests/fixtures/missing-title.md` | **CREATE** | Test fixture missing the `title` field. |
| `.github/workflows/build-index.yml` | **CREATE** | Post-merge ingestion workflow. |

No changes to `_bmad/` scripts, schemas, or tests. No changes to `pr-validate.yml`. No changes to existing docs (the workflow auto-generates sidecars beside existing files on next push to main).

### Current Repository State (baseline `74de78c`)

- `docs/user-authentication/` contains two files: `concepts.md` (has valid front-matter) and `index.md` (currently contains only `#Test commit` — **no front-matter**).
- **The generator must handle `index.md` gracefully.** When a document has no parseable front-matter, the generator should log the error with the file name and reason, skip that file, and continue. It should still exit non-zero at the end if any file failed (per AC 3). Do not let the absence of front-matter cause an unhandled Python traceback.
- `.github/workflows/pr-validate.yml` exists; `build-index.yml` does not exist yet.
- `.github/CODEOWNERS` maps `@slf-aobrien` as domain owner.
- `_bmad/scripts/validate_context_metadata.py` passes 11 tests — do not regress it.
- No `scripts/` directory exists — this story creates it.
- Current branches: `main` (HEAD `74de78c`) and `feature/user-authentication`.

### Previous Story Intelligence

#### From Epic 1 Retrospective (2026-07-09)

All four items below were documented as patterns that required code-review patches in Epic 1. Do not repeat them:

1. **`shell: bash` on all multi-line run steps** — `mapfile` and other bash builtins silently fail on `sh`. Add `shell: bash` explicitly every time.
2. **`timeout-minutes` on every job** — omitting it caused open-ended workflow risk in `pr-validate.yml`. `build-index.yml` MUST have it.
3. **`concurrency:` key** — absent from `pr-validate.yml`; multiple simultaneous pushes can race. Add it from day one here.
4. **`set -euo pipefail`** — silenced errors (`2>/dev/null`) and missing `set -e` were flagged as CI quality gaps. Apply it in every non-trivial shell block.

#### From Story 1.3 (`pr-validate.yml` patterns to replicate)

- `--diff-filter=ACMR` to include renamed files in the changed-doc list.
- `find docs -type f -name '*.md'` fallback when no reachable base commit.
- `mapfile -t FILES < /tmp/file.txt` pattern for file list ingestion.
- `$GITHUB_OUTPUT` for step output, not deprecated `set-output`.

#### From Story 1.4 (auto-commit pattern)

Git identity for CI commits:
```
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
```
Always check `git diff --cached --quiet` before committing — do not create empty commits.

#### From Deferred Work Log

- `pr-validate.yml` is missing `concurrency:` — flagged but deferred. Fix this pattern now in `build-index.yml`.
- `fetch-depth: 0` is expensive at scale — use `fetch-depth: 2` for push events where only prev/curr commit is needed.
- `docs/user-authentication/index.md` currently has only `#Test commit` and no front-matter. This is a pre-existing state; do not add a PR to fix it in this story. The generator must handle it gracefully (per the current repository state note above).

### Testing Requirements

**Unit tests (`python3 -m unittest discover scripts/tests`):**
- Valid document → `.jsonld` sidecar with all required fields at correct types.
- `bsc:source_hash` equals `"sha256:" + sha256(file_bytes).hexdigest()`.
- `bsc:source_path` is a relative path (not absolute), matching the input file path.
- `@id` is `"bsc:" + source_path_without_extension`.
- Document missing required front-matter field (`title`) → `ValueError` or equivalent raised, no `.jsonld` file written.
- Document with `validated-on: null` → `bsc:validated_on` is JSON `null` (not string `"null"` or omitted).

**Regression guard:**
- `python3 -m unittest discover _bmad/scripts/tests` — confirm all 11 existing tests still pass.

**Manual integration verification:**
1. Run `python3 scripts/generate_jsonld.py docs/user-authentication/concepts.md` locally and confirm a valid `.jsonld` is written at `docs/user-authentication/concepts.jsonld`.
2. Inspect the sidecar: valid JSON, all required fields present.
3. Run the same command against `docs/user-authentication/index.md` (which has no front-matter) — confirm an error is printed and no `.jsonld` file is created for it, and the command exits 1.
4. Push a content change to a doc on `main` and confirm `build-index.yml` runs, generates the sidecar, and commits it back with the `[skip ci]` message.
5. Confirm the auto-commit does NOT re-trigger the workflow.
6. Push a change to a non-doc file (e.g., a planning artifact) — confirm the workflow detects no changed `.md` files and prints the skip message.

### UX and Diagnostics Requirements

Per the Experience Spine (EXPERIENCE.md) and UX-DR12 (no-silent-failure):
- Any document that fails generation must be named in the error output with the specific cause (e.g., `"ERROR [docs/user-authentication/index.md]: missing required front-matter field: title"`).
- Successful generation must print a confirmation: `"Generated: docs/user-authentication/concepts.jsonld"`.
- If no documents changed, the workflow must print an explicit skip message, not remain silent.
- If all documents succeed, the CI log must show the list of generated sidecars and a `"Sidecar generation complete"` summary.

### Pitfalls To Avoid

- **DO NOT use `yaml.load()` without a Loader** — always `yaml.safe_load()`. This is an OWASP deserialization injection risk.
- **DO NOT place the generator under `_bmad/`** — that directory is bmad infrastructure. The production pipeline script belongs at `scripts/generate_jsonld.py`.
- **DO NOT co-locate `.jsonld` sidecars under `index/`** — the FR-2 requirement is explicit: the sidecar lives in the same directory as the source `.md`. The `index/` directory is for the aggregated `index.json` (Story 2.4), not per-document sidecars.
- **DO NOT add `build_manifest_id` to the sidecar format** — that is Story 2.4's invariant. Adding it now without a producer makes the field meaningless and misleading.
- **DO NOT set `cancel-in-progress: true`** in the concurrency block — a cancelled mid-run could leave sidecars committed for some docs but not others, corrupting the next diff.
- **DO NOT silently pass over files with parse errors** — log each failure, continue to the next file, and exit 1 at the end.
- **DO NOT create `.jsonld` files manually** — they must be auto-generated; manual edits violate AD-4.
- **DO NOT use `fetch-depth: 0`** in `build-index.yml` — `fetch-depth: 2` is sufficient for push-event diffs.
- **DO NOT omit `set -euo pipefail`** in shell steps — errors must surface explicitly.
- **DO NOT use `uv` or `rg`** — repo command policy (per `AGENTS.md` and `docs/project-context.md`). Use `python3` and `grep`/`find` respectively.

## Dev Agent Record

### Implementation Plan

1. **`scripts/generate_jsonld.py`** — Production sidecar generator using `yaml.safe_load()` (OWASP-safe), `hashlib.sha256` over full file bytes, `json.dumps` with `indent=2`. Datetime objects from PyYAML are normalised to RFC 3339 (`T`/`Z` format) via `_to_rfc3339()`. Pre-write validation confirms `@context`, `@type`, and all required non-null fields. Batch mode: try/except per file, errors collected and reported, exit 1 if any failed.
2. **`.github/workflows/build-index.yml`** — Post-merge workflow with `concurrency` (`cancel-in-progress: false`), `permissions: contents: write`, `timeout-minutes: 10`, `fetch-depth: 2`, `shell: bash` on all multi-line steps, `set -euo pipefail` in non-trivial blocks, `[skip ci]` on auto-commit.
3. **`scripts/tests/`** — 20 unit tests covering: sidecar structure, source_hash SHA-256 correctness, source_path relative (not absolute), `validated-on: null` → JSON `null`, missing required field raises + no sidecar written, main() exit codes (0/1), mixed-batch continues and exits 1.

### Completion Notes

- ✅ AC1: workflow triggers on push to main, detects changed docs in `docs/`, generates `.jsonld` alongside `.md`.
- ✅ AC2: sidecar is well-formed JSON, contains `@context` and `@type: DigitalDocument`, all required fields present and non-null (`bsc:validated_on` nullable), produced by generator with exit 0.
- ✅ AC3: document with missing/malformed front-matter exits non-zero, names the file and cause in stderr, no partial sidecar written.
- ✅ 20 new tests pass (`python3 -m unittest discover scripts/tests`).
- ✅ 11 regression tests pass (`python3 -m unittest discover _bmad/scripts/tests`).
- ✅ Manual integration: `docs/user-authentication/concepts.jsonld` generated correctly; `docs/user-authentication/index.md` (no front-matter) produces error + exit 1, no sidecar.
- ✅ All Epic 1 retrospective patterns applied: `shell: bash`, `timeout-minutes`, `concurrency`, `set -euo pipefail`.
- ✅ `yaml.safe_load()` used throughout — OWASP deserialization injection risk avoided.

## File List

- `scripts/generate_jsonld.py` — CREATED: sidecar generator script.
- `scripts/tests/__init__.py` — CREATED: package init (empty).
- `scripts/tests/test_generate_jsonld.py` — CREATED: 20 unit tests.
- `scripts/tests/fixtures/valid-concepts.md` — CREATED: test fixture with complete valid front-matter.
- `scripts/tests/fixtures/missing-title.md` — CREATED: test fixture missing `title` field.
- `.github/workflows/build-index.yml` — CREATED: post-merge ingestion workflow.
- `docs/user-authentication/concepts.jsonld` — CREATED: generated sidecar (auto-generated artifact; manually created here for integration verification; will be regenerated by CI on merge).

## Change Log

- 2026-07-09: Implemented Story 2.1 — created sidecar generator (`scripts/generate_jsonld.py`), post-merge workflow (`.github/workflows/build-index.yml`), unit tests and fixtures (`scripts/tests/`). 20 new tests pass. 11 regression tests pass.
