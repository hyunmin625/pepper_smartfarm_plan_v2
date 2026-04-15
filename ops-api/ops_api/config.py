from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .bootstrap import REPO_ROOT


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


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "OPS_API_DATABASE_URL",
            f"sqlite:///{REPO_ROOT / 'artifacts' / 'runtime' / 'ops_api' / 'ops_api.db'}",
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
    )
