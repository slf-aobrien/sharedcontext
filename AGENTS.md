# AGENTS Instructions

These instructions apply to this repository/workspace.

## Command Execution Policy

- Do not run `uv` commands.
- Do not run `rg` commands.
- Use alternatives:
  - For Python scripts, use `python3` directly.
  - For text search, use `grep`.
  - For file discovery, use `find`.

## Priority And Scope

- Treat this file as repository-level agent guidance for all tasks in this workspace.
- If a task requires command execution, follow the policy above unless the user explicitly overrides it for that task.

## Rationale

This repository standard avoids relying on `uv` and `rg` so workflow behavior remains consistent across environments.
