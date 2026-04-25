#!/usr/bin/env python3
"""Build a JSON/Markdown report from the ops-api runtime_gate payload."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCKER_ACTIONS = {
    "champion_not_ds_v11_frozen": "production champion을 ds_v11 frozen FT model로 되돌린다.",
    "shadow_window_no_window": "실제 운영 shadow case를 누적해 window report를 먼저 생성한다.",
    "shadow_window_hold": "real shadow window의 agreement/citation/residual 원인을 확인하고 hold를 해소한다.",
    "shadow_window_rollback": "critical disagreement 또는 rollback 원인을 residual backlog로 옮기고 자동 submit을 막는다.",
    "approval_queue_pending": "승인 대기 decision/automation trigger를 승인 또는 거절로 닫는다.",
    "policy_risk_events_present": "blocked/approval_required policy event 원인을 검토하고 재발 여부를 확인한다.",
    "critical_shadow_residuals_open": "critical real shadow residual을 먼저 수정하고 재검증한다.",
    "shadow_residuals_open": "open real shadow residual owner와 expected_fix를 확정한다.",
    "shadow_residual_fixes_unverified": "fixed residual이 같은 유형의 실제 shadow case에서 재발하지 않는지 검증한다.",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"{path}: expected JSON object")


def _fetch_dashboard_data(base_url: str, api_key: str | None) -> dict[str, Any]:
    request = urllib.request.Request(
        url=f"{base_url.rstrip('/')}/dashboard/data",
        headers={**({"x-api-key": api_key} if api_key else {})},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request) as response:  # noqa: S310
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else ""
        raise RuntimeError(f"GET /dashboard/data failed: HTTP {exc.code} {detail[:500]}") from exc
    return json.loads(body)


def _unwrap_dashboard_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return data if isinstance(data, dict) else {}


def build_report(payload: dict[str, Any], *, source: str) -> dict[str, Any]:
    data = _unwrap_dashboard_payload(payload)
    gate = data.get("runtime_gate") or {}
    summary = data.get("summary") or {}
    shadow_window = data.get("shadow_window") or {}
    residuals = data.get("shadow_residuals") or {}
    blockers = [str(item) for item in (gate.get("blockers") or [])]
    gate_state = str(gate.get("gate_state") or "unknown")
    runtime_mode = str(gate.get("runtime_mode") or "unknown")
    shadow_status = str(gate.get("shadow_window_status") or shadow_window.get("promotion_decision") or "unknown")
    submit_allowed = gate_state == "ready" and not blockers and shadow_status == "promote"

    return {
        "generated_at": _now_iso(),
        "source": source,
        "submit_allowed": submit_allowed,
        "gate_state": gate_state,
        "runtime_mode": runtime_mode,
        "shadow_window_status": shadow_status,
        "retriever_type": gate.get("retriever_type") or "keyword",
        "champion": gate.get("champion") or {},
        "approval_queue_count": int(gate.get("approval_queue_count") or 0),
        "policy_risk_event_count": int(gate.get("policy_risk_event_count") or 0),
        "policy_change_count": int(gate.get("policy_change_count") or 0),
        "open_residual_count": int(gate.get("open_residual_count") or residuals.get("open_residual_count") or 0),
        "critical_residual_count": int(
            gate.get("critical_residual_count") or residuals.get("critical_residual_count") or 0
        ),
        "unverified_fix_count": int(gate.get("unverified_fix_count") or residuals.get("unverified_fix_count") or 0),
        "blockers": blockers,
        "recommended_next_actions": [
            {
                "blocker": blocker,
                "next_action": BLOCKER_ACTIONS.get(
                    blocker,
                    "shadow window, approval queue, policy event, residual backlog 중 해당 원인을 확인한다.",
                ),
            }
            for blocker in blockers
        ],
        "summary_snapshot": {
            "decision_count": summary.get("decision_count"),
            "approval_pending_count": summary.get("approval_pending_count"),
            "automation_pending_count": summary.get("automation_pending_count"),
            "policy_event_count": summary.get("policy_event_count"),
            "alert_count": summary.get("alert_count"),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Runtime Gate Blocker Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- source: `{report['source']}`",
        f"- submit_allowed: `{report['submit_allowed']}`",
        f"- gate_state: `{report['gate_state']}`",
        f"- runtime_mode: `{report['runtime_mode']}`",
        f"- shadow_window_status: `{report['shadow_window_status']}`",
        f"- retriever_type: `{report['retriever_type']}`",
        f"- approval_queue_count: `{report['approval_queue_count']}`",
        f"- policy_risk_event_count: `{report['policy_risk_event_count']}`",
        f"- open_residual_count: `{report['open_residual_count']}`",
        f"- critical_residual_count: `{report['critical_residual_count']}`",
        f"- unverified_fix_count: `{report['unverified_fix_count']}`",
        "",
        "## Blockers",
        "",
    ]
    if report["blockers"]:
        for item in report["recommended_next_actions"]:
            lines.append(f"- `{item['blocker']}`: {item['next_action']}")
    else:
        lines.append("- 없음")
    lines.extend(["", "## Champion", ""])
    for key, value in (report.get("champion") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--input-json", default="")
    parser.add_argument("--output-json", default="artifacts/reports/runtime_gate_blockers.json")
    parser.add_argument("--output-md", default="artifacts/reports/runtime_gate_blockers.md")
    parser.add_argument("--fail-on-blocked", action="store_true")
    args = parser.parse_args()

    if not args.input_json and not args.base_url:
        print("ERROR set --input-json or --base-url", file=sys.stderr)
        return 2
    try:
        if args.input_json:
            source = args.input_json
            payload = _load_json(Path(args.input_json))
        else:
            source = f"{args.base_url.rstrip('/')}/dashboard/data"
            payload = _fetch_dashboard_data(args.base_url, args.api_key)
        report = build_report(payload, source=source)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "submit_allowed": report["submit_allowed"], "blockers": report["blockers"]}, ensure_ascii=False, indent=2))
    return 1 if args.fail_on_blocked and not report["submit_allowed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
