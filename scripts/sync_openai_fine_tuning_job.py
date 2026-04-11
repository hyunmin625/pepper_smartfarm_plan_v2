#!/usr/bin/env python3
"""Sync OpenAI fine-tuning job status, events, and failure cases from a saved manifest."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


DEFAULT_FAILURE_CASES_PATH = Path("artifacts/fine_tuning/failure_cases.jsonl")
DEFAULT_EVENTS_DIR = Path("artifacts/fine_tuning/events")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def append_failure_case(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_job_ids: set[str] = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and isinstance(item.get("job_id"), str):
                existing_job_ids.add(item["job_id"])
    if record["job_id"] in existing_job_ids:
        return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_events(path: Path, events: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            if hasattr(event, "model_dump"):
                payload = event.model_dump()
            else:
                payload = dict(event)
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--failure-cases-path", default=str(DEFAULT_FAILURE_CASES_PATH))
    parser.add_argument("--events-dir", default=str(DEFAULT_EVENTS_DIR))
    args = parser.parse_args()

    if load_dotenv:
        load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY not found.")
    if OpenAI is None:
        raise SystemExit("openai package is not installed in the current environment.")

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    job_id = manifest.get("job_id")
    if not isinstance(job_id, str) or not job_id:
        raise SystemExit("manifest does not contain job_id")

    client = OpenAI(api_key=api_key)
    job = client.fine_tuning.jobs.retrieve(job_id)
    event_page = client.fine_tuning.jobs.list_events(job_id)
    events = list(getattr(event_page, "data", []))

    if hasattr(job, "model_dump"):
        job_payload = job.model_dump()
    else:
        job_payload = dict(job)
    manifest["latest_synced_at"] = utc_now_iso()
    manifest["status"] = job_payload.get("status", manifest.get("status"))
    manifest["fine_tuned_model"] = job_payload.get("fine_tuned_model")
    manifest["result_files"] = job_payload.get("result_files", [])
    manifest["estimated_finish"] = job_payload.get("estimated_finish")
    manifest["finished_at"] = job_payload.get("finished_at")
    manifest["error"] = job_payload.get("error")

    events_path = Path(args.events_dir) / f"{job_id}.jsonl"
    write_events(events_path, events)
    manifest["events_path"] = events_path.as_posix()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if manifest["status"] in {"failed", "cancelled"}:
        latest_message = None
        if events:
            latest = events[0]
            if hasattr(latest, "model_dump"):
                latest = latest.model_dump()
            latest_message = latest.get("message")
        failure_record = {
            "recorded_at": utc_now_iso(),
            "experiment_name": manifest.get("experiment_name"),
            "job_id": job_id,
            "base_model": manifest.get("base_model"),
            "model_version": manifest.get("model_version"),
            "dataset_version": manifest.get("dataset_version"),
            "prompt_version": manifest.get("prompt_version"),
            "eval_version": manifest.get("eval_version"),
            "status": manifest["status"],
            "error": manifest.get("error"),
            "latest_event_message": latest_message,
        }
        append_failure_case(Path(args.failure_cases_path), failure_record)

    print(f"job_id: {job_id}")
    print(f"status: {manifest['status']}")
    print(f"events_path: {events_path.as_posix()}")
    print(f"manifest: {manifest_path.as_posix()}")


if __name__ == "__main__":
    main()
