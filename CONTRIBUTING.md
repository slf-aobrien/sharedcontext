# Contributing Context Documents

This guide covers the end-to-end path for contributing a new context document to the
**bmadSharedContext** repository during Phase 1 of the pilot.

Phase 1 scope is limited to the **User Authentication** domain.

---

## Overview

Context documents are plain markdown files with a YAML front-matter block that carries
structured governance metadata.  The markdown file is the **only editable source of truth**
for any context document.  Derived artifacts (JSON-LD sidecars, index graphs) will be generated
from the markdown once the publication pipeline is active (Epic 2); you never author or edit them directly.

A valid submission requires:

1. A markdown file placed in the correct location.
2. A complete and correctly formatted YAML front-matter block.
3. A local validation pass before opening a pull request.

---

## Phase 1: Where Context Documents Live

Place new User Authentication context documents in:

```
docs/user-authentication/
```

Use lowercase-hyphenated filenames, for example:

```
docs/user-authentication/password-reset-flow.md
```

---

## Step 1: Copy the Template

Create the target directory if it does not yet exist, then copy the canonical template:

```
mkdir -p docs/user-authentication/
cp templates/context-document-template.md docs/user-authentication/your-document-name.md
```

Open the new file and fill in every front-matter field.  The template contains inline
instructions above each field explaining exactly what value is expected.

---

## Step 2: Fill In the Front Matter

Every context document **must** start with a YAML front-matter block delimited by `---`.
Example of a minimal valid block:

```markdown
---
title: Password Reset Flow
domain: user-authentication
description: Describes the end-to-end password reset flow used by the authentication service.
keywords:
  - password-reset
  - authentication
  - user-management
created: 2026-07-08T00:00:00Z
updated: 2026-07-08T00:00:00Z
validated-by: <your-name-or-email>
validated-on: null
status: draft
---
```

Detailed field rules are listed in the template file and enforced by the validator.  Keep the
schema at `_bmad/schemas/context_document_metadata.schema.json` and the validator script at
`_bmad/scripts/validate_context_metadata.py` as the **authoritative source of truth**; this
guide explains the same rules in plain language but the schema file governs.

---

## Step 3: Validate Locally

Run the validator against your file before committing:

```
python3 _bmad/scripts/validate_context_metadata.py docs/user-authentication/your-document-name.md
```

To validate every document in the directory at once:

```
python3 _bmad/scripts/validate_context_metadata.py docs/user-authentication/
```

### Reading the Output

**All clear** — no blocking issues:

```
{"ok": true, "errors": [], ...}
```

**Blocking errors** — you must fix these before the document can be merged:

```json
{
  "ok": false,
  "errors": [
    {
      "file": "docs/user-authentication/password-reset-flow.md",
      "field": "keywords",
      "message": "must use block-list YAML for consistency ..."
    }
  ]
}
```

### How to Interpret and Fix Errors

Errors are grouped by `file` and then `field`.  For each error:

| Error message | What to fix |
|---|---|
| `missing required field` | Add the field to your front matter. |
| `must be non-empty string` | The field is blank; provide a real value. |
| `must be RFC3339 UTC (YYYY-MM-DDTHH:MM:SSZ)` | Reformat the timestamp, e.g. `2026-07-08T00:00:00Z`. |
| `must be null or RFC3339 UTC (YYYY-MM-DDTHH:MM:SSZ)` | For `validated-on`: use `null` if not yet validated, or reformat the timestamp, e.g. `2026-07-08T00:00:00Z`. |
| `must use block-list YAML for consistency` | Change `keywords: [foo, bar]` to the multi-line block form shown in the template. |
| `must be one of: draft, active, deprecated` | Change `status` to one of those three values exactly. |
| `missing YAML front matter` | Add `---` delimiters at the very top of the file. |
| `block scalars are not supported` | Do not use `|` or `>` for multi-line values in front matter. |
| `inline mappings are not supported` | Do not use `{}` style values in front matter. |

After fixing all errors, re-run the validator and confirm `"ok": true` before continuing.

---

## Step 4: Open a Pull Request

Once `"ok": true`, commit your file and open a pull request.  The PR description should
include the command output showing the successful local validation run.

The repository has automated schema validation wired at `.github/workflows/pr-validate.yml`.
When you open a PR targeting `main`, the workflow checks every changed markdown file under
`docs/` against the front-matter contract and blocks merge if any required field is missing
or malformed.  The check uses the same validator you ran locally, so a local pass means the
CI check will pass too.

PRs that modify files under `docs/user-authentication/` will automatically request review
from the domain owner as configured in `.github/CODEOWNERS`.  The PR cannot merge until
that review is approved.

---

## Field Reference

All required fields are described in `templates/context-document-template.md`.  For the
normative contract, see `_bmad/schemas/context_document_metadata.schema.json`.

| Field | Required | Notes |
|---|---|---|
| `title` | Yes | Human-readable document title, non-empty string. |
| `domain` | Yes | Must be `user-authentication` in Phase 1. |
| `description` | Yes | One-to-two sentence summary of document content. |
| `keywords` | Yes | Block-list YAML; at least one non-empty keyword. |
| `created` | Yes | RFC3339 UTC: `YYYY-MM-DDTHH:MM:SSZ`. |
| `updated` | Yes | RFC3339 UTC; update on every edit. |
| `validated-by` | Yes | Your name or email (non-empty); use your own identifier as author before formal review. |
| `validated-on` | Yes | RFC3339 UTC timestamp, or `null` if not yet validated. |
| `status` | Yes | One of `draft`, `active`, or `deprecated`. |

---

## Out of Scope for Phase 1

The following are **not** part of this contribution flow and should not be referenced in
documents or PRs until the relevant stories are complete:

- JSON-LD sidecar generation (Epic 2)
- Retrieval API or CLI flows (Epic 3)

---

## Repository Admin Setup

This section is for repository administrators, not contributors.

### Enable Branch Protection for `main`

The CODEOWNERS review requirement is only enforced after the following branch protection
rule is active.  A repository admin must complete this step once after the `CODEOWNERS`
file is merged.

**GitHub UI** (Settings → Branches → Add branch protection rule):

1. Branch name pattern: `main`
2. ✅ Require a pull request before merging — Require approvals: **1**
3. ✅ Require review from Code Owners
4. ✅ Require status checks to pass before merging
   - Add status check: `Validate context document front matter`
   - Add status check: `CODEOWNERS placeholder check`
5. ✅ Require branches to be up to date before merging (recommended)
6. ✅ Do not allow bypassing the above settings (enforces rules for administrators too)
7. Save changes.

**GitHub CLI alternative** (requires admin token):

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
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null
}
EOF
```

Replace `{owner}/{repo}` with the actual repository path.  The `CODEOWNERS` placeholder
`@OWNER_GITHUB_USERNAME` must also be replaced with a real GitHub username or team slug
before this step can be fully verified.
