#!/usr/bin/env python3
"""Local uvicorn launcher for the ops-api dashboard.

Boots ``ops_api.app.create_app(settings=load_settings())`` with the live
.env so the champion (ds_v11 fine-tune), OpenAI retriever, automation
rules and AI chat endpoints are all wired exactly as they will run in
production. Listens on 0.0.0.0:8000 so it's reachable from the Windows
host browser when running inside WSL2.

Usage:

    python3 scripts/run_ops_api_local.py [--host HOST] [--port PORT]

The script does not daemonize; run it with ``run_in_background`` or
``nohup`` if you want it detached.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
for sibling in ("ops-api", "llm-orchestrator", "policy-engine", "state-estimator", "execution-gateway"):
    sys.path.insert(0, str(REPO_ROOT / sibling))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except Exception:
    pass

import uvicorn  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.config import load_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0", help="bind host (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="bind port (default 8000)")
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    settings = load_settings()
    print(f"[run_ops_api_local] provider={settings.llm_provider}")
    print(f"[run_ops_api_local] model={settings.llm_model_id.rsplit(':', 1)[-1]}")
    print(f"[run_ops_api_local] retriever={settings.retriever_type}")
    print(f"[run_ops_api_local] auth_mode={settings.auth_mode}")
    print(f"[run_ops_api_local] db={settings.database_url}")
    print(f"[run_ops_api_local] binding {args.host}:{args.port}")

    app = create_app(settings=settings)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        # Avoid the default reloader because we pass a prebuilt app object.
        reload=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
