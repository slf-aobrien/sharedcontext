# Pilot Definition Snapshot

Date: 2026-07-07
Session topic: Prototype shared context for domain knowledge and skill sets for AI agents and humans
Mode: Facilitator

## Objective
Design a GitHub-based shared-context system using Google's open knowledge format, with GitHub Actions extracting keywords/phrases into a searchable database, then expose data via API (Go) and UI (React).

## Core Questions Raised
- Who will use it and how?
- Who uploads and validates context?
- How are agents configured to consume context?
- How are conflicts identified and resolved?
- What metrics prove usage, adoption, growth, and value?
- Will this replace or augment SharePoint/Confluence?
- What pilot criteria define success?

## Failure-Mode Questions (Pre-Mortem)
- Why would adoption fail?
- What happens if data is inaccurate or conflicting?
- Could data volume create low-trust outputs/hallucinations?
- Is contribution/upload too hard?
- Are retrieval failures domain-specific?
- Are domain boundaries too broad or wrong?
- Are review and PR approval cycles too slow or under-skilled?
- Is the initiative perceived as overkill?

## Critical Assumption
Agents can reliably access shared context and use it cost-effectively enough to generate positive ROI.

## Early Success Signals
- API metrics show agent access and usage of context.
- Users reference keywords in requirements and agents can guide implementation, suggest options, and flag conflicts.
- Faster and more accurate implementation outcomes.
- Steady growth in context uploads.
- Cross-functional value (business, ops, development).

## Constraint Map
Real constraints:
- Agent configuration/access setup risk.
- Context accuracy risk.
- Limited domain coverage.
- Disagreement on correct information.
- Misleading/wrong keywords.
- Slow or complex feedback loop.

Perceived constraints:
- Job security concerns.
- Usability concerns (system feels hard).

## Mitigation Ideas Captured
- Document/build skills for configuring agents.
- Define business and IT context owners.
- Import existing SharePoint/Confluence content to avoid an empty knowledge base.
- Establish conflict identification/resolution workflow early.
- Enable users to update keywords/labels.

## Morphology (Pilot Design Choices)
- Ingestion: Markdown docs merged via GitHub; Actions populate database.
- Conflict governance: Pre-merge checks to detect conflicting statements.
- Retrieval/indexing: Keyword-based API retrieval.
- Contribution model: Start with git workflow, then add web workflow.

## Scenario Cross
Axes selected:
- Adoption level (low/high)
- Data quality/accuracy level (low/high)

Quadrant strategies:
- Low adoption, low quality: Improve quality.
- Low adoption, high quality: Promote value, simplify access and agent creation.
- High adoption, low quality: Engage business/analyst teams to resolve quality issues.
- High adoption, high quality: Maintain with cross-disciplinary engagement.

No-regret move:
Start with the simplest visible domain to demonstrate value quickly.

## Pilot Domain and Use Cases
Starter domain:
- User Authentication

Initial pilot use cases:
1. Agent implementation guidance
2. Conflict resolution
3. Human interface to validate rule correctness

## Day-One Must-Haves (MoSCoW: Must)
1. Interactive script that asks a few questions and generates an agent configured to access shared context — no documentation reading required.
2. Core technical stack running and accessible even if initial context data is minimal.
3. Mechanism for both agents and humans to begin populating shared context from day one.

## Pilot Acceptance Tests
| # | Must-Have | Pass Condition | Fail Signal |
|---|-----------|----------------|-------------|
| 1 | Agent creation | Agent created and accessing shared context within 5 minutes | Agent creation failed |
| 2 | Retrieval speed/accuracy | System finds and returns accurate context in ≤ 2 seconds | Retrieval failed |
| 3 | User engagement | Users are engaged and excited to browse and contribute context | Adoption failed |

## Kill Criterion
If agents cannot reliably access shared context cost-effectively enough to produce positive ROI, the pilot is stopped.

## Convergence Status
Pilot definition complete. Ready for next phase: product brief or PRD creation.

## Source of Truth
Raw chronological log:
- .memlog.md in this same folder
