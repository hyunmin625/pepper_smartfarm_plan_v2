#!/usr/bin/env python3
"""Validate OpenAI SFT chat-format JSONL files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append((line_number, row))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    errors: list[str] = []
    total_rows = 0
    for file_name in args.files:
        path = Path(file_name)
        rows = load_jsonl(path)
        total_rows += len(rows)
        for line_number, row in rows:
            prefix = f"{path}:{line_number}"
            unexpected_keys = sorted(set(row.keys()) - {"messages"})
            if unexpected_keys:
                errors.append(f"{prefix}: unexpected top-level keys: {', '.join(unexpected_keys)}")
            messages = row.get("messages")
            if not isinstance(messages, list) or len(messages) < 2:
                errors.append(f"{prefix}: messages must be an array with at least 2 items")
                continue
            roles = [message.get("role") for message in messages if isinstance(message, dict)]
            if "user" not in roles or "assistant" not in roles:
                errors.append(f"{prefix}: messages must include user and assistant roles")
            for index, message in enumerate(messages, start=1):
                if not isinstance(message, dict):
                    errors.append(f"{prefix}: messages[{index}] must be an object")
                    continue
                if message.get("role") not in {"system", "user", "assistant"}:
                    errors.append(f"{prefix}: messages[{index}].role invalid")
                content = message.get("content")
                if not isinstance(content, str) or not content.strip():
                    errors.append(f"{prefix}: messages[{index}].content must be non-empty string")

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"files: {len(args.files)}")
    print(f"rows: {total_rows}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
