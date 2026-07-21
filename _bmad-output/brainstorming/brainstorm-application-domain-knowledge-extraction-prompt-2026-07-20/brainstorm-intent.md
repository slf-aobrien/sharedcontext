# Intent: Domain Knowledge Scanner Prompt

## Goal
Create a reusable prompt that scans an application codebase to extract embedded domain knowledge and outputs commit-ready knowledge artifacts.

## Focus Slice
Start with a narrow business slice:
- Enrolling a member in Voluntary Dental Coverage.

## Core Decisions
- Source priority: code first, documentation second.
- Traceability is required for every extracted rule.
- Confidence should increase with cross-reference evidence across multiple locations/sources.
- Conflicts are commit-allowed in any state when documented, but agent consumption must use only approved and unconflicted rules.
- Output should produce two deliverables each run:
  - Full extraction report (includes pending/conflicted items).
  - Agent-consumable subset (approved + unconflicted only).
- Knowledge should be organized by concept with three categories:
  - required-data
  - eligibility-rules
  - coverage-specific-rules
- Prompt must distinguish baseline prerequisites from coverage-specific deltas.

## Pre-Scan Dependency Check
The prompt should ask for prerequisite domains before scanning.
Initial prerequisite example:
- Required Basic Member Data

If prerequisite knowledge is missing in the repository, create a baseline concept artifact first or flag it as required dependency work.

## Why This Matters
This structure keeps extracted knowledge reviewable, traceable, and safe for downstream agent use while remaining flexible as new subjects are added.
