#!/usr/bin/env python3
"""Validate malformed JSON recovery paths for the LLM response parser."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from llm_orchestrator.response_parser import parse_response  # noqa: E402


def main() -> int:
    cases = [
        {
            "case_id": "strict-json",
            "raw": '{"risk_level":"medium","recommended_actions":[{"action_type":"create_alert"}]}',
            "expect_json_object_ok": True,
        },
        {
            "case_id": "markdown-fence",
            "raw": "```json\n{\"risk_level\":\"high\",\"recommended_actions\":[{\"action_type\":\"request_human_check\"}]}\n```",
            "expect_json_object_ok": True,
        },
        {
            "case_id": "smart-quotes-and-trailing-comma",
            "raw": "분석 결과입니다. {“risk_level”: “unknown”, “recommended_actions”: [{“action_type”: “pause_automation”,}],}",
            "expect_json_object_ok": True,
        },
        {
            "case_id": "irrecoverable",
            "raw": "operator review required without structured json",
            "expect_json_object_ok": False,
        },
    ]
    errors: list[str] = []
    results: list[dict[str, object]] = []
    for case in cases:
        parsed = parse_response(case["raw"])
        if parsed.json_object_ok != case["expect_json_object_ok"]:
            errors.append(f"{case['case_id']} expected json_object_ok={case['expect_json_object_ok']}, got {parsed.json_object_ok}")
        results.append(
            {
                "case_id": case["case_id"],
                "strict_json_ok": parsed.strict_json_ok,
                "recovered_json_ok": parsed.recovered_json_ok,
                "json_object_ok": parsed.json_object_ok,
                "parse_error": parsed.parse_error,
                "parsed_keys": sorted((parsed.parsed_output or {}).keys()),
            }
        )
    print(json.dumps({"errors": errors, "results": results}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
