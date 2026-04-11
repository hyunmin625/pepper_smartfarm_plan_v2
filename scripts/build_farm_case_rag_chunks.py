#!/usr/bin/env python3
"""Build farm_case RAG chunks from approved farm_case candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("data/examples/farm_case_candidate_samples.jsonl")
DEFAULT_OUTPUT = Path("data/rag/farm_case_seed_chunks.jsonl")

CLIMATE_RISKS = {"heat_stress", "flower_drop", "condensation_risk", "frost_risk", "high_temperature"}
ROOTZONE_RISKS = {"overwet", "root_browning", "salt_accumulation", "rootzone_stress", "poor_establishment"}
PEST_DISEASE_RISKS = {
    "phytophthora_blight",
    "southern_blight",
    "whitefly",
    "powdery_mildew_severe",
    "virus_vector_pressure",
    "mold_risk",
    "thrips_outbreak",
}
SAFETY_RISKS = {"residue_violation", "export_rejection", "low_decision_confidence", "stale_sensor"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def infer_agent_use(row: dict[str, Any]) -> list[str]:
    risk_tags = set(normalize_list(row.get("risk_tags")))
    growth_stage = set(normalize_list(row.get("growth_stage")))
    sensor_tags = set(normalize_list(row.get("sensor_tags")))
    agent_use: list[str] = []

    if risk_tags & CLIMATE_RISKS or sensor_tags & {"temperature", "humidity", "vpd", "co2", "light"}:
        agent_use.append("climate-agent")
    if risk_tags & ROOTZONE_RISKS or sensor_tags & {"substrate_moisture", "soil_moisture", "drain_ec", "drain_rate", "ph"}:
        agent_use.append("irrigation-agent")
        agent_use.append("nutrient-agent")
    if risk_tags & PEST_DISEASE_RISKS or row.get("trigger_type") in {"disease_alert", "pest_alert"}:
        agent_use.append("pest-disease-agent")
    if row.get("crop_type") == "dried_red_pepper" or "harvest_drying_storage" in growth_stage:
        agent_use.append("harvest-drying-agent")
    if risk_tags & SAFETY_RISKS or row.get("sensor_quality") in {"partial", "bad"}:
        agent_use.append("safety-agent")
    if not agent_use:
        agent_use.append("report-agent")

    deduped: list[str] = []
    for item in agent_use:
        if item not in deduped:
            deduped.append(item)
    return deduped


def map_outcome(value: str) -> str:
    if value == "partial_success":
        return "mixed"
    return value


def derive_greenhouse_type(cultivation_type: list[str]) -> list[str]:
    return [
        item
        for item in cultivation_type
        if item in {"greenhouse", "rain_shelter", "tunnel", "plastic_house", "large_plastic_house"}
    ]


def is_eligible(row: dict[str, Any]) -> bool:
    return (
        row.get("review_status") == "approved"
        and row.get("sensor_quality") != "bad"
        and row.get("outcome") != "unknown"
    )


def build_chunk(row: dict[str, Any], input_path: Path) -> dict[str, Any]:
    cultivation_type = normalize_list(row.get("cultivation_type"))
    greenhouse_type = derive_greenhouse_type(cultivation_type)
    approved_at = str(row.get("approved_at", ""))
    effective_date = approved_at.split("T", maxsplit=1)[0] if approved_at else ""
    season = row.get("season")
    cultivar = row.get("cultivar")
    trust_level = row.get("trust_level", "medium")

    chunk: dict[str, Any] = {
        "chunk_id": row["case_id"],
        "document_id": f"FARM-CASE-{row['farm_id']}",
        "source_url": f"{input_path}#case_id={row['case_id']}",
        "source_type": "farm_case",
        "crop_type": row["crop_type"],
        "growth_stage": normalize_list(row.get("growth_stage")),
        "cultivation_type": cultivation_type,
        "sensor_tags": normalize_list(row.get("sensor_tags")),
        "risk_tags": normalize_list(row.get("risk_tags")),
        "operation_tags": normalize_list(row.get("operation_tags")),
        "causality_tags": normalize_list(row.get("causality_tags")),
        "visual_tags": normalize_list(row.get("visual_tags")),
        "source_pages": "event_window",
        "source_section": "approved farm_case candidate",
        "trust_level": trust_level,
        "version": "farm_case.v1",
        "effective_date": effective_date,
        "active": True,
        "farm_id": row["farm_id"],
        "zone_id": row["zone_id"],
        "outcome": map_outcome(row["outcome"]),
        "chunk_summary": row["chunk_summary"],
        "agent_use": infer_agent_use(row),
        "citation_required": False,
    }
    if season:
        chunk["season"] = normalize_list(season)
    if cultivar:
        chunk["cultivar"] = normalize_list(cultivar)
    if greenhouse_type:
        chunk["greenhouse_type"] = greenhouse_type
    return chunk


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    rows = load_jsonl(input_path)

    approved_rows = [row for row in rows if is_eligible(row)]
    chunks = [build_chunk(row, input_path) for row in approved_rows]
    write_jsonl(output_path, chunks)

    print(f"input_rows: {len(rows)}")
    print(f"eligible_rows: {len(approved_rows)}")
    print(f"output_rows: {len(chunks)}")
    print(f"wrote: {output_path}")


if __name__ == "__main__":
    main()
