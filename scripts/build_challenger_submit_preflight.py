#!/usr/bin/env python3
"""Build a challenger submit preflight report from current gate artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def candidate_summary(manifest: dict[str, Any], candidate_name: str) -> dict[str, Any]:
    return {
        "candidate_name": candidate_name,
        "dataset_version": manifest.get("dataset_version"),
        "prompt_version": manifest.get("prompt_version"),
        "eval_version": manifest.get("eval_version"),
        "model_version": manifest.get("model_version"),
        "manifest_status": manifest.get("status"),
        "mode": manifest.get("mode"),
        "training_rows": int(manifest.get("training_rows") or 0),
        "validation_rows": int(manifest.get("validation_rows") or 0),
        "notes": str(manifest.get("notes") or ""),
    }


def build_candidate_decision(
    candidate: dict[str, Any],
    gate_summary: dict[str, Any],
    synthetic_shadow: dict[str, Any],
    offline_shadow: dict[str, Any],
    real_shadow_status: str,
) -> dict[str, Any]:
    blocking_reasons: list[str] = []

    if candidate["manifest_status"] != "prepared":
        blocking_reasons.append(f"manifest_status is {candidate['manifest_status']}")
    if candidate["mode"] != "dry_run":
        blocking_reasons.append(f"mode is {candidate['mode']}")
    if gate_summary["blind_holdout_pass_rate"] < 0.95:
        blocking_reasons.append(
            f"blind_holdout50_validator {gate_summary['blind_holdout_pass_rate']:.4f} < 0.9500"
        )
    if synthetic_shadow["promotion_decision"] != "promote":
        blocking_reasons.append(
            "synthetic_shadow_day0 is "
            f"{synthetic_shadow['promotion_decision']} "
            f"(agreement={synthetic_shadow['operator_agreement_rate']:.4f})"
        )
    if synthetic_shadow["critical_disagreement_count"] > 0:
        blocking_reasons.append(
            f"synthetic_shadow_day0 critical_disagreement_count={synthetic_shadow['critical_disagreement_count']}"
        )
    if real_shadow_status != "pass":
        blocking_reasons.append(f"real_shadow_mode_status is {real_shadow_status}")

    recommendation = "blocked" if blocking_reasons else "ready_for_submit"
    preferred_if_unblocked = candidate["dataset_version"] == "ds_v13"

    return {
        **candidate,
        "blind_holdout50_validator_pass_rate": gate_summary["blind_holdout_pass_rate"],
        "blind_holdout50_validator_promotion": gate_summary["promotion_decision"],
        "synthetic_shadow_day0_agreement_rate": synthetic_shadow["operator_agreement_rate"],
        "synthetic_shadow_day0_promotion": synthetic_shadow["promotion_decision"],
        "offline_shadow_agreement_rate": offline_shadow["operator_agreement_rate"],
        "offline_shadow_promotion": offline_shadow["promotion_decision"],
        "real_shadow_mode_status": real_shadow_status,
        "preferred_if_unblocked": preferred_if_unblocked,
        "submit_recommendation": recommendation,
        "blocking_reasons": blocking_reasons,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Challenger Submit Preflight",
        "",
        "## Current Gate Context",
        "",
        f"- baseline_model: `{summary['baseline_model']}`",
        f"- blind_holdout50_validator_pass_rate: `{summary['blind_holdout50_validator_pass_rate']}`",
        f"- blind_holdout50_validator_promotion: `{summary['blind_holdout50_validator_promotion']}`",
        f"- synthetic_shadow_day0_agreement_rate: `{summary['synthetic_shadow_day0_agreement_rate']}`",
        f"- synthetic_shadow_day0_promotion: `{summary['synthetic_shadow_day0_promotion']}`",
        f"- offline_shadow_agreement_rate: `{summary['offline_shadow_agreement_rate']}`",
        f"- offline_shadow_promotion: `{summary['offline_shadow_promotion']}`",
        f"- real_shadow_mode_status: `{summary['real_shadow_mode_status']}`",
        "",
        "## Candidate Decisions",
        "",
    ]

    for candidate in summary["candidates"]:
        lines.extend(
            [
                f"### {candidate['candidate_name']}",
                "",
                f"- dataset_version: `{candidate['dataset_version']}`",
                f"- prompt_version: `{candidate['prompt_version']}`",
                f"- eval_version: `{candidate['eval_version']}`",
                f"- model_version: `{candidate['model_version']}`",
                f"- manifest_status: `{candidate['manifest_status']}`",
                f"- training_rows: `{candidate['training_rows']}`",
                f"- validation_rows: `{candidate['validation_rows']}`",
                f"- preferred_if_unblocked: `{candidate['preferred_if_unblocked']}`",
                f"- submit_recommendation: `{candidate['submit_recommendation']}`",
            ]
        )
        if candidate["blocking_reasons"]:
            lines.append("- blocking_reasons:")
            for reason in candidate["blocking_reasons"]:
                lines.append(f"  - `{reason}`")
        else:
            lines.append("- blocking_reasons: 없음")
        lines.append("")

    lines.extend(
        [
            "## Decision Rule",
            "",
            "- `blind_holdout50 validator >= 0.95`가 아니면 submit 금지",
            "- `synthetic shadow day0 promote`가 아니면 submit 금지",
            "- `real_shadow_mode_status=pass`가 아니면 submit 금지",
            "- 두 candidate가 모두 열리면 `preferred_if_unblocked=true`인 쪽을 우선 검토",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline-model",
        default="ds_v11/prompt_v5_methodfix_batch14",
    )
    parser.add_argument(
        "--gate-report",
        default="artifacts/reports/product_readiness_gate_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50_validator_applied.json",
    )
    parser.add_argument(
        "--synthetic-shadow-report",
        default="artifacts/reports/shadow_mode_ds_v11_day0_seed.json",
    )
    parser.add_argument(
        "--offline-shadow-report",
        default="artifacts/reports/shadow_mode_ds_v11_blind_holdout50_offline.json",
    )
    parser.add_argument(
        "--candidate-manifest",
        action="append",
        required=True,
        help="Candidate manifest path. Pass multiple times.",
    )
    parser.add_argument(
        "--real-shadow-mode-status",
        default="not_run",
        help="Current real shadow mode status: not_run, hold, pass, rollback",
    )
    parser.add_argument(
        "--output-prefix",
        default="artifacts/reports/challenger_submit_preflight",
    )
    args = parser.parse_args()

    gate = load_json(Path(args.gate_report))["gate_summary"]
    synthetic_shadow = load_json(Path(args.synthetic_shadow_report))
    offline_shadow = load_json(Path(args.offline_shadow_report))

    candidates: list[dict[str, Any]] = []
    for manifest_path in args.candidate_manifest:
        manifest = load_json(Path(manifest_path))
        candidate = candidate_summary(manifest, Path(manifest_path).stem)
        candidates.append(
            build_candidate_decision(
                candidate,
                gate,
                synthetic_shadow,
                offline_shadow,
                args.real_shadow_mode_status,
            )
        )

    summary = {
        "baseline_model": args.baseline_model,
        "blind_holdout50_validator_pass_rate": gate["blind_holdout_pass_rate"],
        "blind_holdout50_validator_promotion": gate["promotion_decision"],
        "synthetic_shadow_day0_agreement_rate": synthetic_shadow["operator_agreement_rate"],
        "synthetic_shadow_day0_promotion": synthetic_shadow["promotion_decision"],
        "offline_shadow_agreement_rate": offline_shadow["operator_agreement_rate"],
        "offline_shadow_promotion": offline_shadow["promotion_decision"],
        "real_shadow_mode_status": args.real_shadow_mode_status,
        "candidates": candidates,
    }

    output_prefix = Path(args.output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")

    print(f"summary_json: {json_path}")
    print(f"summary_md: {md_path}")
    for candidate in candidates:
        print(f"{candidate['dataset_version']}: {candidate['submit_recommendation']}")


if __name__ == "__main__":
    main()
