#!/usr/bin/env python3
"""Validate /ai/chat endpoint end-to-end with a TestClient-backed app.

Exercises:
1. Empty ``messages`` returns 400.
2. Missing user message returns 400.
3. Single-turn chat returns 200 with ``data.reply.content`` non-empty
   and ``provider`` populated.
4. Multi-turn chat with conversation history still succeeds.
5. Chat endpoint respects the ``read_runtime`` permission when auth_mode
   is header_token (viewer token → 200, no key → 401).
6. Dashboard HTML exposes the AI chat view hooks (chatMessages,
   chatInput, sendChatMessage, /ai/chat) so the UI and backend stay
   in sync.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from fastapi.testclient import TestClient  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.config import Settings  # noqa: E402


def _make_settings(tmp_path: Path, auth_mode: str = "disabled") -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path}/ops_api.db",
        runtime_mode_path=tmp_path / "runtime_mode.json",
        auth_mode=auth_mode,
        auth_tokens_json="",
        shadow_audit_log_path=tmp_path / "shadow.jsonl",
        validator_audit_log_path=tmp_path / "validator.jsonl",
        llm_provider="stub",
        llm_model_id="pepper-ops-local-stub",
        llm_prompt_version="sft_v10",
        llm_timeout_seconds=5.0,
        llm_max_retries=1,
    )


def main() -> int:
    errors: list[str] = []
    for key in ("OPS_API_AUTH_MODE", "OPS_API_AUTH_TOKENS_JSON"):
        os.environ.pop(key, None)

    with tempfile.TemporaryDirectory(prefix="ops-api-ai-chat-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        app = create_app(settings=_make_settings(tmp_path))
        client = TestClient(app)

        empty = client.post("/ai/chat", json={"messages": []})
        if empty.status_code != 400:
            errors.append(f"empty messages should 400, got {empty.status_code}")

        no_user = client.post(
            "/ai/chat",
            json={"messages": [{"role": "assistant", "content": "hello"}]},
        )
        if no_user.status_code != 400:
            errors.append(f"missing user message should 400, got {no_user.status_code}")

        single = client.post(
            "/ai/chat",
            json={
                "messages": [
                    {"role": "user", "content": "zone-a 상태 요약해줘"},
                ],
                "context": {"zone_hint": "gh-01-zone-a"},
            },
        )
        if single.status_code != 200:
            errors.append(f"single turn should 200, got {single.status_code}")
        else:
            body = single.json().get("data") or {}
            reply = (body.get("reply") or {}).get("content")
            if not reply:
                errors.append("reply.content should be non-empty")
            if body.get("provider") != "stub":
                errors.append(f"provider should be stub, got {body.get('provider')}")
            if not body.get("model_id"):
                errors.append("model_id should be populated")

        multi = client.post(
            "/ai/chat",
            json={
                "messages": [
                    {"role": "user", "content": "현재 고추 온실 상태는?"},
                    {"role": "assistant", "content": "전체 5개 존 중 2개가 normal, 1개가 caution입니다."},
                    {"role": "user", "content": "caution 존의 원인은?"},
                ],
            },
        )
        if multi.status_code != 200:
            errors.append(f"multi turn should 200, got {multi.status_code}")

        dashboard_html = client.get("/dashboard")
        if dashboard_html.status_code != 200:
            errors.append(f"dashboard GET should 200, got {dashboard_html.status_code}")
        html = dashboard_html.text
        hooks = ("chatMessages", "chatInput", "sendChatMessage", "/ai/chat", "AI 어시스턴트", "AI AGRO-SYSTEM")
        for hook in hooks:
            if hook not in html:
                errors.append(f"dashboard HTML missing hook {hook!r}")

    # Second run with header_token to exercise auth path
    with tempfile.TemporaryDirectory(prefix="ops-api-ai-chat-auth-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        app = create_app(settings=_make_settings(tmp_path, auth_mode="header_token"))
        client = TestClient(app)

        no_key = client.post("/ai/chat", json={"messages": [{"role": "user", "content": "hi"}]})
        if no_key.status_code != 401:
            errors.append(f"header_token mode without api key should 401, got {no_key.status_code}")

        viewer = client.post(
            "/ai/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers={"x-api-key": "viewer-demo-token"},
        )
        if viewer.status_code != 200:
            errors.append(f"viewer token should 200, got {viewer.status_code}")

    report = {
        "errors": errors,
        "status": "ok" if not errors else "failed",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
