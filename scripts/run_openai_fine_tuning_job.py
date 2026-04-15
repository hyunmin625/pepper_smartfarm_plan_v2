#!/usr/bin/env python3
"""Prepare or submit an OpenAI fine-tuning job and persist a run manifest."""

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


DEFAULT_MODEL = "gpt-4.1-mini-2025-04-14"
DEFAULT_TRAIN_FILE = Path("artifacts/fine_tuning/openai_sft_train.jsonl")
DEFAULT_VALIDATION_FILE = Path("artifacts/fine_tuning/openai_sft_validation.jsonl")
DEFAULT_RUNS_DIR = Path("artifacts/fine_tuning/runs")


def count_rows(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def short_model_name(model: str) -> str:
    """Produce a filename-safe short alias for the base model.

    Accepts either a plain OpenAI base id (`gpt-4.1-mini-2025-04-14`) or a
    fine-tuned checkpoint id (`ft:gpt-4.1-mini-...:DTryNJg3`). For fine-tuned
    models we return `ftbase-<tail>` where tail is the opaque checkpoint
    suffix OpenAI hands out, so continuous/incremental fine-tuning runs stay
    inside filename + suffix length limits while still being traceable.
    """
    if model.startswith("ft:"):
        tail = model.rsplit(":", 1)[-1] or "unknown"
        return f"ftbase-{tail}"
    return (
        model.replace("gpt-4.1-mini-2025-04-14", "gpt41mini")
        .replace("gpt-4.1-2025-04-14", "gpt41")
        .replace("gpt-4.1-nano-2025-04-14", "gpt41nano")
    )


def build_experiment_name(model: str, dataset_version: str, prompt_version: str, eval_version: str, date_tag: str) -> str:
    return f"ft-sft-{short_model_name(model)}-{dataset_version}-{prompt_version}-{eval_version}-{date_tag}"


def upload_file(client: Any, path: Path) -> str:
    with path.open("rb") as handle:
        result = client.files.create(file=handle, purpose="fine-tune")
    return result.id


def build_hyperparameters(args: argparse.Namespace) -> dict[str, Any]:
    """Return the explicit hyperparameters dict to send to OpenAI, or empty
    when every flag is left at None (= OpenAI auto). An empty dict means
    the request body will not carry a `hyperparameters` key at all, so the
    old auto-selection behaviour is preserved byte-for-byte.
    """
    hp: dict[str, Any] = {}
    if args.n_epochs is not None:
        hp["n_epochs"] = int(args.n_epochs)
    if args.learning_rate_multiplier is not None:
        hp["learning_rate_multiplier"] = float(args.learning_rate_multiplier)
    if args.batch_size is not None:
        hp["batch_size"] = int(args.batch_size)
    return hp


def build_manifest(args: argparse.Namespace, experiment_name: str, train_rows: int, validation_rows: int) -> dict[str, Any]:
    hp = build_hyperparameters(args)
    return {
        "schema_version": "fine_tuning_run.v1",
        "experiment_name": experiment_name,
        "mode": "submit" if args.submit else "dry_run",
        "status": "submitted" if args.submit else "prepared",
        "created_at": utc_now_iso(),
        "base_model": args.model,
        "model_version": args.model_version,
        "dataset_version": args.dataset_version,
        "prompt_version": args.prompt_version,
        "eval_version": args.eval_version,
        "training_file_path": str(Path(args.training_file).as_posix()),
        "validation_file_path": str(Path(args.validation_file).as_posix()) if args.validation_file else None,
        "training_rows": train_rows,
        "validation_rows": validation_rows,
        "suffix": args.suffix or experiment_name[:64],
        "hyperparameters": hp if hp else "auto",
        "job_id": None,
        "training_file_id": None,
        "validation_file_id": None,
        "fine_tuned_model": None,
        "result_files": [],
        "error": None,
        "notes": args.notes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--model-version", default="pepper-ops-sft-v1.0.0")
    parser.add_argument("--dataset-version", default="ds_v1")
    parser.add_argument("--prompt-version", default="prompt_v1")
    parser.add_argument("--eval-version", default="eval_v1")
    parser.add_argument("--training-file", default=str(DEFAULT_TRAIN_FILE))
    parser.add_argument("--validation-file", default=str(DEFAULT_VALIDATION_FILE))
    parser.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    parser.add_argument("--suffix", default=None)
    parser.add_argument("--run-tag", default=None)
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--n-epochs",
        type=int,
        default=None,
        help=(
            "Explicit number of training epochs. Leave unset to let OpenAI "
            "auto-select. Phase H postmortem: ds_v12 was trained with epochs=3 "
            "+ lr×2, which caused catastrophic forgetting. Use 2 with lr=1.0 "
            "for conservative retries."
        ),
    )
    parser.add_argument(
        "--learning-rate-multiplier",
        type=float,
        default=None,
        help=(
            "Explicit learning rate multiplier. Leave unset to let OpenAI "
            "auto-select. Phase H postmortem: ds_v12 auto-picked 2.0 which "
            "overrode the pepper-ops schema persona. Use 1.0 to keep the "
            "existing persona stable while adding batch22 corrections."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Explicit batch size. Leave unset to let OpenAI auto-select (usually 1 for this dataset size).",
    )
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()

    if load_dotenv:
        load_dotenv()

    training_path = Path(args.training_file)
    validation_path = Path(args.validation_file) if args.validation_file else None
    train_rows = count_rows(training_path)
    validation_rows = count_rows(validation_path) if validation_path and validation_path.exists() else 0
    date_tag = args.run_tag or datetime.now().strftime("%Y%m%d-%H%M%S")
    experiment_name = build_experiment_name(
        args.model,
        args.dataset_version,
        args.prompt_version,
        args.eval_version,
        date_tag,
    )
    manifest = build_manifest(args, experiment_name, train_rows, validation_rows)

    if args.submit:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit("OPENAI_API_KEY not found. Use --submit only when API access is configured.")
        if OpenAI is None:
            raise SystemExit("openai package is not installed in the current environment.")

        client = OpenAI(api_key=api_key)
        training_file_id = upload_file(client, training_path)
        validation_file_id = upload_file(client, validation_path) if validation_path else None

        request_body: dict[str, Any] = {
            "model": args.model,
            "training_file": training_file_id,
            "suffix": manifest["suffix"],
            "metadata": {
                "experiment_name": experiment_name,
                "model_version": args.model_version,
                "dataset_version": args.dataset_version,
                "prompt_version": args.prompt_version,
                "eval_version": args.eval_version,
            },
        }
        if validation_file_id:
            request_body["validation_file"] = validation_file_id
        hp = build_hyperparameters(args)
        if hp:
            request_body["hyperparameters"] = hp

        job = client.fine_tuning.jobs.create(**request_body)
        manifest["job_id"] = job.id
        manifest["training_file_id"] = training_file_id
        manifest["validation_file_id"] = validation_file_id
        manifest["status"] = getattr(job, "status", "submitted")
        manifest["result_files"] = list(getattr(job, "result_files", []))

    runs_dir = Path(args.runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = runs_dir / f"{experiment_name}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"experiment_name: {experiment_name}")
    print(f"status: {manifest['status']}")
    print(f"training_rows: {train_rows}")
    print(f"validation_rows: {validation_rows}")
    print(f"hyperparameters: {manifest['hyperparameters']}")
    print(f"manifest: {manifest_path.as_posix()}")
    if manifest["job_id"]:
        print(f"job_id: {manifest['job_id']}")


if __name__ == "__main__":
    main()
