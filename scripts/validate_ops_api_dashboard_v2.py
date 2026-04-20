#!/usr/bin/env python3
"""Verify Phase T-1 /dashboard/v2 handoff prototype wiring.

The Claude Design handoff (`pepper smartfarm dashboard ui V1-handoff`)
ships the new dashboard as a React + Babel-standalone prototype. Phase
T-1 mounts it at ``/dashboard/v2`` (index + src/*.jsx) without touching
the existing ``/dashboard`` so operators can preview the redesign while
we gradually rewire each view from MOCK to real endpoints.

Checks:

1. ``GET /dashboard/v2`` returns HTML with the handoff's CSS tokens
   and script hooks.
2. Every ``src/*.jsx`` file referenced from index.html is reachable
   under ``/dashboard/v2/src/<name>.jsx`` and contains its component
   marker.
3. The existing ``/dashboard`` still returns 200 (regression guard).

Runs stub-backed (no Postgres) via an in-process Settings fixture.
"""

from __future__ import annotations

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
from ops_api.runtime_mode import save_runtime_mode  # noqa: E402


INDEX_HTML_HOOKS = [
    "iFarm 통합제어 — 대시보드 재설계",
    "--brand:          #006a26",
    "window.__TWEAK_DEFAULTS",
    'src="src/tokens.jsx"',
    'src="src/app.jsx"',
]

EXPECTED_JSX_FILES = [
    ("tokens.jsx", "const STATUS ="),
    ("chrome.jsx", "function Sidebar"),
    ("dashboard.jsx", "function Dashboard"),
    ("decisions.jsx", "function DecisionsPage"),
    ("rules.jsx", "function RulesPage"),
    ("alerts.jsx", "function AlertsPage"),
    ("zones.jsx", "function ZonesPage"),
    ("chat.jsx", "function ChatPage"),
    ("devices.jsx", "function DevicesPage"),
    ("policies_robot.jsx", "function PoliciesPage"),
    ("designsystem.jsx", "function DesignSystemPage"),
    ("app.jsx", "function App"),
]


def _resolve_base_postgres_url() -> str:
    url = os.getenv("OPS_API_POSTGRES_SMOKE_URL") or os.getenv("OPS_API_DATABASE_URL")
    if not url or not url.strip():
        print(
            "[validate_ops_api_dashboard_v2] SKIP: set OPS_API_DATABASE_URL or "
            "OPS_API_POSTGRES_SMOKE_URL",
        )
        raise SystemExit(0)
    return url.strip()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}", flush=True)
        raise SystemExit(1)
    print(f"  ok  : {message}", flush=True)


def _make_settings(tmp_root: Path, database_url: str) -> Settings:
    mode_path = tmp_root / "runtime_mode.json"
    save_runtime_mode(mode_path, mode="approval", actor_id="smoke", reason="dashboard_v2")
    return Settings(
        database_url=database_url,
        runtime_mode_path=mode_path,
        auth_mode="disabled",
        auth_tokens_json="",
        shadow_audit_log_path=tmp_root / "shadow.jsonl",
        validator_audit_log_path=tmp_root / "validator.jsonl",
        llm_provider="stub",
        llm_model_id="pepper-ops-local-stub",
        llm_prompt_version="sft_v10",
        llm_timeout_seconds=5.0,
        llm_max_retries=1,
        retriever_type="keyword",
        retriever_rag_index_path="",
        automation_enabled=False,
    )


def main() -> int:
    db_url = _resolve_base_postgres_url()
    with tempfile.TemporaryDirectory(prefix="ops-api-dashv2-") as tmp:
        tmp_root = Path(tmp)
        settings = _make_settings(tmp_root, db_url)
        app = create_app(settings=settings)
        client = TestClient(app)

        print("[1] GET /dashboard/v2 — index.html served")
        res = client.get("/dashboard/v2")
        _assert(res.status_code == 200, f"/dashboard/v2 returns 200 (got {res.status_code})")
        html = res.text
        for hook in INDEX_HTML_HOOKS:
            _assert(hook in html, f"/dashboard/v2 carries `{hook[:60]}…`")

        print()
        print("[2] GET /dashboard/v2/src/<file>.jsx — each prototype source is reachable")
        for filename, marker in EXPECTED_JSX_FILES:
            jres = client.get(f"/dashboard/v2/src/{filename}")
            _assert(
                jres.status_code == 200,
                f"/dashboard/v2/src/{filename} returns 200 (got {jres.status_code})",
            )
            _assert(
                marker in jres.text,
                f"{filename} carries marker `{marker}`",
            )

        print()
        print("[3] GET /dashboard — existing dashboard still serves (regression guard)")
        res = client.get("/dashboard")
        _assert(res.status_code == 200, f"/dashboard status 200 (got {res.status_code})")
        _assert(
            "iFarm" in res.text,
            "legacy dashboard still carries iFarm brand",
        )

    print()
    print("all Phase T-1 invariants passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
