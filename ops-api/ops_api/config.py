from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .bootstrap import REPO_ROOT


def _require_postgres_database_url(database_url: str) -> str:
    normalized = database_url.strip()
    if not normalized:
        raise RuntimeError(
            "OPS_API_DATABASE_URL must be set to a PostgreSQL URL. "
            "SQLite runtime is no longer allowed."
        )
    if normalized.startswith("postgresql://") or normalized.startswith("postgresql+"):
        return normalized
    raise RuntimeError(
        "OPS_API_DATABASE_URL must point to PostgreSQL/TimescaleDB. "
        "SQLite runtime is no longer allowed."
    )


@dataclass(frozen=True)
class Settings:
    database_url: str
    runtime_mode_path: Path
    auth_mode: str
    auth_tokens_json: str
    shadow_audit_log_path: Path
    validator_audit_log_path: Path
    llm_provider: str
    llm_model_id: str
    llm_prompt_version: str
    llm_timeout_seconds: float
    llm_max_retries: int
    # Retriever backend selection. Default stays 'keyword' so existing
    # deployments keep the historical behaviour until the operator opts in
    # to the denser OpenAI embedding retriever via OPS_API_RETRIEVER_TYPE.
    # See artifacts/reports/phase_f_validator_retriever_improvements.md for
    # the recall@5 benchmark that motivates the 'openai' option.
    retriever_type: str = "keyword"
    retriever_rag_index_path: str = ""
    # Automation runner (Phase P). Opt-in via OPS_API_AUTOMATION_ENABLED=true
    # because the background tick should only run once real sensor data
    # is flowing through sensor_readings. Default False keeps short-lived
    # test harnesses and local dev bootstrap free of the asyncio loop.
    # When enabled the FastAPI lifespan starts a background task that
    # periodically builds a per-zone sensor snapshot from
    # ``sensor_readings`` and feeds it into ``evaluate_rules`` so
    # operator-defined automation rules fire without manual
    # /automation/evaluate calls. See docs/automation_runner_design.md
    # for the full flow.
    automation_enabled: bool = False
    automation_interval_sec: float = 15.0
    automation_snapshot_window_sec: float = 120.0


def load_settings() -> Settings:
    return Settings(
        database_url=_require_postgres_database_url(
            os.getenv(
                "OPS_API_DATABASE_URL",
                "",
            )
        ),
        runtime_mode_path=Path(
            os.getenv(
                "OPS_API_RUNTIME_MODE_PATH",
                str(REPO_ROOT / "artifacts" / "runtime" / "ops_api" / "runtime_mode.json"),
            )
        ),
        auth_mode=os.getenv("OPS_API_AUTH_MODE", "disabled"),
        auth_tokens_json=os.getenv("OPS_API_AUTH_TOKENS_JSON", ""),
        shadow_audit_log_path=Path(
            os.getenv(
                "OPS_API_SHADOW_AUDIT_LOG_PATH",
                str(REPO_ROOT / "artifacts" / "runtime" / "llm_orchestrator" / "shadow_mode_audit.jsonl"),
            )
        ),
        validator_audit_log_path=Path(
            os.getenv(
                "OPS_API_VALIDATOR_AUDIT_LOG_PATH",
                str(REPO_ROOT / "artifacts" / "runtime" / "llm_orchestrator" / "output_validator_audit.jsonl"),
            )
        ),
        llm_provider=os.getenv("OPS_API_LLM_PROVIDER", "stub"),
        llm_model_id=os.getenv("OPS_API_MODEL_ID", "pepper-ops-local-stub"),
        llm_prompt_version=os.getenv("OPS_API_PROMPT_VERSION", "sft_v10"),
        llm_timeout_seconds=float(os.getenv("OPS_API_LLM_TIMEOUT_SECONDS", "30")),
        llm_max_retries=int(os.getenv("OPS_API_LLM_MAX_RETRIES", "3")),
        retriever_type=os.getenv("OPS_API_RETRIEVER_TYPE", "keyword"),
        retriever_rag_index_path=os.getenv("OPS_API_RETRIEVER_RAG_INDEX_PATH", ""),
        automation_enabled=_parse_bool(
            os.getenv("OPS_API_AUTOMATION_ENABLED", "false"),
            default=False,
        ),
        automation_interval_sec=float(
            os.getenv("OPS_API_AUTOMATION_INTERVAL_SEC", "15")
        ),
        automation_snapshot_window_sec=float(
            os.getenv("OPS_API_AUTOMATION_SNAPSHOT_WINDOW_SEC", "120")
        ),
    )


def _parse_bool(raw: str | None, *, default: bool) -> bool:
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"true", "1", "yes", "on"}:
        return True
    if value in {"false", "0", "no", "off"}:
        return False
    return default
