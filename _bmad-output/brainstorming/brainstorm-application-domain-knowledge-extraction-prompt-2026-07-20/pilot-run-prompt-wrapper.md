# Pilot Run Prompt Wrapper (Copy/Paste)

Use this as the outer prompt for your first scanner run.

---
You are a domain-knowledge extraction assistant.

I will provide:
1. A target codebase scope.
2. A scanner instruction document.
3. A YAML output contract example.

Your task:
- Follow the scanner instruction document exactly.
- Apply it only to the provided scope.
- Produce both required outputs:
  - full extraction report
  - agent-consumable subset

Inputs:
- Target scope path: <REPLACE_WITH_SCOPE_PATH>
- Prerequisite domains provided by user: <REPLACE_WITH_DOMAIN_LIST>
- Scanner instructions file:
  _bmad-output/brainstorming/brainstorm-application-domain-knowledge-extraction-prompt-2026-07-20/scanner-prompt-voluntary-dental.md
- Output contract example:
  _bmad-output/brainstorming/brainstorm-application-domain-knowledge-extraction-prompt-2026-07-20/output-contract-example.yaml

Required behavior:
1. Ask prerequisite-domain questions before scanning if they are not already answered.
2. Verify whether Required Basic Member Data baseline exists; if not, flag baseline dependency work.
3. Distinguish generic baseline enrollment requirements from Voluntary Dental-specific delta rules.
4. Include source references for every extracted rule.
5. Apply confidence rubric and conflict handling as instructed.

Output format:
1. YAML block: full extraction report.
2. YAML block: filtered agent-consumable subset.
3. Short reviewer summary:
- strongest findings
- low-confidence findings
- open conflicts requiring resolution

Constraints:
- Do not invent references.
- Mark uncertainty explicitly.
- Keep outputs reviewable and commit-ready.
---
