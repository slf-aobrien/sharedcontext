---
name: Shared Context Pilot
status: final
sources:
  - "{planning_artifacts}/prds/prd-bmadSharedContext-2026-07-07/prd.md"
  - "{planning_artifacts}/prds/prd-bmadSharedContext-2026-07-07/addendum.md"
updated: 2026-07-07
---

# Shared Context Pilot - Experience Spine

## Foundation

Multi-surface technical workflow spanning GitHub repository browsing and contribution, pull-request quality gates, CLI-based agent creation, and local Retrieval API verification. No dedicated product UI is in MVP scope; `DESIGN.md` is the visual identity reference for project-owned artifacts such as templates, reports, and lightweight demo pages, while GitHub and terminal conventions remain inherited.

[ASSUMPTION] Primary usage is desktop-first responsive web plus terminal because Phase 1 contributors are developers, domain owners, and analysts working in GitHub and local environments. Mobile is read-only fallback, not a task-completion target.

## Information Architecture

| Surface | Reached from | Purpose |
|---|---|---|
| Domain folder | Repository root / direct link | Browse context documents within a single domain and understand the knowledge perimeter |
| Context document | Domain folder row / search / PR file link | Read one unit of knowledge, including metadata, freshness, keywords, and status |
| Contribution template | `CONTRIBUTING.md` / templates path | Author a valid context document without outside help |
| Pull request checks | PR open / failed check link | Resolve schema failures, conflicts, and validation issues before merge |
| Conflict report | PR checks / override decision | Compare contradictory claims and decide whether to revise or justify an override |
| Agent creation CLI | Local terminal command | Generate a usable agent config in under five minutes |
| Generated agent config | CLI completion output | Inspect, copy, and use the produced configuration for the chosen task type |
| Retrieval smoke check | CLI follow-up / API call | Verify that a keyword query returns the expected document payload or an explicit empty result |
| Validation freshness review | Context document metadata / periodic review cadence | Confirm whether a document is still trustworthy and update validation metadata |

IA closure rule for this pilot: every stated need in the PRD lands on one of the surfaces above, and every surface maps to at least one named journey below. There is no separate MVP search UI or admin dashboard in Phase 1.

## Voice and Tone

Microcopy must be precise, low-drama, and operational. Brand posture lives in `DESIGN.md`.

| Do | Don't |
|---|---|
| `No context found for this keyword. You can continue without shared context.` | `Nothing matched. Want AI to guess?` |
| `Missing required field: validated-on.` | `Validation failed.` |
| `Conflict detected between session-management.md and token-lifetime.md.` | `Potential issue found.` |
| `Override recorded with justification.` | `Bypassed successfully!` |
| `Agent config generated. Run the smoke check next.` | `You're all set to supercharge your workflow.` |

## Component Patterns

Behavioral rules. Visual specs live in `DESIGN.md.Components`.

| Component | Use | Behavioral rules |
|---|---|---|
| Context document metadata block | Top of every document | Always shows domain, status, keywords, validated-by, and validated-on together. Deprecated status never hides the document; it flags it. |
| Keyword chip | Documents, API result summaries | Chips are informative only. Clicking a chip filters or launches a related query when the host surface supports it; otherwise they remain plain text. |
| Conflict callout | PR check output, retrieval result with unresolved conflict | Always names both sources and the conflicting claim summary. Provide the revision path before the override path. |
| Schema error list | PR validation failure | Group by file first, then missing or malformed field. Each item must point back to the exact file/field combination. |
| Command block | Contribution guide, agent setup, smoke checks | Commands are copyable as a whole. Inline variables are visibly marked and explained immediately below. |
| Agent config summary | After CLI generation | Show selected domain, task type, output format, endpoint, and fallback behavior before handoff to file output. |
| Freshness badge | Documents and retrieval results | Reflects `validated-on` recency, not quality. Missing freshness is neutral-to-cautionary, not hidden. |

## State Patterns

| State | Surface | Treatment |
|---|---|---|
| First contribution attempt | Contribution template | Inline instructions remain visible until replaced; required metadata fields are never hidden behind collapsed help. |
| Schema failure | Pull request checks | Blocking state. Report names offending fields and files and provides a direct path back to the document. |
| Conflict detected | Pull request checks / conflict report | Blocking state until resolved or explicitly overridden with documented justification. Primary action is `Revise document`; secondary action is `Override with justification`. |
| False-positive override | Conflict report | Override path requires a concise rationale that is logged and visible in the audit trail. |
| No retrieval results | Retrieval smoke check / agent runtime | Return HTTP 200 with empty results and explicit copy telling the user the system found no shared context. No synthetic fallback content is invented. |
| Unresolved conflict on retrieval | Retrieval result | Result remains visible but carries a conflict flag and summary so agents and humans can surface uncertainty instead of treating the content as clean. |
| Stale validation | Context document / review cadence | Surface the age of the validation date and route the reviewer toward re-validation, not silent trust. |
| Local stack unavailable | Agent creation smoke check | Explain whether the API, graph store, or network target is unavailable and keep generated config intact for retry. |

## Interaction Primitives

- Markdown-first reading and editing. The authored truth lives in plain markdown with YAML frontmatter.
- Keyboard-first completion for contributor tasks. Every critical path must remain fully operable through GitHub text editing, PR review, and terminal commands.
- Direct file-path linking from validation and conflict outputs back to the implicated artifact.
- Progressive disclosure only for secondary explanation. Blocking reasons, compared sources, and next actions stay visible without expansion.
- Explicit fallback behavior when shared context is empty or unavailable.

Banned in MVP: hidden required fields, hover-only error explanation, auto-dismissed conflict messaging, silent overrides, and any agent behavior that fabricates missing context instead of stating that none was found.

## Accessibility Floor

Behavioral rules. Visual contrast lives in `DESIGN.md`.

- WCAG 2.2 AA for any project-owned HTML artifact generated in the pilot.
- Every blocking validation or conflict message must remain understandable in plain markdown and plain text, not color alone.
- File references, commands, and compared claims must be selectable and copyable from reports.
- Keyboard-only users can complete the contribution, review, and smoke-check paths without requiring drag, hover, or pointer-specific affordances.
- Tables used in HTML artifacts must preserve header associations; markdown tables should be duplicated as lists when a narrow viewport would make them unreadable.
- Terminal instructions avoid ASCII art or dense formatting that obscures step order in screen readers.

## Responsive & Platform

| Surface type | Behavior |
|---|---|
| Desktop web (primary) | Full document tables, side-by-side comparison in conflict reports, copy-ready command blocks |
| Narrow web / mobile fallback | Single-column stack, compared claims become ordered sections instead of columns, command blocks scroll horizontally if needed |
| Terminal | Prompt-by-prompt flow, one required decision per line, generated file path echoed on success |

[ASSUMPTION] Because the pilot is local-first and GitHub-centric, responsive work focuses on readability of generated artifacts rather than designing a touch-native authoring flow.

## Inspiration & Anti-patterns

- Lifted from docs-as-code discipline: plain markdown as the source of truth, frontmatter as the metadata envelope, PRs as the review surface.
- Lifted from modern CI feedback: failed checks should identify the exact file and field, not merely say that a pipeline broke.
- Lifted from trustworthy CLI tools: prompts are few, explicit, and followed by a clear artifact summary.
- Rejected: a decorative dashboard homepage for Phase 1. The product proves value through retrieval accuracy and contribution clarity, not a management shell.
- Rejected: conversational microcopy in blocking flows. These are operational corrections, not brand theater.
- Rejected: a separate search UI in MVP. The pilot must prove the repository plus API loop before adding another surface.

## Key Flows

### Flow 1 - Amelia creates an agent with shared context in under five minutes

1. Amelia opens a terminal in the repository workspace and runs the agent-creation command.
2. The CLI asks for agent name, domain, task type, and output format in a short linear sequence.
3. After the last answer, the system shows an agent config summary: chosen domain, endpoint, output format, and explicit fallback behavior for empty results.
4. Amelia accepts the generated config path and runs the smoke check against the Retrieval API.
5. The API returns at least one User Authentication result with document title, status, validation date, and excerpt.
6. **Climax:** Amelia sees a real shared-context result land in the same working session where she created the agent, proving the agent is wired to organizational knowledge instead of a blank prompt.

Failure path: if the API returns no results, the smoke check says so plainly and preserves the config so Amelia can continue with a no-context fallback instead of treating setup as broken.

### Flow 2 - Aaron resolves a conflicting PR before merge

1. Aaron opens a PR adding or changing a User Authentication document.
2. Schema validation passes, then the conflict check flags a contradiction with an existing document.
3. Aaron opens the conflict report and sees both file names, the compared claims, and the recommended next action to revise the source.
4. He determines whether the contradiction is real or a false positive.
5. If real, he edits the source document and reruns the checks. If false positive, he adds the documented override justification.
6. **Climax:** The PR moves from ambiguous disagreement to a clean, explicit decision path before merge, so the graph database never absorbs contradictory knowledge silently.

Failure path: if Aaron tries to override without justification, the system blocks completion and asks for the rationale in the same flow.

### Flow 3 - Sarah re-validates a document during monthly review

1. Sarah opens the repository view for the User Authentication domain and scans validation metadata.
2. She selects a document whose `validated-on` date is stale or missing.
3. The document surface keeps the metadata adjacent to the body so she can review the rule and its freshness together.
4. Sarah confirms the rule is still correct and updates the validation metadata through the standard contribution path.
5. The PR shows only the metadata change plus any automated checks that still apply.
6. **Climax:** The document returns to an explicitly trusted state, and future retrieval responses can surface that freshness signal to both agents and humans.

Failure path: if Sarah finds the rule outdated, the same flow becomes a content revision instead of a metadata-only refresh; freshness never masks stale substance.
