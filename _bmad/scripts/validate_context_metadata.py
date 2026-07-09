#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate markdown front matter against the context metadata contract.

This script is local-first and uses a single machine-readable schema artifact
as the source of truth for required fields and constraints.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "context_document_metadata.schema.json"
RFC3339_UTC_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


def split_frontmatter(text: str) -> tuple[str | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text

    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            fm = "\n".join(lines[1:idx])
            body = "\n".join(lines[idx + 1:])
            return fm, body

    return None, text


def parse_scalar(value: str) -> Any:
    token = value.strip()
    if token == "null":
        return None
    if token in {"true", "false"}:
        return token == "true"
    if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
        return token[1:-1]
    return token


def _parse_flow_sequence(value: str) -> list[Any]:
    token = value.strip()
    if not (token.startswith("[") and token.endswith("]")):
        raise ValueError(f"invalid flow-style sequence: {value}")

    inner = token[1:-1].strip()
    if inner == "":
        return []

    items: list[Any] = []
    current: list[str] = []
    quote_char: str | None = None

    for char in inner:
        if quote_char is not None:
            current.append(char)
            if char == quote_char:
                quote_char = None
            continue

        if char in {'"', "'"}:
            quote_char = char
            current.append(char)
            continue

        if char == ",":
            items.append(parse_scalar("".join(current)))
            current = []
            continue

        current.append(char)

    if quote_char is not None:
        raise ValueError(f"invalid flow-style sequence: {value}")

    items.append(parse_scalar("".join(current)))
    return items


def parse_simple_yaml_frontmatter(frontmatter: str) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    data: dict[str, Any] = {}
    warnings: list[tuple[str, str]] = []
    lines = frontmatter.splitlines()
    idx = 0

    while idx < len(lines):
        raw = lines[idx]
        if not raw.strip() or raw.lstrip().startswith("#"):
            idx += 1
            continue

        if ":" not in raw:
            idx += 1
            continue

        if raw.startswith(" ") or raw.startswith("\t"):
            idx += 1
            continue

        key, value = raw.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value in {"|", ">", "|-", ">-", "|+", ">+"}:
            warnings.append((key, "block scalars are not supported in context-document front matter"))
            idx += 1
            while idx < len(lines) and (not lines[idx].strip() or lines[idx].startswith((" ", "\t"))):
                idx += 1
            continue

        if value == "":
            items: list[Any] = []
            idx += 1
            while idx < len(lines):
                item_line = lines[idx]
                stripped = item_line.strip()
                if not stripped:
                    idx += 1
                    continue
                if not item_line.startswith((" ", "\t")):
                    break
                content = stripped
                if content.startswith("- "):
                    items.append(parse_scalar(content[2:]))
                else:
                    warnings.append((key, "nested YAML structures are not supported in context-document front matter"))
                idx += 1
            data[key] = items
            continue

        if value.startswith("["):
            try:
                data[key] = _parse_flow_sequence(value)
                if key == "keywords":
                    warnings.append((
                        key,
                        "must use block-list YAML for consistency (example: keywords:\n  - schema\n  - metadata)",
                    ))
            except ValueError:
                warnings.append((key, "unsupported YAML flow-style content"))
            idx += 1
            continue

        if value.startswith("{"):
            warnings.append((key, "inline mappings are not supported in context-document front matter"))
            idx += 1
            continue

        data[key] = parse_scalar(value)
        idx += 1

    return data, warnings


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _error(file_path: Path, field: str, message: str) -> dict[str, str]:
    return {
        "file": str(file_path),
        "field": field,
        "message": message,
    }


def build_helpers(errors: list[dict[str, str]], schema_path: Path) -> list[str]:
    helpers: list[str] = []
    has_keywords_style_error = any(
        err.get("field") == "keywords" and "block-list YAML for consistency" in err.get("message", "")
        for err in errors
    )
    if has_keywords_style_error:
        helpers.append(
            "For keywords formatting, see x-bmad-authoring-conventions "
            f"(keywords_yaml_style, keywords_yaml_example) in {schema_path}."
        )
    return helpers


def validate_metadata(metadata: dict[str, Any], schema: dict[str, Any], file_path: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    required = schema.get("required", [])
    props = schema.get("properties", {})

    for field in required:
        if field not in metadata:
            errors.append(_error(file_path, field, "missing required field"))

    if "status" in metadata:
        allowed = props.get("status", {}).get("enum", [])
        if metadata["status"] not in allowed:
            errors.append(_error(file_path, "status", f"must be one of: {', '.join(allowed)}"))

    for field in ("created", "updated"):
        if field in metadata:
            value = metadata[field]
            if not isinstance(value, str) or not RFC3339_UTC_RE.match(value):
                errors.append(_error(file_path, field, "must be RFC3339 UTC (YYYY-MM-DDTHH:MM:SSZ)"))

    if "validated-on" in metadata:
        value = metadata["validated-on"]
        if value is not None and (not isinstance(value, str) or not RFC3339_UTC_RE.match(value)):
            errors.append(_error(file_path, "validated-on", "must be null or RFC3339 UTC (YYYY-MM-DDTHH:MM:SSZ)"))

    if "keywords" in metadata:
        value = metadata["keywords"]
        if isinstance(value, str) and value.strip().startswith("[") and value.strip().endswith("]"):
            errors.append(_error(
                file_path,
                "keywords",
                "must use block-list YAML for consistency (example: keywords:\n  - schema\n  - metadata)",
            ))
        elif not isinstance(value, list) or not value:
            errors.append(_error(file_path, "keywords", "must be a non-empty list of strings"))
        elif any(not isinstance(item, str) or item.strip() == "" for item in value):
            errors.append(_error(file_path, "keywords", "must contain only non-empty strings"))

    for field in ("title", "domain", "description", "validated-by"):
        if field in metadata and (not isinstance(metadata[field], str) or metadata[field].strip() == ""):
            errors.append(_error(file_path, field, "must be a non-empty string"))

    return errors


def validate_paths(paths: list[Path], schema_path: Path = SCHEMA_PATH) -> dict[str, Any]:
    schema = load_schema(schema_path)
    errors: list[dict[str, str]] = []
    deprecated: list[str] = []

    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(_error(path, "file", f"unable to read file: {exc.strerror or str(exc)}"))
            continue
        except UnicodeDecodeError:
            errors.append(_error(path, "file", "unable to read file: not valid UTF-8 text"))
            continue

        frontmatter, _ = split_frontmatter(text)
        if frontmatter is None:
            errors.append(_error(path, "frontmatter", "missing YAML front matter"))
            continue

        metadata, warnings = parse_simple_yaml_frontmatter(frontmatter)
        for field, message in warnings:
            errors.append(_error(path, field, message))

        file_errors = validate_metadata(metadata, schema, path)
        errors.extend(file_errors)

        if not file_errors and metadata.get("status") == "deprecated":
            deprecated.append(str(path))

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "deprecated": deprecated,
        "schema": str(schema_path),
        "helpers": build_helpers(errors, schema_path),
    }


def collect_markdown_files(inputs: list[str]) -> tuple[list[Path], list[dict[str, str]]]:
    paths: list[Path] = []
    input_errors: list[dict[str, str]] = []
    for item in inputs:
        p = Path(item)
        if not p.exists():
            input_errors.append({
                "file": str(p),
                "field": "path",
                "message": "path does not exist",
            })
            continue

        if p.is_dir():
            paths.extend(sorted(x for x in p.rglob("*.md") if x.is_file()))
        elif p.is_file() and p.suffix.lower() == ".md":
            paths.append(p)
        elif p.is_file():
            input_errors.append({
                "file": str(p),
                "field": "path",
                "message": "file is not markdown (.md)",
            })
    return paths, input_errors


def validate_inputs(inputs: list[str], schema_path: Path = SCHEMA_PATH) -> dict[str, Any]:
    files, input_errors = collect_markdown_files(inputs)
    result = validate_paths(files, schema_path=schema_path)

    if input_errors:
        result["errors"].extend(input_errors)
        result["ok"] = False

    if not files and not input_errors:
        result["ok"] = False
        result["errors"].append({
            "file": "<input>",
            "field": "paths",
            "message": "no markdown files found to validate",
        })

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate markdown context document front matter metadata.")
    parser.add_argument("paths", nargs="+", help="Markdown files or directories to validate")
    parser.add_argument("--schema", help="Path to schema JSON (defaults to canonical schema)")
    parser.add_argument("--output", help="Write JSON report to this file instead of stdout")
    args = parser.parse_args(argv)

    schema_path = Path(args.schema).resolve() if args.schema else SCHEMA_PATH
    result = validate_inputs(args.paths, schema_path=schema_path)

    output = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
