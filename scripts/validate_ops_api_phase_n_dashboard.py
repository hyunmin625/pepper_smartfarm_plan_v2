#!/usr/bin/env python3
"""Smoke-verify the Phase N dashboard UI enhancements.

Phase N added three surfaces where operators can see which AI model /
retriever / runtime mode is currently active:

1. Header champion chip (`#headerChampionChip`) visible from every view.
2. Overview metric grid "Champion" card with `metric-champion` styling.
3. 시스템 > AI Runtime card (`#aiRuntimeCard` + `#aiRuntimeBody`) with
   provider / model label / family / prompt / retriever / chat prompt
   id fields populated from `/ai/config`.
4. 시스템 > Runtime Mode chip (`#runtimeModeChip`).
5. AI 어시스턴트 > Grounding Inspector (`#groundingInspector` with
   `#groundingModelLabel`, `#groundingProvider`, `#groundingZoneHint`,
   `#groundingKeys`, `#groundingAttempts`).

These hooks are exercised by:
- Checking `GET /dashboard` HTML contains each id / CSS class.
- Checking `GET /ai/config` returns the new fields used by loadAiConfig().
- Checking `POST /ai/chat` (stub LLM) still returns `provider`,
  `model_id`, `zone_hint`, `grounding_keys`, `attempts` so the
  grounding inspector has data to render.

Stub-backed (no real OpenAI call), so this smoke runs in CI and
complements the live `validate_ops_api_ai_chat_live.py`.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))

from fastapi.testclient import TestClient  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.config import Settings  # noqa: E402


DASHBOARD_HTML_HOOKS = [
    # Header champion chip
    'id="headerChampionChip"',
    # Overview Champion metric card styling
    "metric-champion",
    # 시스템 > AI Runtime card
    'id="aiRuntimeCard"',
    'id="aiRuntimeBody"',
    'id="aiRuntimeChip"',
    # 시스템 > Runtime Mode chip
    'id="runtimeModeChip"',
    # AI 어시스턴트 > Grounding Inspector
    'id="groundingInspector"',
    'id="groundingModelLabel"',
    'id="groundingProvider"',
    'id="groundingZoneHint"',
    'id="groundingKeys"',
    'id="groundingAttempts"',
    # JS wiring
    "function renderGroundingInspector",
    "loadAiConfig().then",
    "dashboardState",
    "chatState.lastGrounding",
]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}", flush=True)
        raise SystemExit(1)
    print(f"  ok  : {message}", flush=True)


def make_settings() -> Settings:
    tmp = Path(tempfile.mkdtemp(prefix="ops-api-phase-n-"))
    return Settings(
        database_url=f"sqlite:///{tmp}/ops_api.db",
        runtime_mode_path=tmp / "runtime_mode.json",
        auth_mode="disabled",
        auth_tokens_json="",
        shadow_audit_log_path=tmp / "shadow.jsonl",
        validator_audit_log_path=tmp / "validator.jsonl",
        llm_provider="stub",
        llm_model_id="pepper-ops-local-stub",
        llm_prompt_version="sft_v10",
        llm_timeout_seconds=5.0,
        llm_max_retries=1,
        retriever_type="keyword",
        retriever_rag_index_path="",
    )


def main() -> int:
    settings = make_settings()
    app = create_app(settings=settings)
    client = TestClient(app)

    # 1) Dashboard HTML carries every Phase N hook
    print("[1] GET /dashboard — Phase N UI hooks")
    res = client.get("/dashboard")
    _assert(res.status_code == 200, f"/dashboard status 200 (got {res.status_code})")
    html = res.text
    for hook in DASHBOARD_HTML_HOOKS:
        _assert(hook in html, f"dashboard html contains `{hook}`")

    # 2) /ai/config returns the new fields used by loadAiConfig()
    print()
    print("[2] GET /ai/config — new fields")
    res = client.get("/ai/config")
    _assert(res.status_code == 200, f"/ai/config status 200 (got {res.status_code})")
    cfg = res.json().get("data") or {}
    for key in (
        "llm_provider",
        "llm_model_id",
        "llm_model_label",
        "llm_model_family",
        "llm_prompt_version",
        "retriever_type",
        "chat_system_prompt_id",
    ):
        _assert(key in cfg, f"/ai/config.data contains `{key}`")
    _assert(cfg["llm_provider"] == "stub", "provider reflects stub settings")
    _assert(cfg["retriever_type"] == "keyword", "retriever reflects stub settings")

    # 3) /ai/chat returns the fields Grounding Inspector needs
    print()
    print("[3] POST /ai/chat — grounding fields for inspector")
    chat_res = client.post(
        "/ai/chat",
        json={
            "messages": [
                {"role": "user", "content": "zone-a의 현재 상태 요약해줘"},
            ],
            "context": {"zone_hint": "gh-01-zone-a"},
        },
    )
    _assert(chat_res.status_code == 200, f"/ai/chat status 200 (got {chat_res.status_code})")
    body = chat_res.json().get("data") or {}
    for key in ("reply", "model_id", "provider", "zone_hint", "grounding_keys", "attempts"):
        _assert(key in body, f"/ai/chat.data contains `{key}`")
    _assert(isinstance(body["grounding_keys"], list), "grounding_keys is a list")
    reply = body.get("reply") or {}
    _assert(isinstance(reply, dict) and reply.get("role") == "assistant", "reply.role == assistant")
    _assert(bool(reply.get("content")), "reply.content non-empty (stub)")

    print()
    print("all Phase N invariants passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
