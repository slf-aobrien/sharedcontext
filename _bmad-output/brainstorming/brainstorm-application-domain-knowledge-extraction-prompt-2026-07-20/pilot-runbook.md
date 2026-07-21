# Pilot Runbook: Domain Knowledge Scanner

## Purpose
Run a controlled pilot of the voluntary dental domain-knowledge scanner prompt against a real codebase, evaluate output quality, and capture refinement notes.

## Inputs
- Scanner prompt:
  - _bmad-output/brainstorming/brainstorm-application-domain-knowledge-extraction-prompt-2026-07-20/scanner-prompt-voluntary-dental.md
- Output contract reference:
  - _bmad-output/brainstorming/brainstorm-application-domain-knowledge-extraction-prompt-2026-07-20/output-contract-example.yaml
- Intent and success criteria:
  - _bmad-output/brainstorming/brainstorm-application-domain-knowledge-extraction-prompt-2026-07-20/brainstorm-intent.md
- Target codebase path (set by operator)

## Pilot Scope Guidance
Start narrow:
- One enrollment flow or one module tied to Voluntary Dental enrollment.
- Include frontend and backend only if both contain relevant rules.

Avoid first-run anti-patterns:
- Do not scan entire monolith in the first run.
- Do not skip prerequisite domain check.

## Execution Steps
1. Select target scope.
- Choose a bounded folder or feature area.
- Note why this scope was selected.

2. Confirm prerequisite domains.
- Check whether baseline concept artifacts exist for Required Basic Member Data.
- If missing, create or flag as dependency before continuing.

3. Run the prompt.
- Use the wrapper in pilot-run-prompt-wrapper.md.
- Provide the selected codebase scope and any known prerequisite domains.

4. Produce both required outputs.
- Full extraction report (includes conflicted/pending).
- Agent-safe subset (approved and unconflicted only).

5. Validate against quality checks.
- Every rule has traceable references.
- Confidence level follows rubric.
- Conflict rationale is documented when flagged.
- Generic baseline vs dental-specific delta is cleanly separated.

6. Record findings and gaps.
- Log false positives (noise).
- Log missing expected rules.
- Log confidence misclassification.
- Log conflict detection misses.

## Review Checklist
- Rule evidence quality:
  - Are references precise enough for reviewer verification?
- Rule signal quality:
  - Are low-signal, single-reference items downgraded?
- Scope discipline:
  - Are generic enrollment rules minimized unless needed for context?
- Conflict governance:
  - Are conflicted records commit-ready but excluded from agent-safe output?
- Usability:
  - Can a reviewer decide accept/reject/conflict-pending quickly?

## Recommended Output Locations (for pilot)
- Full report:
  - _bmad-output/brainstorming/brainstorm-application-domain-knowledge-extraction-prompt-2026-07-20/pilot-full-report.yaml
- Agent-safe subset:
  - _bmad-output/brainstorming/brainstorm-application-domain-knowledge-extraction-prompt-2026-07-20/pilot-agent-subset.yaml
- Pilot notes:
  - _bmad-output/brainstorming/brainstorm-application-domain-knowledge-extraction-prompt-2026-07-20/pilot-findings.md

## Iteration Loop
After each pilot:
1. Keep what worked in the prompt.
2. Tighten weak instruction areas.
3. Update confidence and conflict wording if needed.
4. Re-run on the same scope once, then expand scope gradually.
