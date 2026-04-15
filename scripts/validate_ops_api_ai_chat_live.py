#!/usr/bin/env python3
"""Live end-to-end smoke for /ai/chat against the production-configured model.

Unlike ``validate_ops_api_ai_chat.py`` this does NOT use the stub client.
It loads the real ``.env`` (OPENAI_API_KEY + OPS_API_MODEL_ID = ds_v11) and
boots a TestClient-backed ops-api app so the endpoint goes through the
full stack: auth → session → grounding context → orchestrator client →
OpenAI fine-tuned model → JSON reply parse.

Asserts that the response:
  1. Returns HTTP 200.
  2. Carries a non-empty ``reply.content`` (Korean natural-language text).
  3. Has ``provider = "openai"``.
  4. Has ``model_id`` matching the configured OPS_API_MODEL_ID.
  5. Includes a non-empty ``grounding_keys`` list.
  6. ``/ai/config`` returns matching provider/model_id so the dashboard
     badge will render correctly.

Writes an append-only transcript to
``artifacts/reports/ai_chat_live_smoke.md`` so future agents can inspect
the last verified reply.

Costs one small OpenAI fine-tuned completion (~$0.002).
Skips with a clear message if OPENAI_API_KEY is missing.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except Exception:
    pass

from fastapi.testclient import TestClient  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.config import load_settings  # noqa: E402


TRANSCRIPT_PATH = REPO_ROOT / "artifacts/reports/ai_chat_live_smoke.md"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}", flush=True)
        raise SystemExit(1)
    print(f"  ok  : {message}", flush=True)


def main() -> int:
    if not os.getenv("OPENAI_API_KEY"):
        print("skip: OPENAI_API_KEY not set — this smoke needs a live key")
        return 0

    settings = load_settings()
    print(f"settings.llm_provider     = {settings.llm_provider}")
    print(f"settings.llm_model_id     = ...:{settings.llm_model_id.rsplit(':', 1)[-1]}")
    print(f"settings.llm_prompt_ver   = {settings.llm_prompt_version}")
    print(f"settings.retriever_type   = {settings.retriever_type}")
    print()

    if settings.llm_provider != "openai":
        print(f"skip: provider must be openai for live smoke (got {settings.llm_provider})")
        return 0

    app = create_app(settings=settings)
    client = TestClient(app)

    # 1) /ai/config matches the configured settings
    print("[1] GET /ai/config")
    res = client.get("/ai/config")
    _assert(res.status_code == 200, f"status 200 (got {res.status_code})")
    cfg = res.json().get("data") or {}
    _assert(cfg.get("llm_provider") == settings.llm_provider, "provider matches settings")
    _assert(cfg.get("llm_model_id") == settings.llm_model_id, "model_id matches settings")
    _assert(bool(cfg.get("llm_model_label")), "model_label populated")
    _assert(bool(cfg.get("llm_model_family")), "model_family populated")
    _assert(cfg.get("retriever_type") == settings.retriever_type, "retriever_type matches")

    # 2) /ai/chat single-turn, real model call
    print()
    print("[2] POST /ai/chat — single-turn live call")
    chat_body = {
        "messages": [
            {
                "role": "user",
                "content": "gh-01-zone-a 현재 상태를 한두 문장으로 요약해줘.",
            }
        ],
        "context": {"zone_hint": "gh-01-zone-a"},
    }
    res = client.post("/ai/chat", json=chat_body)
    _assert(res.status_code == 200, f"status 200 (got {res.status_code})")
    body = res.json().get("data") or {}
    reply_obj = body.get("reply") or {}
    reply_text = reply_obj.get("content") or ""
    print(f"  reply[:200]: {reply_text[:200]}")
    _assert(bool(reply_text.strip()), "reply.content non-empty")
    _assert(reply_obj.get("role") == "assistant", "reply.role == assistant")
    _assert(body.get("provider") == "openai", f"provider=openai (got {body.get('provider')})")
    _assert(body.get("model_id") == settings.llm_model_id, "model_id matches settings")
    grounding_keys = body.get("grounding_keys") or []
    _assert(len(grounding_keys) > 0, f"grounding_keys non-empty (got {grounding_keys})")

    # 3) Persist transcript so future agents can inspect the last verified reply
    TRANSCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    transcript_entry = [
        "",
        f"## {utc_now_iso()} — live smoke OK",
        "",
        f"- provider: `{body.get('provider')}`",
        f"- model_id: `{body.get('model_id')}`",
        f"- grounding_keys: `{grounding_keys}`",
        f"- zone_hint: `{body.get('zone_hint')}`",
        f"- user: `{chat_body['messages'][0]['content']}`",
        f"- reply: {reply_text}",
        "",
    ]
    header_needed = not TRANSCRIPT_PATH.exists()
    with TRANSCRIPT_PATH.open("a", encoding="utf-8") as handle:
        if header_needed:
            handle.write("# /ai/chat live smoke transcript\n\n")
            handle.write("Append-only log of successful end-to-end smokes from\n")
            handle.write("`scripts/validate_ops_api_ai_chat_live.py`. Each entry proves\n")
            handle.write("the production `.env` configured model actually answered a\n")
            handle.write("Korean operator question through the full ops-api stack.\n")
        handle.write("\n".join(transcript_entry))

    print()
    print(f"wrote transcript: {TRANSCRIPT_PATH.as_posix()}")
    print()
    print("all invariants passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
