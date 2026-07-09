---
name: Shared Context Pilot
description: GitHub-native shared context system for domain knowledge and AI agent skills, optimized for repository documents, automation reports, and local-first technical handoffs.
status: final
sources:
  - "{planning_artifacts}/prds/prd-bmadSharedContext-2026-07-07/prd.md"
  - "{planning_artifacts}/prds/prd-bmadSharedContext-2026-07-07/addendum.md"
updated: 2026-07-07
colors:
  surface-base: '#F5F1E8'
  surface-raised: '#FFFDFC'
  surface-muted: '#E7DFD2'
  ink-primary: '#1F2933'
  ink-secondary: '#52606D'
  ink-muted: '#7B8794'
  primary: '#0B5D66'
  on-primary: '#FFFFFF'
  secondary: '#355C7D'
  on-secondary: '#FFFFFF'
  accent: '#C48A3A'
  on-accent: '#1F1710'
  success: '#2E6F40'
  on-success: '#FFFFFF'
  warning: '#A96816'
  on-warning: '#FFF8EF'
  error: '#B2442E'
  on-error: '#FFFFFF'
  border-hairline: '#D7CCBC'
  code-surface: '#EDE7DD'
  focus-ring: '#0B5D66'
typography:
  display:
    fontFamily: Newsreader
    fontSize: 38px
    fontWeight: '500'
    lineHeight: '1.15'
    letterSpacing: -0.02em
  heading:
    fontFamily: IBM Plex Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.25'
  body:
    fontFamily: IBM Plex Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label:
    fontFamily: IBM Plex Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: 0.08em
  mono:
    fontFamily: IBM Plex Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
rounded:
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  full: 9999px
spacing:
  '1': 4px
  '2': 8px
  '3': 12px
  '4': 16px
  '5': 24px
  '6': 32px
  '7': 48px
  gutter: 24px
  content-max: 960px
components:
  status-badge:
    radius: '{rounded.full}'
    font: '{typography.label.fontFamily}'
    background-active: '{colors.primary}'
    background-deprecated: '{colors.surface-muted}'
    foreground-active: '{colors.on-primary}'
    foreground-deprecated: '{colors.ink-secondary}'
  conflict-callout:
    background: '{colors.warning}'
    foreground: '{colors.on-warning}'
    border: 'none'
    radius: '{rounded.lg}'
  schema-error:
    background: '{colors.error}'
    foreground: '{colors.on-error}'
    radius: '{rounded.md}'
  keyword-chip:
    background: '{colors.surface-muted}'
    foreground: '{colors.ink-primary}'
    radius: '{rounded.full}'
  command-block:
    background: '{colors.code-surface}'
    foreground: '{colors.ink-primary}'
    radius: '{rounded.md}'
  document-card:
    background: '{colors.surface-raised}'
    foreground: '{colors.ink-primary}'
    border: '1px solid {colors.border-hairline}'
    radius: '{rounded.lg}'
---

## Brand & Style

Shared Context Pilot is a technical field guide, not a product-marketing shell. The visual identity should make repository artifacts, automation reports, and local demo surfaces feel trustworthy, editorially ordered, and easy to scan under engineering pressure. It leans on warm-paper surfaces, dense but controlled typography, and a single deep-teal action color so operational decisions read clearly without looking like dashboard chrome.

[ASSUMPTION] Because Phase 1 is GitHub-native and local-first, the brand layer primarily applies to project-owned artifacts such as templates, validation reports, generated HTML references, and any lightweight documentation surfaces. GitHub's own interface and the terminal remain inherited containers rather than re-skinned surfaces.

## Colors

The palette separates authority, action, and intervention.

- Warm paper surfaces (`{colors.surface-base}`, `{colors.surface-raised}`) keep markdown-heavy reading from feeling stark or clinical.
- Deep teal (`{colors.primary}`) is the action and trust color. Use it for primary actions, linked jumps inside generated artifacts, and focus indicators that mean the system is ready to proceed.
- Slate blue (`{colors.secondary}`) supports structural navigation and secondary emphasis, especially around source attribution and system topology references.
- Brass (`{colors.accent}`) is reserved for moments of importance that are not failures: freshness metadata, pilot-status markers, and notable retrieval hits.
- Warning amber (`{colors.warning}`) and error brick (`{colors.error}`) are intervention colors only. Warning means a human must reconcile a conflict or stale validation. Error means a blocking schema or pipeline failure.

Avoid gradients, neon status colors, or multiple competing accents. The system should read like vetted knowledge, not telemetry noise.

## Typography

Typography carries most of the hierarchy because many core surfaces are markdown, code, or terminal-adjacent.

- `display` in Newsreader is used sparingly for artifact titles, report headers, and key section openers where a human needs to orient quickly.
- `heading` and `body` in IBM Plex Sans hold the operational surface: tables, labels, guidance text, and explanatory prose.
- `mono` in IBM Plex Mono is the contract voice for file paths, commands, API shapes, and generated config snippets.
- `label` is tracked and compact, used for metadata keys, badge text, and section overlines.

Do not use the serif display role inside dense tables, conflict reports, or code-adjacent callouts. Those surfaces should prioritize parsing speed over flourish.

## Layout & Spacing

Layouts should bias toward single-column reading with deliberate sectional breaks. Most artifacts are document-first, so the default max reading width is `{spacing.content-max}` with generous vertical rhythm between sections and much tighter spacing inside metadata clusters.

- Use `{spacing.gutter}` for the default horizontal page margin on desktop artifact pages.
- Tables, callouts, and command blocks should sit in a consistent vertical cadence: `{spacing.4}` between tightly related items, `{spacing.6}` between distinct blocks, `{spacing.7}` before a new major section.
- Repository-oriented pages should privilege stable left alignment and predictable scanning over card mosaics or dashboard grids.

[ASSUMPTION] When a generated HTML artifact is viewed on mobile, content stacks to one column and tables may overflow horizontally rather than collapsing labels into ambiguous mobile cards.

## Elevation & Depth

Depth should be quiet. Most hierarchy is established through contrast, border weight, and spacing rather than shadows.

- `document-card` surfaces may use a low-contrast border and a minimal shadow only when they float above a warmer page background.
- Conflict and schema callouts should rely on color-block contrast, not extra elevation.
- Command and code blocks should feel inset through tonal difference (`{colors.code-surface}`), not by appearing physically lifted.

## Shapes

Corners are softened but not playful. The system deals with rules, conflicts, and structured knowledge; shapes should convey steadiness.

- Small utility elements use `{rounded.sm}`.
- Default cards, code blocks, and validation modules use `{rounded.md}` or `{rounded.lg}`.
- Fully rounded tokens belong only to small status badges and keyword chips.

Avoid oversized radii, pills for primary buttons, or ornamental shapes that make technical content feel casual.

## Components

- `status-badge` marks draft, active, deprecated, validated, and pilot-only states. Use compact tracked text and keep the badge visually subordinate to document titles.
- `conflict-callout` is the high-attention module for contradictory claims. It should lead with the contradiction summary and immediately expose the compared sources.
- `schema-error` is a blocking pattern. Use it for field-level failures and pipeline-stop messaging; the tone is corrective, not alarming.
- `keyword-chip` represents extracted retrieval terms and domain tags. Chips support scanability but should never become the main hierarchy on a page.
- `command-block` is the canonical surface for terminal steps, API calls, and generated config fragments.
- `document-card` is used for context-document previews, retrieval hits, and report summaries where title, domain, freshness, and excerpt need a stable shell.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Let documents, commands, and file references remain the focal point | Turn artifact pages into analytics dashboards |
| Use warning and error colors only for intervention states | Reuse warning amber as a decorative accent |
| Keep max widths readable and left-aligned | Center long-form technical prose |
| Distinguish code and command surfaces tonally, not theatrically | Add glowing borders, heavy shadows, or gradient shells |
| Make source links and compared documents explicit in conflict UI | Hide the other side of a contradiction behind a secondary click |
