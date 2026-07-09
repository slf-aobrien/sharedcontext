---
# INSTRUCTIONS: Replace every value below with real content before submitting.
# Before opening a pull request:
#   1. Delete ALL comment lines (lines starting with '#') from this front-matter block.
#   2. Replace the '# <Your Document Title Here>' heading below with your actual document title.
#   3. Remove the HTML comment blocks (<!-- ... -->) in the document body.

# REQUIRED — Human-readable title for this document.
# Example: "Password Reset Flow"
title: <your document title here>

# REQUIRED — Domain identifier. Must be "user-authentication" in Phase 1.
# Example: "user-authentication"
domain: user-authentication

# REQUIRED — One-to-two sentence summary of what this document covers.
# Example: "Describes the end-to-end password reset flow used by the authentication service."
description: <one-to-two sentence description>

# REQUIRED — Discovery tags. Use block-list YAML (one item per line with "  - ").
# At least one keyword is required. Do NOT use inline/flow style: [foo, bar].
# Example:
#   keywords:
#     - password-reset
#     - authentication
keywords:
  - <keyword-one>
  - <keyword-two>

# REQUIRED — Creation timestamp in RFC3339 UTC format: YYYY-MM-DDTHH:MM:SSZ
# Set once when you first create the file; do not change on subsequent edits.
# Example: "2026-07-08T00:00:00Z"
created: <YYYY-MM-DDTHH:MM:SSZ>

# REQUIRED — Last-updated timestamp in RFC3339 UTC format: YYYY-MM-DDTHH:MM:SSZ
# Update this every time you edit the document body or front matter.
# Example: "2026-07-08T12:00:00Z"
updated: <YYYY-MM-DDTHH:MM:SSZ>

# REQUIRED — Name or identifier of the person or team who validated this document.
# Must be a non-empty string. Use your own name/email as the initial author identifier
# before formal review; update to the reviewer's identifier after review.
# Example: "aaron@example.com" or "platform-team"
validated-by: <your-name-or-email>

# REQUIRED — Timestamp of last validation, or null if not yet validated.
# Use null until a domain owner has reviewed the document.
# Example: "2026-07-08T00:00:00Z"  or  null
validated-on: null

# REQUIRED — Document lifecycle status. Must be exactly one of: draft, active, deprecated.
#   draft      — Work in progress; not approved for agent consumption.
#   active     — Approved and ready for agent consumption.
#   deprecated — Superseded or retired; still visible but no longer authoritative.
status: draft
---

# <Your Document Title Here>

<!-- Replace this line with the main body of your context document. -->
<!-- Use standard markdown: headings, paragraphs, lists, code blocks. -->
<!-- The YAML front matter above is the only structured metadata section; -->
<!-- keep everything else as readable prose for human and agent consumers. -->

## Summary

<!-- One short paragraph summarising what this document describes. -->

## Details

<!-- Main content: concepts, flows, rules, examples, or references. -->
