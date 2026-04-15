#!/usr/bin/env python3
"""Compare two eval JSONL result files for output schema drift.

Used after fine-tuning to detect when a new model checkpoint has lost
top-level keys (`blocked_action_type` disappearing is how ds_v12 silently
broke forbidden_action), introduced new unexpected keys, or drifted its
citation sub-schema (`chunk_id,document_id` → `doc_id,doc_type`).

Exit code 0 when no drift is flagged (all deltas within thresholds).
Exit code 1 when any of the alarm conditions fire.

Typical invocation after a new fine-tune:

    python3 scripts/compare_output_schemas.py \
        --reference artifacts/reports/fine_tuned_model_eval_ds_v11_..._extended200.jsonl \
        --candidate artifacts/reports/fine_tuned_model_eval_ds_v12_extended200.jsonl \
        --output artifacts/reports/schema_drift_ds_v12_vs_ds_v11.md

Alarm thresholds (default):
  - new top-level keys in candidate (not in reference) >= 3
  - any reference top-level key with count >= 10 drops by >= 50% in candidate
  - any *rare* reference key with count >= 5 disappears entirely in candidate
  - citations single-shape coverage in candidate < 80% (reference is 100% by design)
  - strict_json_rate drop >= 0.05
  - pass_rate drop >= 0.15
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def extract_output(rec: dict[str, Any]) -> dict[str, Any] | None:
    out = (rec.get("response") or {}).get("parsed_output") or rec.get("raw_output")
    return out if isinstance(out, dict) else None


def top_level_key_counts(records: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for rec in records:
        out = extract_output(rec)
        if isinstance(out, dict):
            counter.update(out.keys())
    return counter


def citation_shape_counts(records: list[dict[str, Any]]) -> Counter[tuple[str, ...]]:
    counter: Counter[tuple[str, ...]] = Counter()
    for rec in records:
        out = extract_output(rec)
        if not isinstance(out, dict):
            continue
        cits = out.get("citations") or []
        if not isinstance(cits, list):
            counter[("<non-list>",)] += 1
            continue
        if not cits:
            counter[("<empty>",)] += 1
            continue
        for cit in cits:
            if isinstance(cit, dict):
                counter[tuple(sorted(cit.keys()))] += 1
            elif isinstance(cit, str):
                counter[("<string>",)] += 1
            else:
                counter[("<non-dict>",)] += 1
    return counter


def rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def pass_rate(records: list[dict[str, Any]]) -> float:
    if not records:
        return 0.0
    return rate(sum(1 for r in records if r.get("passed")), len(records))


def strict_json_rate(records: list[dict[str, Any]]) -> float:
    if not records:
        return 0.0
    return rate(sum(1 for r in records if r.get("strict_json_ok")), len(records))


def analyze(
    reference_records: list[dict[str, Any]],
    candidate_records: list[dict[str, Any]],
    *,
    new_key_threshold: int = 3,
    common_key_drop_ratio: float = 0.5,
    rare_key_min_count: int = 5,
    citation_majority_floor: float = 0.80,
    strict_json_drop_limit: float = 0.05,
    pass_rate_drop_limit: float = 0.15,
) -> dict[str, Any]:
    ref_keys = top_level_key_counts(reference_records)
    cand_keys = top_level_key_counts(candidate_records)
    ref_cits = citation_shape_counts(reference_records)
    cand_cits = citation_shape_counts(candidate_records)

    # Key drift computation
    new_keys = sorted(k for k in cand_keys if k not in ref_keys and cand_keys[k] > 0)
    missing_keys = sorted(k for k in ref_keys if k not in cand_keys and ref_keys[k] > 0)
    common_key_drops: list[dict[str, Any]] = []
    for k, ref_count in ref_keys.most_common():
        if ref_count < 10:
            continue
        cand_count = cand_keys.get(k, 0)
        if cand_count == 0:
            common_key_drops.append({"key": k, "reference": ref_count, "candidate": 0, "drop_ratio": 1.0})
            continue
        drop_ratio = (ref_count - cand_count) / ref_count
        if drop_ratio >= common_key_drop_ratio:
            common_key_drops.append({
                "key": k,
                "reference": ref_count,
                "candidate": cand_count,
                "drop_ratio": round(drop_ratio, 4),
            })

    rare_key_losses: list[dict[str, Any]] = []
    for k, ref_count in ref_keys.items():
        if ref_count >= rare_key_min_count and k not in cand_keys:
            rare_key_losses.append({"key": k, "reference_count": ref_count})

    # Citation shape analysis
    total_cand_citations = sum(cand_cits.values())
    total_ref_citations = sum(ref_cits.values())
    cand_majority_shape, cand_majority_count = (None, 0)
    if cand_cits:
        cand_majority_shape, cand_majority_count = cand_cits.most_common(1)[0]
    cand_majority_ratio = rate(cand_majority_count, total_cand_citations)
    ref_majority_shape, ref_majority_count = (None, 0)
    if ref_cits:
        ref_majority_shape, ref_majority_count = ref_cits.most_common(1)[0]
    ref_majority_ratio = rate(ref_majority_count, total_ref_citations)

    # Rate drops
    ref_pass = pass_rate(reference_records)
    cand_pass = pass_rate(candidate_records)
    ref_strict = strict_json_rate(reference_records)
    cand_strict = strict_json_rate(candidate_records)

    alarms: list[str] = []
    if len(new_keys) >= new_key_threshold:
        alarms.append(f"new_top_level_keys: {len(new_keys)} ≥ {new_key_threshold}")
    if common_key_drops:
        alarms.append(f"common_key_drops: {len(common_key_drops)}")
    if rare_key_losses:
        alarms.append(f"rare_key_losses: {len(rare_key_losses)}")
    if cand_majority_ratio < citation_majority_floor:
        alarms.append(
            f"citations_majority_shape_below_floor: {cand_majority_ratio} < {citation_majority_floor}"
        )
    if ref_pass - cand_pass >= pass_rate_drop_limit:
        alarms.append(f"pass_rate_drop: {round(ref_pass - cand_pass, 4)} >= {pass_rate_drop_limit}")
    if ref_strict - cand_strict >= strict_json_drop_limit:
        alarms.append(f"strict_json_rate_drop: {round(ref_strict - cand_strict, 4)} >= {strict_json_drop_limit}")

    return {
        "reference_records": len(reference_records),
        "candidate_records": len(candidate_records),
        "reference_pass_rate": ref_pass,
        "candidate_pass_rate": cand_pass,
        "reference_strict_json_rate": ref_strict,
        "candidate_strict_json_rate": cand_strict,
        "reference_top_keys": ref_keys.most_common(20),
        "candidate_top_keys": cand_keys.most_common(30),
        "new_keys": new_keys,
        "missing_keys": missing_keys,
        "common_key_drops": common_key_drops,
        "rare_key_losses": rare_key_losses,
        "reference_citation_shapes": ref_cits.most_common(10),
        "candidate_citation_shapes": cand_cits.most_common(12),
        "reference_citation_majority": {
            "shape": list(ref_majority_shape) if isinstance(ref_majority_shape, tuple) else ref_majority_shape,
            "count": ref_majority_count,
            "ratio": ref_majority_ratio,
        },
        "candidate_citation_majority": {
            "shape": list(cand_majority_shape) if isinstance(cand_majority_shape, tuple) else cand_majority_shape,
            "count": cand_majority_count,
            "ratio": cand_majority_ratio,
        },
        "alarms": alarms,
    }


def render_markdown(analysis: dict[str, Any], reference_path: Path, candidate_path: Path) -> str:
    lines: list[str] = []
    lines.append(f"# Output schema drift report")
    lines.append("")
    lines.append(f"- reference: `{reference_path.as_posix()}`")
    lines.append(f"- candidate: `{candidate_path.as_posix()}`")
    lines.append("")
    lines.append("## Overall")
    lines.append("")
    lines.append("| metric | reference | candidate | Δ |")
    lines.append("|---|---:|---:|---:|")
    lines.append(
        f"| records | {analysis['reference_records']} | {analysis['candidate_records']} | {analysis['candidate_records']-analysis['reference_records']:+} |"
    )
    lines.append(
        f"| pass_rate | {analysis['reference_pass_rate']} | {analysis['candidate_pass_rate']} | {round(analysis['candidate_pass_rate']-analysis['reference_pass_rate'], 4):+} |"
    )
    lines.append(
        f"| strict_json_rate | {analysis['reference_strict_json_rate']} | {analysis['candidate_strict_json_rate']} | {round(analysis['candidate_strict_json_rate']-analysis['reference_strict_json_rate'], 4):+} |"
    )
    lines.append("")
    lines.append("## Alarms")
    lines.append("")
    if analysis["alarms"]:
        for alarm in analysis["alarms"]:
            lines.append(f"- ⚠️  **{alarm}**")
    else:
        lines.append("- ✅ no drift alarms fired")
    lines.append("")
    lines.append("## New top-level keys (candidate-only)")
    lines.append("")
    if analysis["new_keys"]:
        for k in analysis["new_keys"]:
            lines.append(f"- `{k}`")
    else:
        lines.append("- 없음")
    lines.append("")
    lines.append("## Missing top-level keys (reference-only)")
    lines.append("")
    if analysis["missing_keys"]:
        for k in analysis["missing_keys"]:
            lines.append(f"- `{k}`")
    else:
        lines.append("- 없음")
    lines.append("")
    lines.append("## Common key drops (ref count ≥10, ≥50% drop)")
    lines.append("")
    if analysis["common_key_drops"]:
        lines.append("| key | reference | candidate | drop_ratio |")
        lines.append("|---|---:|---:|---:|")
        for item in analysis["common_key_drops"]:
            lines.append(
                f"| `{item['key']}` | {item['reference']} | {item['candidate']} | {item['drop_ratio']} |"
            )
    else:
        lines.append("- 없음")
    lines.append("")
    lines.append("## Rare-key losses (ref count ≥5, candidate 0)")
    lines.append("")
    if analysis["rare_key_losses"]:
        for item in analysis["rare_key_losses"]:
            lines.append(f"- `{item['key']}` (reference count: {item['reference_count']})")
    else:
        lines.append("- 없음")
    lines.append("")
    lines.append("## Citation shape distribution")
    lines.append("")
    lines.append(
        f"- reference majority shape: `{analysis['reference_citation_majority']['shape']}` "
        f"({analysis['reference_citation_majority']['ratio']} of citations)"
    )
    lines.append(
        f"- candidate majority shape: `{analysis['candidate_citation_majority']['shape']}` "
        f"({analysis['candidate_citation_majority']['ratio']} of citations)"
    )
    lines.append("")
    lines.append("### reference citation shapes")
    lines.append("")
    lines.append("| shape | count |")
    lines.append("|---|---:|")
    for shape, count in analysis["reference_citation_shapes"]:
        lines.append(f"| `{shape}` | {count} |")
    lines.append("")
    lines.append("### candidate citation shapes")
    lines.append("")
    lines.append("| shape | count |")
    lines.append("|---|---:|")
    for shape, count in analysis["candidate_citation_shapes"]:
        lines.append(f"| `{shape}` | {count} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two eval jsonls for output schema drift")
    parser.add_argument("--reference", required=True, help="Reference eval jsonl (known-good baseline, e.g. ds_v11)")
    parser.add_argument("--candidate", required=True, help="Candidate eval jsonl (new model under test)")
    parser.add_argument("--output", default=None, help="Optional markdown output path")
    parser.add_argument("--json-output", default=None, help="Optional raw JSON analysis output path")
    parser.add_argument("--new-key-threshold", type=int, default=3)
    parser.add_argument("--common-key-drop-ratio", type=float, default=0.5)
    parser.add_argument("--rare-key-min-count", type=int, default=5)
    parser.add_argument("--citation-majority-floor", type=float, default=0.80)
    parser.add_argument("--strict-json-drop-limit", type=float, default=0.05)
    parser.add_argument("--pass-rate-drop-limit", type=float, default=0.15)
    parser.add_argument("--exit-on-alarm", action="store_true", help="Return exit code 1 when alarms fire")
    args = parser.parse_args()

    ref_path = Path(args.reference)
    cand_path = Path(args.candidate)
    reference_records = load_records(ref_path)
    candidate_records = load_records(cand_path)
    analysis = analyze(
        reference_records,
        candidate_records,
        new_key_threshold=args.new_key_threshold,
        common_key_drop_ratio=args.common_key_drop_ratio,
        rare_key_min_count=args.rare_key_min_count,
        citation_majority_floor=args.citation_majority_floor,
        strict_json_drop_limit=args.strict_json_drop_limit,
        pass_rate_drop_limit=args.pass_rate_drop_limit,
    )

    markdown = render_markdown(analysis, ref_path, cand_path)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")
        print(f"wrote markdown: {out_path.as_posix()}")
    if args.json_output:
        json_path = Path(args.json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)

        def _to_serializable(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {str(k): _to_serializable(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_to_serializable(v) for v in obj]
            return obj

        json_path.write_text(
            json.dumps(_to_serializable(analysis), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"wrote json: {json_path.as_posix()}")

    print(f"reference_records: {analysis['reference_records']}")
    print(f"candidate_records: {analysis['candidate_records']}")
    print(f"pass_rate: {analysis['reference_pass_rate']} → {analysis['candidate_pass_rate']}")
    print(f"strict_json_rate: {analysis['reference_strict_json_rate']} → {analysis['candidate_strict_json_rate']}")
    print(f"new_keys: {len(analysis['new_keys'])}")
    print(f"common_key_drops: {len(analysis['common_key_drops'])}")
    print(f"rare_key_losses: {len(analysis['rare_key_losses'])}")
    print(f"ref citation majority: {analysis['reference_citation_majority']}")
    print(f"cand citation majority: {analysis['candidate_citation_majority']}")
    print(f"alarms ({len(analysis['alarms'])}): {analysis['alarms']}")

    if analysis["alarms"] and args.exit_on_alarm:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
