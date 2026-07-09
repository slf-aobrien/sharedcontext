# Project Context

## Command Execution Policy

- Do not run `uv` commands.
- Do not run `rg` commands.
- Use alternatives:
  - For Python scripts, use `python3` directly.
  - For text search, use `grep`.
  - For file discovery, use `find`.

## Rationale

This repository standard avoids relying on `uv` and `rg` so workflow behavior remains consistent across environments.

## Canonical Source

This policy is canonical in `AGENTS.md` at the repository root.
